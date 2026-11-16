import datetime
import os
from pathlib import Path
import re
import json
from google import genai

# パス設定
VAULT_ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = VAULT_ROOT / "raw"
WIKI_DIR = VAULT_ROOT / "wiki"
PATTERNS_DIR = WIKI_DIR / "patterns"
SKILLS_DIR = VAULT_ROOT / "skills"
IMPACT_FILE = WIKI_DIR / "skill-impact.md"

# フォルダ作成の確保
RAW_DIR.mkdir(parents=True, exist_ok=True)
WIKI_DIR.mkdir(parents=True, exist_ok=True)
PATTERNS_DIR.mkdir(parents=True, exist_ok=True)

# Geminiクライアント初期化
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))


def call_llm(prompt: str, system_instruction: str = "") -> str:
    """Gemini 2.5 Flash を呼び出す共通関数"""
    config = (
        {"system_instruction": system_instruction}
        if system_instruction
        else None
    )
    response = client.models.generate_content(
        model="gemini-2.5-flash", contents=prompt, config=config
    )
    return response.text.strip()


# ==========================================
# 1. Inference Agent (タスク実行)
# ==========================================
def run_inference_agent(
    task_id: str, skill_name: str, task_input: str
) -> dict:
    skill_path = SKILLS_DIR / skill_name / "SKILL.md"
    skill_content = (
        skill_path.read_text(encoding="utf-8") if skill_path.exists() else ""
    )

    system_instruction = f"""あなたは手順を厳密に順守する実行エージェントです。
以下のスキル指示書に従ってタスクを実行してください。
規約違反や指示を満たせない場合は文頭に「ERROR:」を付けて理由を出力してください。

【Active Skill】
{skill_content}
"""
    print(f"[1. Inference] タスク '{task_id}' を実行中...")
    output = call_llm(task_input, system_instruction=system_instruction)

    # 判定：出力に ERROR が含まれるか、またはJSON指定なのにJSON形式でない場合は失敗とする
    is_success = not output.startswith("ERROR:") and (
        "{" in output and "}" in output
    )

    # raw/ に実行トレースを保存
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    raw_filename = f"{datetime.date.today()}_{task_id}.md"
    raw_path = RAW_DIR / raw_filename
    raw_md = f"""---
task_id: {task_id}
timestamp: {now_str}
success: {is_success}
---

# Trace: {task_id}
- **Active Skill**: [[skills/{skill_name}/SKILL]]
- **Input**: {task_input}

## LLM Output
```text
{output}
```
"""
    raw_path.write_text(raw_md, encoding="utf-8")

    return {
        "is_success": is_success,
        "output": output,
        "raw_file": raw_filename,
    }


# ==========================================
# 2. Wiki Maintainer (エラー分析 & Wiki自動更新)
# ==========================================
def run_wiki_maintainer(
    task_id: str, skill_name: str, error_log: str, raw_filename: str = ""
) -> str:
    print(f"[2. Wiki Maintainer] エラーを分析してパターンを抽出中...")

    # 次の PAT ID 番号の算出
    existing_pats = list(PATTERNS_DIR.glob("PAT-*.md"))
    pat_numbers = []
    for p in existing_pats:
        match = re.search(r"PAT-(\d+)", p.name)
        if match:
            pat_numbers.append(int(match.group(1)))
    next_pat_num = max(pat_numbers, default=0) + 1
    pat_id = f"PAT-{next_pat_num:03d}"

    system_instruction = """あなたはシステムエラーから改善パターンを抽出するWikiナレッジ管理者です。
エラーログを分析し、必ず以下のJSONフォーマットのみを出力してください。

```json
{
  "title": "簡潔なパターン名 (例: Regex Timeout on Large Input)",
  "slug": "url-friendly-slug (例: regex-timeout)",
  "cause": "根本原因の説明",
  "lesson": "再発防止のための具体的な教訓"
}
```
"""

    prompt = f"""以下の実行エラーログを分析し、根本原因と再発防止の教訓を抽出してください。

【エラーログ】
{error_log}
"""

    analysis_raw = call_llm(prompt, system_instruction=system_instruction)

    # JSONのパース
    json_match = re.search(r"```json\s*(\{.*?\})\s*```", analysis_raw, re.DOTALL)
    if json_match:
        json_str = json_match.group(1)
    else:
        json_str = analysis_raw.strip("{} \n")
        json_str = "{" + json_str + "}"

    try:
        data = json.loads(json_str)
    except Exception:
        data = {
            "title": "Extraction Failure Pattern",
            "slug": "extraction-failure",
            "cause": error_log,
            "lesson": "入力フォーマットの検証およびストリームパースを採用すること。",
        }

    title = data.get("title", "Unknown Pattern")
    slug = data.get("slug", "pattern-detail")
    cause = data.get("cause", error_log)
    lesson = data.get("lesson", "パース処理を見直すこと。")

    pattern_filename = f"{pat_id}_{slug}.md"
    pattern_path = PATTERNS_DIR / pattern_filename

    # 1. PAT-XXX.md の作成
    pattern_md = f"""---
id: {pat_id}
type: failure
detected_iteration: iter-{next_pat_num:02d}
status: mitigated
---

# Failure Pattern: {title}

## 発生事象
{error_log}

## 根本原因
{cause}

## 関連ログ・スキル
- 実行ログ: [[raw/{raw_filename if raw_filename else 'mock_raw'}]]
- 改善適用スキル: [[skills/{skill_name}/SKILL]]
"""
    pattern_path.write_text(pattern_md, encoding="utf-8")
    print(f"[2. Wiki Maintainer] パターン作成完了: {pattern_path}")

    # 2. skill-impact.md への末尾追記
    impact_entry = f"""
| iter-{next_pat_num:02d} | `{skill_name}` | {title} | - | - | **REJECTED** | [[diff-iter-{next_pat_num:02d}]] |

### iter-{next_pat_num:02d} Rejection Details
- **Reason**: {cause}
- **Wiki Pattern Linked**: [[wiki/patterns/{pat_id}_{slug}]]
- **Lesson**: {lesson}
"""
    with open(IMPACT_FILE, "a", encoding="utf-8") as f:
        f.write(impact_entry)

    print(f"[2. Wiki Maintainer] skill-impact.md 追記完了")
    return str(pattern_path)


if __name__ == "__main__":
    # モックエラーログを用いたテスト実行
    mock_task_id = "test-task-001"
    mock_skill_name = "data-extraction"
    mock_error_log = "ERROR: 入力データから指定されたJSONフォーマット（物件名・家賃）を抽出できませんでした。正規表現の不一致、またはテキスト長によるタイムアウトが発生しています。"

    print("=== WikiSkill Loop (Test Execution) ===")
    pattern_file = run_wiki_maintainer(
        task_id=mock_task_id,
        skill_name=mock_skill_name,
        error_log=mock_error_log,
        raw_filename="2026-10-06_test-task-001.md",
    )
    print(f"テスト成功: {pattern_file} が生成されました。")