import json
import re
import shutil
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

JST = timezone(timedelta(hours=9))
BRAIN_DIR = Path(r"C:\Users\PC_User\.gemini\antigravity-cli\brain")
HISTORY_DIR = Path(r"C:\Users\PC_User\.gemini\history")
VAULT_DIR = Path(r"C:\Users\PC_User\Obsidian_2")
OUTPUT_DIR = VAULT_DIR / "youyaku"
BACKUP_OUTPUT_DIR = Path(r"G:\マイドライブ\Obsidian_2\youyaku")
LINK_TARGET_DIRS = ("06_Reports", "07_Ideas", "03_Resources", "youtube")
_VAULT_NOTE_INDEX_CACHE: list[str] | None = None


def _backup_to_gdrive(src_file: Path) -> None:
    try:
        if BACKUP_OUTPUT_DIR.parent.exists():
            BACKUP_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src_file, BACKUP_OUTPUT_DIR / src_file.name)
    except Exception as e:
        print(f"Backup copy skipped ({src_file.name}): {e}", file=sys.stderr)


def parse_iso_to_jst(iso_str: str) -> datetime:
    if not iso_str:
        return datetime.now(JST)
    dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
    return dt.astimezone(JST)


def extract_user_text(content: str) -> str:
    match = re.search(r"<USER_REQUEST>\s*(.*?)\s*</USER_REQUEST>", content, re.DOTALL)
    return match.group(1).strip() if match else content.strip()


def clean_arg_path(raw_path: str) -> str:
    if not raw_path:
        return ""
    return raw_path.strip('"').replace("\\\\", "\\")


def get_vault_note_index() -> list[str]:
    """06_Reports / 07_Ideas / 03_Resources / youtube 配下のノート名(拡張子なし)を長い順に返す。"""
    global _VAULT_NOTE_INDEX_CACHE
    if _VAULT_NOTE_INDEX_CACHE is not None:
        return _VAULT_NOTE_INDEX_CACHE

    names: set[str] = set()
    for d_name in LINK_TARGET_DIRS:
        target_dir = VAULT_DIR / d_name
        if not target_dir.exists():
            continue
        for md_file in target_dir.rglob("*.md"):
            stem = md_file.stem.strip()
            # 誤リンク防止: 短すぎる名前や日付のみのファイル名は除外
            if len(stem) >= 4 and not re.fullmatch(r"\d{2}-\d{2}-\d{4}", stem):
                names.add(stem)

    _VAULT_NOTE_INDEX_CACHE = sorted(names, key=len, reverse=True)
    return _VAULT_NOTE_INDEX_CACHE


def convert_text_to_wikilinks(text: str) -> str:
    """コードブロック・既存リンク・URLを保護しつつ、Vault内の関連ノート言及を [[ファイル名]] に変換する。"""
    if not text:
        return text

    placeholders: dict[str, str] = {}

    def _stash(match: re.Match) -> str:
        key = f"\x00WL_PROTECT_{len(placeholders)}\x00"
        placeholders[key] = match.group(0)
        return key

    # コードブロック、インラインコード、既存WikiLink、Markdownリンク、URLを退避
    protected = re.sub(r"```.*?```", _stash, text, flags=re.DOTALL)
    protected = re.sub(r"`[^`\n]+`", _stash, protected)
    protected = re.sub(r"\[\[[^\]]+\]\]", _stash, protected)
    protected = re.sub(r"\[[^\]]+\]\([^)]+\)", _stash, protected)
    protected = re.sub(r"https?://[^\s\)\]>\"']+", _stash, protected)

    # 1) 対象ディレクトリのパス付き言及 (例: 06_Reports/xxx.md) を [[xxx]] に変換
    dirs_pat = "|".join(re.escape(d) for d in LINK_TARGET_DIRS)
    protected = re.sub(
        rf"(?:[A-Za-z]:[\\/][^\s\"'`<>|]*?[\\/])?(?:{dirs_pat})[\\/](?:[^\s\\/'\"`<>|\[\]()]+[\\/])*([^\s\\/'\"`<>|\[\]()]+?)\.md\b",
        lambda m: f"[[{m.group(1)}]]",
        protected,
    )

    # 2) インデックス登録済みノート名（.md付き or 生テキスト）を [[ノート名]] に変換
    note_names = get_vault_note_index()
    if note_names:
        # 既に [[...]] に変換された部分を再退避
        protected = re.sub(r"\[\[[^\]]+\]\]", _stash, protected)
        alt_pat = "|".join(re.escape(n) for n in note_names)
        pattern = re.compile(rf"(?<![A-Za-z0-9_\[])({alt_pat})(?:\.md)?(?![A-Za-z0-9_\]])")
        protected = pattern.sub(lambda m: f"[[{m.group(1)}]]", protected)

    for key, val in placeholders.items():
        protected = protected.replace(key, val)
    return protected


def _format_mermaid_label(raw: str) -> str:
    """Mermaidラベル文字列を "..." で安全に囲む。"""
    inner = raw.strip()
    if len(inner) >= 2 and inner.startswith('"') and inner.endswith('"'):
        inner = inner[1:-1]
    inner = inner.replace('"', "’").replace("\r\n", "<br>").replace("\n", "<br>")
    return f'"{inner}"'


def _sanitize_flowchart_line(line: str) -> str:
    """flowchart/graph の1行を走査し、ノード・分岐ラベルを "..." で囲み、不正矢印を補正する。"""
    stripped = line.strip()
    if not stripped or stripped.startswith(("%%", "flowchart ", "graph ", "end", "style ", "classDef ", "class ", "click ", "linkStyle ")):
        return line

    indent = line[: len(line) - len(line.lstrip())]

    # subgraph ID[ラベル] / subgraph "ラベル" の補正
    m_sub = re.match(r"^subgraph\s+([A-Za-z0-9_]+)\s*\[(.*)\]\s*$", stripped)
    if m_sub:
        return f'{indent}subgraph {m_sub.group(1)}[{_format_mermaid_label(m_sub.group(2))}]'

    # 単独の不正矢印 `->` を `-->` に補正（`<->` や `-->` や `-.->` は維持）
    s = re.sub(r"(?<![-=.o<x])\s*->\s*(?![>])", " --> ", stripped)
    # `-->|ラベル|` のエッジラベルを |"..."| に統一
    s = re.sub(
        r"(-->|-.->|==>)\|([^|\n]+)\|",
        lambda m: f"{m.group(1)}|{_format_mermaid_label(m.group(2))}|",
        s,
    )

    # ノード形状ごとの括弧を走査して中身を "..." で囲む
    open_close = [
        ("[[", "]]"),
        ("((", "))"),
        ("([", "])"),
        ("{{", "}}"),
        ("[", "]"),
        ("(", ")"),
        ("{", "}"),
    ]
    out: list[str] = []
    i = 0
    n = len(s)
    while i < n:
        # 文字列リテラル外の識別子直後の開き括弧を検出
        if s[i].isalnum() or s[i] == "_":
            j = i
            while j < n and (s[j].isalnum() or s[j] == "_"):
                j += 1
            ident = s[i:j]
            matched_pair = None
            for op, cl in open_close:
                if s.startswith(op, j):
                    matched_pair = (op, cl)
                    break
            if matched_pair:
                op, cl = matched_pair
                k = j + len(op)
                in_quote = False
                depth = 1
                while k < n:
                    ch = s[k]
                    if ch == '"' and (k == 0 or s[k - 1] != "\\"):
                        in_quote = not in_quote
                    elif not in_quote:
                        if s.startswith(cl, k):
                            depth -= 1
                            if depth == 0:
                                break
                        elif s.startswith(op, k):
                            depth += 1
                    k += 1
                if k < n and depth == 0:
                    raw_label = s[j + len(op) : k]
                    out.append(f"{ident}{op}{_format_mermaid_label(raw_label)}{cl}")
                    i = k + len(cl)
                    continue
            out.append(ident)
            i = j
            continue
        out.append(s[i])
        i += 1
    return indent + "".join(out)


def sanitize_mermaid_code(code: str) -> str:
    """Mermaidコードブロックの構文エラー（未囲みラベル、不正矢印等）を修正する。"""
    if not code or not code.strip():
        return code
    lines = code.splitlines()
    first_non_empty = next((ln.strip() for ln in lines if ln.strip()), "")
    if not first_non_empty.startswith(("flowchart", "graph")):
        return code
    return "\n".join(_sanitize_flowchart_line(ln) for ln in lines)


def _safe_mermaid_text(text: str, max_len: int = 32) -> str:
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    first_line = lines[0] if lines else "..."
    short = first_line[:max_len] + ("…" if len(first_line) > max_len else "")
    replacements = {
        '"': "’",
        "'": "’",
        "[": "（",
        "]": "）",
        "{": "｛",
        "}": "｝",
        "<": "＜",
        ">": "＞",
        "|": "｜",
        "`": "’",
        "\\": "/",
        "#": "＃",
        "&": "＆",
        ";": "；",
    }
    for k, v in replacements.items():
        short = short.replace(k, v)
    return short


def _build_daily_analysis_data(target_date_str: str, conversations: list, edited_files: list) -> dict:
    """HTML版・Markdown版で共有する日次分析サマリーデータを構築する。"""
    subgraphs = []
    sg_links = []
    step_num = 0
    location_questions = 0
    error_mentions = 0
    topics_list = []

    max_convs = min(len(conversations), 6)
    for c_idx, conv in enumerate(conversations[:max_convs], 1):
        first_user_msg = next((m["text"] for m in conv["messages"] if m["role"] == "よっちゃん"), "対話")
        topic_short = _safe_mermaid_text(first_user_msg, 24)
        topics_list.append(topic_short)
        sg_id = f"S{c_idx}"
        sg_lines = [f'    subgraph {sg_id}["セッション{c_idx}：{topic_short}（{conv["first_time"][:5]}〜）"]']
        prev_node = None
        msgs_slice = conv["messages"][:8]
        for msg in msgs_slice:
            step_num += 1
            node_id = f"N{step_num}"
            role_icon = "🧑" if msg["role"] == "よっちゃん" else "🤖"
            safe_txt = _safe_mermaid_text(msg["text"], 28)
            sg_lines.append(f'        {node_id}["{role_icon} {msg["time"][:5]} {safe_txt}"]')
            if prev_node:
                sg_lines.append(f"        {prev_node} --> {node_id}")
            prev_node = node_id
        sg_lines.append("    end")
        subgraphs.append("\n".join(sg_lines))
        if c_idx > 1:
            sg_links.append(f"    S{c_idx - 1} --> {sg_id}")

    for conv in conversations:
        for msg in conv["messages"]:
            if msg["role"] == "よっちゃん":
                txt = msg["text"]
                if any(k in txt for k in ("何処", "どこ", "場所", "どれ")):
                    location_questions += 1
                if any(k in txt for k in ("エラー", "失敗", "動かない", "できない", "文字化け", "見ずらい", "見づらい", "直して", "違う")):
                    error_mentions += 1

    mermaid_auto = "flowchart TD\n" + "\n\n".join(subgraphs)
    if sg_links:
        mermaid_auto += "\n\n" + "\n".join(sg_links)
    mermaid_auto = sanitize_mermaid_code(mermaid_auto)

    user_turns = sum(1 for c in conversations for m in c["messages"] if m["role"] == "よっちゃん")
    edit_count = len(edited_files)
    unique_files = list(dict.fromkeys(fp for _, _, fp in edited_files))
    topics_summary = " ／ ".join(f"「{t}」" for t in topics_list[:4])
    if len(conversations) > 4:
        topics_summary += f" ほか計{len(conversations)}件"

    issues: list[tuple[str, str]] = []
    if location_questions > 0:
        issues.append((
            f"保存場所・対象確認の発生（{location_questions}回）",
            "ファイルの配置場所や対象に関する再確認が発生しているため、保存時は「1テーマ＝1ファイル」でパスを最上部に明示する必要がある。",
        ))
    if error_mentions > 0:
        issues.append((
            f"表示・動作の微調整要求（{error_mentions}回）",
            "エラー解消や視認性改善のやり取りが発生。初回実装時の検証（Goal-Drivenテスト）の自動化・強化が課題。",
        ))
    if edit_count > 6:
        issues.append((
            f"複数ファイルへの分散編集（計{edit_count}回）",
            "更新箇所が多岐にわたるため、後からの追跡コストを下げる集約ノートの活用が有効。",
        ))
    if not issues:
        issues.append((
            "手戻りのないスムーズな進行",
            "大きな迷子やエラーは未検出。対話だけで終わらせず、得た知見を `LoopEngineering/` やレシピへ継続的に昇華させることが今後の課題。",
        ))

    return {
        "mermaid_auto": mermaid_auto,
        "user_turns": user_turns,
        "conv_count": len(conversations),
        "edit_count": edit_count,
        "unique_files": unique_files,
        "topics_summary": topics_summary,
        "issues": issues,
    }


def collect_daily_data(target_date_str: str):
    conversations = []
    edited_files = []

    if BRAIN_DIR.exists():
        for conv_dir in BRAIN_DIR.iterdir():
            if not conv_dir.is_dir():
                continue
            log_file = conv_dir / ".system_generated" / "logs" / "transcript_full.jsonl"
            if not log_file.exists():
                log_file = conv_dir / ".system_generated" / "logs" / "transcript.jsonl"
            if not log_file.exists():
                continue

            mtime_jst = datetime.fromtimestamp(log_file.stat().st_mtime, JST).strftime("%Y-%m-%d")
            if mtime_jst < target_date_str:
                continue

            qa_pairs = []
            try:
                with log_file.open("r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        step = json.loads(line)
                        step_dt = parse_iso_to_jst(step.get("created_at", ""))
                        if step_dt.strftime("%Y-%m-%d") != target_date_str:
                            continue

                        step_type = step.get("type")
                        source = step.get("source")
                        time_str = step_dt.strftime("%H:%M:%S")

                        if source == "USER_EXPLICIT" and step_type == "USER_INPUT":
                            q_text = extract_user_text(step.get("content", ""))
                            if q_text:
                                qa_pairs.append({"role": "よっちゃん", "time": time_str, "text": q_text})

                        elif source == "MODEL" and step_type == "PLANNER_RESPONSE":
                            a_text = (step.get("content") or "").strip()
                            if a_text:
                                qa_pairs.append({"role": "AI", "time": time_str, "text": a_text})

                            for tc in step.get("tool_calls", []):
                                tool_name = tc.get("name", "")
                                if tool_name in ("write_file", "edit_file"):
                                    file_path = clean_arg_path(tc.get("args", {}).get("Path", ""))
                                    if file_path:
                                        edited_files.append((time_str, tool_name, file_path))
            except Exception:
                continue

            if qa_pairs:
                conversations.append({
                    "id": conv_dir.name,
                    "first_time": qa_pairs[0]["time"],
                    "messages": qa_pairs,
                })

    backup_files = []
    if HISTORY_DIR.exists():
        for p in HISTORY_DIR.rglob("*"):
            if p.is_file() and ".git" not in p.parts:
                try:
                    mtime = datetime.fromtimestamp(p.stat().st_mtime, JST)
                    if mtime.strftime("%Y-%m-%d") == target_date_str:
                        backup_files.append((mtime.strftime("%H:%M:%S"), str(p)))
                except Exception:
                    continue

    conversations.sort(key=lambda x: x["first_time"])
    return conversations, edited_files, backup_files


def collect_all_daily_data(target_dates: set) -> dict:
    conv_by_date = {d: [] for d in target_dates}
    edits_by_date = {d: [] for d in target_dates}
    backups_by_date = {d: [] for d in target_dates}

    if BRAIN_DIR.exists():
        for conv_dir in BRAIN_DIR.iterdir():
            if not conv_dir.is_dir():
                continue
            log_file = conv_dir / ".system_generated" / "logs" / "transcript_full.jsonl"
            if not log_file.exists():
                log_file = conv_dir / ".system_generated" / "logs" / "transcript.jsonl"
            if not log_file.exists():
                continue

            qa_by_date = {}
            try:
                with log_file.open("r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        step = json.loads(line)
                        step_dt = parse_iso_to_jst(step.get("created_at", ""))
                        d_str = step_dt.strftime("%Y-%m-%d")
                        if d_str not in target_dates:
                            continue

                        step_type = step.get("type")
                        source = step.get("source")
                        time_str = step_dt.strftime("%H:%M:%S")

                        if source == "USER_EXPLICIT" and step_type == "USER_INPUT":
                            q_text = extract_user_text(step.get("content", ""))
                            if q_text:
                                qa_by_date.setdefault(d_str, []).append({"role": "よっちゃん", "time": time_str, "text": q_text})

                        elif source == "MODEL" and step_type == "PLANNER_RESPONSE":
                            a_text = (step.get("content") or "").strip()
                            if a_text:
                                qa_by_date.setdefault(d_str, []).append({"role": "AI", "time": time_str, "text": a_text})

                            for tc in step.get("tool_calls", []):
                                tool_name = tc.get("name", "")
                                if tool_name in ("write_file", "edit_file"):
                                    file_path = clean_arg_path(tc.get("args", {}).get("Path", ""))
                                    if file_path:
                                        edits_by_date[d_str].append((time_str, tool_name, file_path))
            except Exception:
                continue

            for d_str, qa_pairs in qa_by_date.items():
                if qa_pairs:
                    conv_by_date[d_str].append({
                        "id": conv_dir.name,
                        "first_time": qa_pairs[0]["time"],
                        "messages": qa_pairs,
                    })

    if HISTORY_DIR.exists():
        for p in HISTORY_DIR.rglob("*"):
            if p.is_file() and ".git" not in p.parts:
                try:
                    mtime = datetime.fromtimestamp(p.stat().st_mtime, JST)
                    d_str = mtime.strftime("%Y-%m-%d")
                    if d_str in target_dates:
                        backups_by_date[d_str].append((mtime.strftime("%H:%M:%S"), str(p)))
                except Exception:
                    continue

    result = {}
    for d in target_dates:
        convs = conv_by_date[d]
        convs.sort(key=lambda x: x["first_time"])
        result[d] = (convs, edits_by_date[d], backups_by_date[d])
    return result


def _format_md_message_body(text: str) -> str:
    """会話テキスト内のMermaidブロックをサニタイズし、関連ノート言及を [[ファイル名]] に変換する。"""
    mermaid_keywords = (
        "flowchart",
        "graph",
        "sequenceDiagram",
        "stateDiagram",
        "stateDiagram-v2",
        "classDiagram",
        "erDiagram",
        "xychart-beta",
    )
    placeholders: dict[str, str] = {}

    def _replace_fence(match: re.Match) -> str:
        lang = (match.group(1) or "").strip()
        code_raw = match.group(2).strip("\n")
        first_word = code_raw.lstrip().split()[0] if code_raw.strip() else ""
        if lang.lower() == "mermaid" or first_word in mermaid_keywords:
            safe_code = sanitize_mermaid_code(code_raw)
            block = f"```mermaid\n{safe_code}\n```"
        else:
            block = match.group(0)
        key = f"\x00MD_FENCE_{len(placeholders)}\x00"
        placeholders[key] = block
        return key

    processed = re.sub(r"```(\w*)\n(.*?)```", _replace_fence, text, flags=re.DOTALL)
    processed = convert_text_to_wikilinks(processed)
    for key, val in placeholders.items():
        processed = processed.replace(key, val)
    return processed


def generate_markdown(target_date_str: str, precollected=None) -> Path | None:
    """Obsidian用の日次Markdownレポートを生成する（WikiLink補完・Mermaid安全化・MOC追記付き）。"""
    if precollected is not None:
        conversations, edited_files, backup_files = precollected
    else:
        conversations, edited_files, backup_files = collect_daily_data(target_date_str)

    if not conversations:
        return None

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    out_file = OUTPUT_DIR / f"{target_date_str}_Antigravity日報.md"

    # 1. 編集・作成ファイル履歴
    file_lines: list[str] = []
    for time_str, tool_name, file_path in edited_files:
        badge = "新規作成/上書き" if tool_name == "write_file" else "部分編集"
        p = Path(file_path)
        link_suffix = f" → [[{p.stem}]]" if p.suffix.lower() == ".md" and "Obsidian_2" in file_path else ""
        file_lines.append(f"- `{time_str}` **{badge}** `{file_path}`{link_suffix}")
    for time_str, b_path in backup_files:
        file_lines.append(f"- `{time_str}` **バックアップ** `{b_path}`")
    files_md = "\n".join(file_lines) if file_lines else "- 本日AIが編集したファイルはありません。"

    # 2. 分析サマリー & Mermaidフロー図
    data = _build_daily_analysis_data(target_date_str, conversations, edited_files)
    if data["unique_files"]:
        linked_files = []
        for fp in data["unique_files"][:4]:
            p = Path(fp)
            if p.suffix.lower() == ".md" and "Obsidian_2" in fp:
                linked_files.append(f"[[{p.stem}]]")
            else:
                linked_files.append(f"`{p.name}`")
        short_files = ", ".join(linked_files)
        if len(data["unique_files"]) > 4:
            short_files += f" ほか計{len(data['unique_files'])}ファイル"
        qual_md = f"計 {data['edit_count']} 回のファイル操作により、{short_files} への具体的な成果物反映・記録が完了している。"
    else:
        qual_md = "ファイル直接編集を伴わない調査・コマンド実行・方針整理セッションとして、前提確認と手順提示が行われている。"

    issues_md = " / ".join(f"**{t}**：{d}" for t, d in data["issues"])
    issues_md = convert_text_to_wikilinks(issues_md)

    # 3. 会話ログ本文
    conv_blocks: list[str] = []
    for idx, conv in enumerate(conversations, 1):
        first_q = next((m["text"].splitlines()[0][:50] for m in conv["messages"] if m["role"] == "よっちゃん"), "会話")
        conv_blocks.append(f"### {idx}. {first_q}（開始 {conv['first_time']} / ID: `{conv['id'][:8]}`）")
        for msg in conv["messages"]:
            label = "🧑 よっちゃん" if msg["role"] == "よっちゃん" else "🤖 AI"
            body = _format_md_message_body(msg["text"])
            conv_blocks.append(f"#### {label}（{msg['time']}）\n\n{body}")
    conv_md = "\n\n---\n\n".join(conv_blocks)

    body_text = f"""---
date: {target_date_str}
tags:
  - antigravity
  - daily-log
type: daily-report
---

# 📅 {target_date_str} Antigravity 1日の記録

## 📝 AIが編集・作成したファイル履歴

{files_md}

## 📊 AIとよっちゃんのやり取り図解 ＆ 今後の課題・問題点

### 1. やり取りの全体フロー図（全 {data['user_turns']} 往復 ・ {data['conv_count']} セッション）

```mermaid
{data['mermaid_auto']}
```

### 2. 現状診断（核・質・特・欠）と今後の課題解決ベクトル（方・移・拡・新）

| 視点 | 診断結果（やり取りから見えた事実と課題） |
| :--- | :--- |
| **【核】核心** | 本日の主要テーマ：{data['topics_summary']} を軸に、よっちゃんの意図（Vibe）を具体的な手順・設定・コードへ変換。 |
| **【質】品質** | {qual_md} |
| **【特】特性** | 「前提条件の確認（Think Before Coding）」と選択肢（A/B/C）の提示により、最小のタイプ数で合意形成と実行が回っている。 |
| **【欠】欠損（問題点）** | {issues_md} |

| ベクトル | 今後の具体的な改善アクション |
| :--- | :--- |
| **【方】方向性** | **暗黙知のレシピ化（Compilation）**：本日のやり取りで確定した手順やコマンドを、再利用可能な標準レシピ・長期記憶（`memories/`）として定着させる。 |
| **【移】移動性** | **1テーマ＝1ファイル＆ダッシュボード連携**：成果物の保存先を迷わせないよう独立ファイル化し、[[Cockpit_MOC]] や日報目次から即座にアクセス可能にする。 |
| **【拡】拡張性** | **アイアンマンスーツ化（自動化スクリプト連携）**：定型作業や検証コマンドをスクリプト・タスクスケジューラへ組み込み、人間の手作業ループを削減する。 |
| **【新】新規性** | **視覚化（図解・表）の標準適用**：複雑な仕様やログは文字だけで追わず、ズーム可能なフロー図とマトリクス表で直感的に俯瞰する。 |

## 💬 会話ログ

{conv_md}
"""

    # 本文中でリンクされた関連ノートを収集して末尾ナビゲーションにまとめる
    found_links = list(dict.fromkeys(re.findall(r"\[\[([^\]|]+)(?:\|[^\]]+)?\]\]", body_text)))
    related_notes = [lnk for lnk in found_links if lnk != "Cockpit_MOC"]
    nav_lines = [
        "---",
        "## 🔗 関連ナビゲーション",
        "- [[Cockpit_MOC]]",
    ]
    for lnk in related_notes[:20]:
        nav_lines.append(f"- [[{lnk}]]")

    md_doc = body_text + "\n" + "\n".join(nav_lines) + "\n"
    out_file.write_text(md_doc, encoding="utf-8")
    _backup_to_gdrive(out_file)
    return out_file


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--all":
        existing_reports = sorted(OUTPUT_DIR.glob("*_Antigravity日報.md"))
        all_dates = [rf.name.split("_")[0] for rf in existing_reports]
        today_str = datetime.now(JST).strftime("%Y-%m-%d")
        if today_str not in all_dates:
            all_dates.append(today_str)
        data_map = collect_all_daily_data(set(all_dates))
        updated_md = 0
        for d_str in sorted(all_dates):
            pre = data_map.get(d_str)
            if generate_markdown(d_str, precollected=pre) is not None:
                updated_md += 1
        print(f"Updated {updated_md} Markdown reports (checked {len(all_dates)} dates).")
    else:
        target_date = sys.argv[1] if len(sys.argv) > 1 else datetime.now(JST).strftime("%Y-%m-%d")
        pre = collect_daily_data(target_date)
        saved_md = generate_markdown(target_date, precollected=pre)
        if saved_md:
            print(f"Saved Markdown: {saved_md}")
        else:
            print(f"Skipped Markdown (0 conversations): {target_date}")
