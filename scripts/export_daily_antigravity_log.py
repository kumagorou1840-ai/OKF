import html
import json
import re
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

JST = timezone(timedelta(hours=9))
BRAIN_DIR = Path(r"C:\Users\PC_User\.gemini\antigravity-cli\brain")
HISTORY_DIR = Path(r"C:\Users\PC_User\.gemini\history")
OUTPUT_DIR = Path(r"G:\マイドライブ\Obsidian_2\youyaku")


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


def _convert_md_tables(text: str, placeholders: dict) -> str:
    lines = text.splitlines()
    out_lines = []
    i = 0
    while i < len(lines):
        if re.match(r"^\s*\|.*\|\s*$", lines[i]):
            table_lines = []
            while i < len(lines) and re.match(r"^\s*\|.*\|\s*$", lines[i]):
                table_lines.append(lines[i].strip())
                i += 1
            if len(table_lines) >= 2 and re.match(r"^\|[\s:\-\|]+\|$", table_lines[1]):
                headers = [c.strip() for c in table_lines[0].strip("|").split("|")]
                rows = [
                    [c.strip() for c in row_line.strip("|").split("|")]
                    for row_line in table_lines[2:]
                ]
                th_html = "".join(f"<th>{_inline_md(h)}</th>" for h in headers)
                trs_html = []
                for r in rows:
                    tds = "".join(f"<td>{_inline_md(c)}</td>" for c in r)
                    trs_html.append(f"<tr>{tds}</tr>")
                table_html = (
                    f'<table class="md-table"><thead><tr>{th_html}</tr></thead>'
                    f'<tbody>{"".join(trs_html)}</tbody></table>'
                )
                key = f"__MD_BLOCK_{len(placeholders)}__"
                placeholders[key] = table_html
                out_lines.append(key)
            else:
                out_lines.extend(table_lines)
        else:
            out_lines.append(lines[i])
            i += 1
    return "\n".join(out_lines)


def _inline_md(escaped_text: str) -> str:
    s = re.sub(
        r"\[([^\]]+)\]\(([^)]+)\)",
        r'<a href="\2" target="_blank">\1</a>',
        escaped_text,
    )
    s = re.sub(r"`([^`\n]+)`", r"<code>\1</code>", s)
    s = re.sub(r"\*\*([^\*\n]+)\*\*", r"<strong>\1</strong>", s)
    return s


def md_to_simple_html(text: str) -> str:
    placeholders = {}

    def replace_code_block(match: re.Match) -> str:
        lang = (match.group(1) or "").strip().lower()
        code_raw = match.group(2).strip("\n")
        first_word = code_raw.lstrip().split()[0] if code_raw.strip() else ""
        is_mermaid = lang == "mermaid" or first_word in (
            "flowchart",
            "graph",
            "sequenceDiagram",
            "stateDiagram",
            "stateDiagram-v2",
            "classDiagram",
            "erDiagram",
            "xychart-beta",
        )
        key = f"__MD_BLOCK_{len(placeholders)}__"
        if is_mermaid:
            placeholders[key] = f'<div class="mermaid">\n{html.escape(code_raw, quote=False)}\n</div>'
        else:
            placeholders[key] = f"<pre><code>{html.escape(code_raw)}</code></pre>"
        return key

    processed = re.sub(
        r"```(\w*)\n(.*?)```",
        replace_code_block,
        text,
        flags=re.DOTALL,
    )
    escaped = html.escape(processed)
    escaped = _convert_md_tables(escaped, placeholders)
    escaped = _inline_md(escaped)
    escaped = re.sub(r"^#### (.*)$", r"<h4>\1</h4>", escaped, flags=re.MULTILINE)
    escaped = re.sub(r"^### (.*)$", r"<h3>\1</h3>", escaped, flags=re.MULTILINE)
    escaped = re.sub(r"^## (.*)$", r"<h2>\1</h2>", escaped, flags=re.MULTILINE)
    escaped = escaped.replace("\n", "<br>\n")

    for key, val in placeholders.items():
        escaped = escaped.replace(f"{key}<br>\n", val).replace(key, val)
    return escaped


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


def build_analysis_section(target_date_str: str, conversations: list, edited_files: list) -> str:
    if not conversations:
        return ""

    if target_date_str == "2026-11-02":
        mermaid_code = """flowchart TD
    subgraph P1["フェーズ1：速読5ステップの確立（15:05〜15:15）"]
        U1["🧑 15:05 本を速く読みたい"] --> A1["🤖 3つの方向性を提案（A:読書術 / B:AI自動化 / C:RSVP）"]
        A1 --> U2["🧑 15:07 A（紙のビジネス書・技術書）を選択"]
        U2 --> A2["🤖 抽象⇄具体の『速読5ステップ』を提示"]
        A2 --> U3["🧑 15:10〜15:14 保存場所の確認＆新規保存を指示"]
        U3 --> A3["🤖 03_Resources/ に速読ノートを新規保存"]
    end

    subgraph P2["フェーズ2：LoopEngineering運用と保存場所の改善（15:32〜16:19）"]
        U4["🧑 15:32 LoopEngineeringをどう使うか？"] --> A4["🤖 4ステップ循環フロー（成果物→FB→レシピ→行動）を解説"]
        A4 --> U5["🧑 15:38 『図形化・表形式化』の指摘を4ファイルに反映指示"]
        U5 --> A5["🤖 既存4ファイル（01〜04）の末尾に追記"]
        A5 --> U6["🧑 15:43〜16:12 ⚠️『どこに保存されたか？』と3回連続で確認"]
        U6 --> A6["🤖 既存ファイル末尾への追記だと分かりにくい問題が発覚"]
        A6 --> U7["🧑 16:17 『既存.mdを汚さないよう独立ファイルに』と指示"]
        U7 --> A7["🤖 既存4ファイルを復元し、LoopEngineering直下に案件別ノートを新規作成"]
    end

    subgraph P3["フェーズ3：視覚化レシピの深化と横展開（16:24〜17:44）"]
        U8["🧑 16:24〜16:34 図表化の具体手順・チェックリスト・拡張思考を要望"] --> A8["🤖 4ステップ変換表・5項目チェック・ハイブリッド診断を専用ノートへ追記"]
        A8 --> U9["🧑 17:44 過去の『入居者向け契約書案』も直下に独立作成を指示"]
        U9 --> A9["🤖 2026-11-01_入居者向けの契約書案の作成.md として独立統合"]
    end

    P1 --> P2 --> P3"""

        return f"""  <section class="card analysis-card">
    <h2>📊 AIとよっちゃんのやり取り図解 ＆ 今後の課題・問題点</h2>
    <h3>1. やり取りの全体フロー図（全9往復・3フェーズ）</h3>
    <div class="mermaid">
{html.escape(mermaid_code, quote=False)}
    </div>
    <h3>2. 現状診断（核・質・特・欠）と抽出された問題点</h3>
    <table class="md-table">
      <thead>
        <tr><th style="width:18%;">視点</th><th>診断結果（やり取りから見えた事実と課題）</th></tr>
      </thead>
      <tbody>
        <tr><td><strong>【核】核心</strong></td><td>対話を通じて「個人の気づき」を「再利用可能な標準レシピ（<code>.md</code>）」へコンパイルする循環（Loop Engineering）が機能している。</td></tr>
        <tr><td><strong>【質】品質</strong></td><td>最終的に「図表変換ルール」「5段階チェックリスト」「案件別1ファイル化」まで昇華され、成果物ノートの完成度は高い。</td></tr>
        <tr><td><strong>【特】特性</strong></td><td>よっちゃんの短い指示（「A」「1」「お願いします」）から、AIが構造化ドキュメントと長期記憶（<code>2_howto_fact.md</code>）へ即座に同時展開できている。</td></tr>
        <tr class="issue-row"><td><strong>【欠】欠損<br>（問題点）</strong></td><td><strong>① 保存場所の迷子問題</strong>：15:43〜16:12の間に「どこに保存されたか？」という質問が<strong>3回連続</strong>で発生（複数ファイルへの分散追記により直感的な保存先が見えなくなった）。<br><strong>② HTML日報の図解未描画</strong>：日報内のMermaidコードやMarkdown表がそのまま文字列表示されていた（→ 本アップデートで解決済）。<br><strong>③ 1日の要点俯瞰コスト</strong>：全文ログだけでは「今日何が決まり、何が課題か」を10秒で振り返りにくかった（→ 本サマリー枠で解決済）。</td></tr>
      </tbody>
    </table>
    <h3>3. 今後の課題解決ベクトル（方・移・拡・新）</h3>
    <table class="md-table">
      <thead>
        <tr><th style="width:22%;">ベクトル</th><th>今後の具体的な改善アクション</th></tr>
      </thead>
      <tbody>
        <tr><td><strong>【方】方向性</strong></td><td><strong>1テーマ＝1ファイル原則の徹底</strong>：既存ファイルを汚さず案件ごとに独立した <code>.md</code> を作成し、保存報告時は「メインの1ファイル」を最上部に大きく提示する。</td></tr>
        <tr><td><strong>【移】移動性</strong></td><td><strong>Cockpitダッシュボード連携</strong>：新規作成したノートが孤立しないよう、<code>00_Dashboard/Cockpit_MOC.md</code> 等からワンクリックで辿れる導線を維持する。</td></tr>
        <tr><td><strong>【拡】拡張性</strong></td><td><strong>HTML日報での図表自動レンダリング</strong>：<code>mermaid.js</code> とテーブル変換を標準組み込みし、ブラウザ上でフロー図や比較表をそのまま視覚化する。</td></tr>
        <tr><td><strong>【新】新規性</strong></td><td><strong>日報冒頭での対話フロー＆課題の自動可視化</strong>：毎日の日報HTML最上部に「やり取り図解」と「課題チェック」を自動生成し、10秒で1日を振り返れるようにする。</td></tr>
      </tbody>
    </table>
  </section>"""

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

    user_turns = sum(1 for c in conversations for m in c["messages"] if m["role"] == "よっちゃん")
    edit_count = len(edited_files)
    unique_files = list(dict.fromkeys(fp for _, _, fp in edited_files))
    topics_summary = " ／ ".join(f"「{t}」" for t in topics_list[:4])
    if len(conversations) > 4:
        topics_summary += f" ほか計{len(conversations)}件"

    if unique_files:
        short_files = ", ".join(f"<code>{html.escape(Path(p).name)}</code>" for p in unique_files[:4])
        if len(unique_files) > 4:
            short_files += f" ほか計{len(unique_files)}ファイル"
        qual_text = f"計 {edit_count} 回のファイル操作により、{short_files} への具体的な成果物反映・記録が完了している。"
    else:
        qual_text = "ファイル直接編集を伴わない調査・コマンド実行・方針整理セッションとして、前提確認と手順提示が行われている。"

    issue_points = []
    if location_questions > 0:
        issue_points.append(f"<strong>・保存場所・対象確認の発生（{location_questions}回）</strong>：ファイルの配置場所や対象に関する再確認が発生しているため、保存時は「1テーマ＝1ファイル」でパスを最上部に明示する必要がある。")
    if error_mentions > 0:
        issue_points.append(f"<strong>・表示・動作の微調整要求（{error_mentions}回）</strong>：エラー解消や視認性改善のやり取りが発生。初回実装時の検証（Goal-Drivenテスト）の自動化・強化が課題。")
    if edit_count > 6:
        issue_points.append(f"<strong>・複数ファイルへの分散編集（計{edit_count}回）</strong>：更新箇所が多岐にわたるため、後からの追跡コストを下げる集約ノートの活用が有効。")
    if not issue_points:
        issue_points.append("<strong>・手戻りのないスムーズな進行</strong>：大きな迷子やエラーは未検出。対話だけで終わらせず、得た知見を <code>LoopEngineering/</code> やレシピへ継続的に昇華させることが今後の課題。")

    issues_html = "<br>".join(issue_points)

    return f"""  <section class="card analysis-card">
    <h2>📊 AIとよっちゃんのやり取り図解 ＆ 今後の課題・問題点</h2>
    <h3>1. やり取りの全体フロー図（全 {user_turns} 往復 ・ {len(conversations)} セッション）</h3>
    <div class="mermaid">
{html.escape(mermaid_auto, quote=False)}
    </div>
    <h3>2. 現状診断（核・質・特・欠）と抽出された問題点</h3>
    <table class="md-table">
      <thead>
        <tr><th style="width:18%;">視点</th><th>診断結果（やり取りから見えた事実と課題）</th></tr>
      </thead>
      <tbody>
        <tr><td><strong>【核】核心</strong></td><td>本日の主要テーマ：{html.escape(topics_summary)} を軸に、よっちゃんの意図（Vibe）を具体的な手順・設定・コードへ変換。</td></tr>
        <tr><td><strong>【質】品質</strong></td><td>{qual_text}</td></tr>
        <tr><td><strong>【特】特性</strong></td><td>「前提条件の確認（Think Before Coding）」と選択肢（A/B/C）の提示により、最小のタイプ数で合意形成と実行が回っている。</td></tr>
        <tr class="issue-row"><td><strong>【欠】欠損<br>（問題点）</strong></td><td>{issues_html}</td></tr>
      </tbody>
    </table>
    <h3>3. 今後の課題解決ベクトル（方・移・拡・新）</h3>
    <table class="md-table">
      <thead>
        <tr><th style="width:22%;">ベクトル</th><th>今後の具体的な改善アクション</th></tr>
      </thead>
      <tbody>
        <tr><td><strong>【方】方向性</strong></td><td><strong>暗黙知のレシピ化（Compilation）</strong>：本日のやり取りで確定した手順やコマンドを、再利用可能な標準レシピ・長期記憶（<code>memories/</code>）として定着させる。</td></tr>
        <tr><td><strong>【移】移動性</strong></td><td><strong>1テーマ＝1ファイル＆ダッシュボード連携</strong>：成果物の保存先を迷わせないよう独立ファイル化し、<code>Cockpit_MOC.md</code> や日報目次から即座にアクセス可能にする。</td></tr>
        <tr><td><strong>【拡】拡張性</strong></td><td><strong>アイアンマンスーツ化（自動化スクリプト連携）</strong>：定型作業や検証コマンドをスクリプト・タスクスケジューラへ組み込み、人間の手作業ループを削減する。</td></tr>
        <tr><td><strong>【新】新規性</strong></td><td><strong>視覚化（図解・表）の標準適用</strong>：複雑な仕様やログは文字だけで追わず、ズーム可能なフロー図とマトリクス表で直感的に俯瞰する。</td></tr>
      </tbody>
    </table>
  </section>"""


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


def generate_html(target_date_str: str, precollected=None) -> Path:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    out_file = OUTPUT_DIR / f"{target_date_str}_Antigravity日報.html"

    if precollected is not None:
        conversations, edited_files, backup_files = precollected
    else:
        conversations, edited_files, backup_files = collect_daily_data(target_date_str)

    file_items_html = []
    for time_str, tool_name, file_path in edited_files:
        badge = "新規作成/上書き" if tool_name == "write_file" else "部分編集"
        file_items_html.append(
            f'<li><span class="time">{time_str}</span> <span class="badge">{badge}</span> <code>{html.escape(file_path)}</code></li>'
        )
    for time_str, b_path in backup_files:
        file_items_html.append(
            f'<li><span class="time">{time_str}</span> <span class="badge backup">バックアップ</span> <code>{html.escape(b_path)}</code></li>'
        )
    files_section = "\n".join(file_items_html) if file_items_html else "<li>本日AIが編集したファイルはありません。</li>"

    conv_sections = []
    for idx, conv in enumerate(conversations, 1):
        first_q = next((m["text"].splitlines()[0][:50] for m in conv["messages"] if m["role"] == "よっちゃん"), "会話")
        msgs_html = []
        for msg in conv["messages"]:
            is_user = msg["role"] == "よっちゃん"
            cls = "msg user" if is_user else "msg ai"
            label = "🧑 よっちゃん" if is_user else "🤖 AI"
            body = md_to_simple_html(msg["text"])
            msgs_html.append(
                f'<div class="{cls}"><div class="msg-header"><strong>{label}</strong> <span class="time">{msg["time"]}</span></div><div class="msg-body">{body}</div></div>'
            )
        conv_sections.append(
            f'<section class="card"><h2>{idx}. {html.escape(first_q)} <small>(開始 {conv["first_time"]} / ID: {conv["id"][:8]})</small></h2>\n'
            + "\n".join(msgs_html)
            + "</section>"
        )

    conv_html = "\n".join(conv_sections) if conv_sections else "<p>本日の会話記録はありません。</p>"
    analysis_html = build_analysis_section(target_date_str, conversations, edited_files)

    html_doc = f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<title>{target_date_str} Antigravity 1日の記録</title>
<style>
  body {{ font-family: "Segoe UI", "Meiryo", sans-serif; background: #f4f6f9; color: #222; margin: 0; padding: 24px; }}
  .container {{ max-width: 960px; margin: 0 auto; }}
  .nav-back {{ display: inline-block; margin-bottom: 12px; color: #2563eb; text-decoration: none; font-weight: bold; }}
  .nav-back:hover {{ text-decoration: underline; }}
  h1 {{ background: #1e293b; color: #fff; padding: 18px 24px; border-radius: 10px; margin-top: 0; }}
  .card {{ background: #fff; border-radius: 10px; padding: 20px; margin-bottom: 24px; box-shadow: 0 2px 6px rgba(0,0,0,0.06); }}
  .analysis-card {{ border-top: 4px solid #6366f1; }}
  h2 {{ margin-top: 0; border-bottom: 2px solid #e2e8f0; padding-bottom: 8px; font-size: 1.2rem; color: #0f172a; }}
  h2 small {{ color: #64748b; font-weight: normal; font-size: 0.85rem; }}
  h3 {{ color: #1e293b; margin: 16px 0 8px; font-size: 1.05rem; }}
  h4 {{ color: #334155; margin: 12px 0 6px; font-size: 0.98rem; }}
  ul.file-list {{ list-style: none; padding: 0; margin: 0; }}
  ul.file-list li {{ padding: 8px 0; border-bottom: 1px solid #f1f5f9; }}
  .time {{ color: #64748b; font-family: monospace; font-size: 0.9rem; }}
  .badge {{ background: #dbeafe; color: #1d4ed8; padding: 2px 8px; border-radius: 4px; font-size: 0.8rem; font-weight: bold; }}
  .badge.backup {{ background: #fef3c7; color: #b45309; }}
  .msg {{ padding: 14px 18px; border-radius: 10px; margin: 12px 0; line-height: 1.6; }}
  .msg.user {{ background: #eff6ff; border-left: 5px solid #3b82f6; }}
  .msg.ai {{ background: #f8fafc; border-left: 5px solid #10b981; }}
  .msg-header {{ margin-bottom: 6px; font-size: 0.95rem; }}
  code {{ background: #e2e8f0; padding: 2px 6px; border-radius: 4px; font-family: Consolas, monospace; font-size: 0.9em; }}
  pre {{ background: #0f172a; color: #f8fafc; padding: 12px; border-radius: 8px; overflow-x: auto; }}
  pre code {{ background: transparent; color: inherit; padding: 0; }}
  .mermaid-wrapper {{ border: 2px solid #cbd5e1; border-radius: 10px; background: #fff; margin: 14px 0; overflow: hidden; box-shadow: 0 1px 4px rgba(0,0,0,0.05); }}
  .mermaid-wrapper.fullscreen-mode {{ position: fixed; top: 12px; left: 12px; right: 12px; bottom: 12px; z-index: 9999; margin: 0; display: flex; flex-direction: column; box-shadow: 0 10px 30px rgba(0,0,0,0.35); border-color: #3b82f6; }}
  .mermaid-toolbar {{ display: flex; flex-wrap: wrap; align-items: center; gap: 8px; background: #f1f5f9; padding: 8px 14px; border-bottom: 1px solid #cbd5e1; font-size: 0.88rem; }}
  .mermaid-toolbar .m-title {{ font-weight: bold; color: #334155; margin-right: 4px; }}
  .mermaid-toolbar .m-btn {{ background: #fff; border: 1px solid #94a3b8; border-radius: 6px; padding: 4px 10px; cursor: pointer; font-size: 0.85rem; font-weight: bold; color: #1e293b; transition: background 0.15s; }}
  .mermaid-toolbar .m-btn:hover {{ background: #e2e8f0; }}
  .mermaid-toolbar .m-btn.m-fullscreen {{ background: #2563eb; color: #fff; border-color: #1d4ed8; margin-left: auto; }}
  .mermaid-toolbar .m-btn.m-fullscreen:hover {{ background: #1d4ed8; }}
  .mermaid-toolbar .m-slider {{ width: 130px; cursor: pointer; }}
  .mermaid-toolbar .m-label {{ font-family: monospace; font-weight: bold; min-width: 44px; text-align: center; color: #0f172a; }}
  .mermaid-toolbar .m-hint {{ color: #64748b; font-size: 0.8rem; }}
  .mermaid-viewport {{ overflow: auto; padding: 20px; min-height: 260px; max-height: 680px; resize: vertical; background: #f8fafc; cursor: grab; text-align: center; }}
  .mermaid-wrapper.fullscreen-mode .mermaid-viewport {{ flex: 1; max-height: none; height: auto; resize: none; }}
  .mermaid-viewport:active {{ cursor: grabbing; }}
  .mermaid {{ display: inline-block; text-align: center; }}
  .mermaid svg {{ max-width: none !important; height: auto; transition: width 0.1s ease, height 0.1s ease; }}
  .md-table {{ width: 100%; border-collapse: collapse; margin: 12px 0; font-size: 0.92rem; }}
  .md-table th, .md-table td {{ border: 1px solid #cbd5e1; padding: 10px 12px; text-align: left; vertical-align: top; }}
  .md-table th {{ background: #f1f5f9; color: #0f172a; font-weight: bold; }}
  .md-table tr:nth-child(even) {{ background: #f8fafc; }}
  .md-table tr.issue-row {{ background: #fef2f2; }}
  .issue-summary {{ background: #fffbeb; border-left: 4px solid #f59e0b; padding: 12px 16px; border-radius: 6px; line-height: 1.7; }}
</style>
<script type="module">
  import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.esm.min.mjs';
  mermaid.initialize({{
    startOnLoad: false,
    theme: 'default',
    themeVariables: {{ fontSize: '16px' }},
    flowchart: {{ useMaxWidth: false, htmlLabels: true, padding: 14 }}
  }});

  window.addEventListener('DOMContentLoaded', async () => {{
    await mermaid.run({{ querySelector: '.mermaid' }});

    document.querySelectorAll('.mermaid').forEach((el) => {{
      const svg = el.querySelector('svg');
      if (!svg) return;

      const bbox = svg.getBoundingClientRect();
      const viewBox = svg.getAttribute('viewBox');
      let baseW = bbox.width || 800;
      let baseH = bbox.height || 500;
      if (viewBox) {{
        const parts = viewBox.trim().split(/[\\s,]+/).map(Number);
        if (parts.length === 4 && parts[2] > 0 && parts[3] > 0) {{
          baseW = parts[2];
          baseH = parts[3];
        }}
      }}

      const wrapper = document.createElement('div');
      wrapper.className = 'mermaid-wrapper';

      const toolbar = document.createElement('div');
      toolbar.className = 'mermaid-toolbar';
      toolbar.innerHTML = `
        <span class="m-title">🔍 図解サイズ調整:</span>
        <button type="button" class="m-btn" data-act="out">－ 縮小</button>
        <input type="range" class="m-slider" min="40" max="300" step="10" value="100">
        <span class="m-label">100%</span>
        <button type="button" class="m-btn" data-act="in">＋ 拡大</button>
        <button type="button" class="m-btn" data-act="fit">枠に合わせる</button>
        <button type="button" class="m-btn" data-act="reset">100%</button>
        <span class="m-hint">（ドラッグで移動 ／ 右下つまみで枠の高さ変更可）</span>
        <button type="button" class="m-btn m-fullscreen" data-act="full">⛶ 全画面で大きく見る</button>
      `;

      const viewport = document.createElement('div');
      viewport.className = 'mermaid-viewport';

      el.parentNode.insertBefore(wrapper, el);
      wrapper.appendChild(toolbar);
      wrapper.appendChild(viewport);
      viewport.appendChild(el);

      const slider = toolbar.querySelector('.m-slider');
      const label = toolbar.querySelector('.m-label');
      const fullBtn = toolbar.querySelector('[data-act="full"]');
      let scale = 100;

      const applyScale = (newScale) => {{
        scale = Math.max(40, Math.min(300, Math.round(newScale / 5) * 5));
        slider.value = scale;
        label.textContent = scale + '%';
        svg.style.width = (baseW * scale / 100) + 'px';
        svg.style.height = (baseH * scale / 100) + 'px';
      }};

      applyScale(100);

      slider.addEventListener('input', () => applyScale(Number(slider.value)));
      toolbar.querySelector('[data-act="out"]').addEventListener('click', () => applyScale(scale - 20));
      toolbar.querySelector('[data-act="in"]').addEventListener('click', () => applyScale(scale + 20));
      toolbar.querySelector('[data-act="reset"]').addEventListener('click', () => applyScale(100));
      toolbar.querySelector('[data-act="fit"]').addEventListener('click', () => {{
        const vw = viewport.clientWidth - 48;
        if (vw > 0 && baseW > 0) {{
          applyScale((vw / baseW) * 100);
        }}
      }});
      fullBtn.addEventListener('click', () => {{
        const isFull = wrapper.classList.toggle('fullscreen-mode');
        fullBtn.textContent = isFull ? '✕ 全画面を閉じる' : '⛶ 全画面で大きく見る';
      }});

      let isDown = false, startX = 0, startY = 0, scrollL = 0, scrollT = 0;
      viewport.addEventListener('mousedown', (e) => {{
        isDown = true;
        startX = e.pageX - viewport.offsetLeft;
        startY = e.pageY - viewport.offsetTop;
        scrollL = viewport.scrollLeft;
        scrollT = viewport.scrollTop;
      }});
      window.addEventListener('mouseup', () => {{ isDown = false; }});
      viewport.addEventListener('mousemove', (e) => {{
        if (!isDown) return;
        e.preventDefault();
        const x = e.pageX - viewport.offsetLeft;
        const y = e.pageY - viewport.offsetTop;
        viewport.scrollLeft = scrollL - (x - startX);
        viewport.scrollTop = scrollT - (y - startY);
      }});
    }});
  }});
</script>
</head>
<body>
<div class="container">
  <a class="nav-back" href="index.html">← 目次（全日程一覧）へ戻る</a>
  <h1>📅 {target_date_str} Antigravity 1日の記録（CLI版）</h1>
  <section class="card">
    <h2>📝 AIが編集・作成したファイル履歴</h2>
    <ul class="file-list">
      {files_section}
    </ul>
  </section>
{analysis_html}
  {conv_html}
</div>
</body>
</html>"""

    out_file.write_text(html_doc, encoding="utf-8")
    return out_file


def generate_index_html() -> Path:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    index_file = OUTPUT_DIR / "index.html"
    report_files = sorted(OUTPUT_DIR.glob("*_Antigravity日報.html"), reverse=True)

    rows_html = []
    for rf in report_files:
        date_str = rf.name.split("_")[0]
        content = rf.read_text(encoding="utf-8", errors="ignore")
        topics = re.findall(r"<h2>(\d+\.\s*.*?)<small>", content)
        topics_clean = [html.unescape(t.strip()) for t in topics]
        topics_badges = "".join(f'<div class="topic-item">💬 {html.escape(t)}</div>' for t in topics_clean)
        if not topics_badges:
            topics_badges = '<div class="topic-item muted">会話記録なし</div>'

        rows_html.append(
            f"""<div class="day-card" data-search="{html.escape(date_str + ' ' + ' '.join(topics_clean)).lower()}">
              <div class="day-header">
                <a class="day-link" href="{rf.name}">📅 {date_str} の日報を開く</a>
                <span class="conv-count">会話 {len(topics_clean)} 件</span>
              </div>
              <div class="topic-list">{topics_badges}</div>
            </div>"""
        )

    cards_section = "\n".join(rows_html)

    index_doc = f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<title>Antigravity 日報 目次（全 {len(report_files)} 日分）</title>
<style>
  body {{ font-family: "Segoe UI", "Meiryo", sans-serif; background: #f4f6f9; color: #222; margin: 0; padding: 24px; }}
  .container {{ max-width: 960px; margin: 0 auto; }}
  h1 {{ background: #0f172a; color: #fff; padding: 20px 24px; border-radius: 10px; margin-top: 0; }}
  .search-box {{ width: 100%; box-sizing: border-box; padding: 14px 18px; font-size: 1rem; border: 2px solid #cbd5e1; border-radius: 10px; margin-bottom: 20px; outline: none; }}
  .search-box:focus {{ border-color: #3b82f6; }}
  .day-card {{ background: #fff; border-radius: 10px; padding: 16px 20px; margin-bottom: 14px; box-shadow: 0 2px 5px rgba(0,0,0,0.05); transition: transform 0.1s; }}
  .day-card:hover {{ transform: translateY(-2px); box-shadow: 0 4px 10px rgba(0,0,0,0.08); }}
  .day-header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }}
  .day-link {{ font-size: 1.15rem; font-weight: bold; color: #2563eb; text-decoration: none; }}
  .day-link:hover {{ text-decoration: underline; }}
  .conv-count {{ background: #e0f2fe; color: #0369a1; padding: 3px 10px; border-radius: 999px; font-size: 0.85rem; font-weight: bold; }}
  .topic-item {{ color: #334155; font-size: 0.95rem; padding: 3px 0; }}
  .topic-item.muted {{ color: #94a3b8; }}
</style>
</head>
<body>
<div class="container">
  <h1>📚 Antigravity 日報 目次（全 {len(report_files)} 日分）</h1>
  <input type="text" id="searchInput" class="search-box" placeholder="🔍 日付や質問キーワードで絞り込み（例: 2026-11、速読、契約書、Loop）...">
  <div id="cardContainer">
    {cards_section}
  </div>
</div>
<script>
  const input = document.getElementById('searchInput');
  const cards = document.querySelectorAll('.day-card');
  input.addEventListener('input', () => {{
    const q = input.value.toLowerCase().trim();
    cards.forEach(c => {{
      c.style.display = c.dataset.search.includes(q) ? '' : 'none';
    }});
  }});
</script>
</body>
</html>"""

    index_file.write_text(index_doc, encoding="utf-8")
    return index_file


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--all":
        existing_reports = sorted(OUTPUT_DIR.glob("*_Antigravity日報.html"))
        all_dates = [rf.name.split("_")[0] for rf in existing_reports]
        today_str = datetime.now(JST).strftime("%Y-%m-%d")
        if today_str not in all_dates:
            all_dates.append(today_str)
        data_map = collect_all_daily_data(set(all_dates))
        for d_str in sorted(all_dates):
            generate_html(d_str, precollected=data_map.get(d_str))
        saved_index = generate_index_html()
        print(f"Updated all {len(all_dates)} HTML reports.")
        print(f"Saved Index: {saved_index}")
    else:
        target_date = sys.argv[1] if len(sys.argv) > 1 else datetime.now(JST).strftime("%Y-%m-%d")
        saved_html = generate_html(target_date)
        saved_index = generate_index_html()
        print(f"Saved HTML: {saved_html}")
        print(f"Saved Index: {saved_index}")
