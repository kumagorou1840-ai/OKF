import datetime
from pathlib import Path

# Vaultのルートディレクトリ（当スクリプトの親階層を想定）
VAULT_ROOT = Path(__file__).resolve().parent.parent

RAW_DIR = VAULT_ROOT / "raw"
WIKI_LOGS_FILE = VAULT_ROOT / "wiki" / "logs.md"


def record_execution_and_update_wiki(
    task_id: str,
    iteration: str,
    status: str,
    reasoning_summary: str,
    trace_content: str,
):
    """raw/ に実行トレースを保存し、wiki/logs.md に履歴を追記する"""
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    date_prefix = datetime.datetime.now().strftime("%Y-%m-%d")

    # 1. raw/ への新規実行ログ書き込み (Immutable)
    raw_filename = f"{date_prefix}_{task_id}.md"
    raw_file_path = RAW_DIR / raw_filename

    raw_text = f"""---
task_id: {task_id}
iteration: {iteration}
timestamp: {now_str}
status: {status}
---

# Execution Trace: {task_id}

## Reasoning Summary
{reasoning_summary}

## Raw Output / Tool Calls
```text
{trace_content}
```
"""
    raw_file_path.write_text(raw_text, encoding="utf-8")
    print(f"実行ログを保存しました: {raw_file_path}")

    # 2. wiki/logs.md へのログ追記
    if WIKI_LOGS_FILE.exists():
        log_entry = f"\n## {iteration} ({now_str})\n- タスクID: `{task_id}`\n- ステータス: `{status}`\n- ログ参照: [[raw/{raw_filename}]]\n- 要約: {reasoning_summary}\n"
        with open(WIKI_LOGS_FILE, "a", encoding="utf-8") as f:
            f.write(log_entry)
        print(f"Wikiログを更新しました: {WIKI_LOGS_FILE}")


if __name__ == "__main__":
    record_execution_and_update_wiki(
        task_id="task-001",
        iteration="iter-01",
        status="success",
        reasoning_summary="データ抽出処理のベースラインテスト完了。",
        trace_content="チャンク分割を行い、データを正常に抽出しました。",
    )

import re

PATTERNS_DIR = VAULT_ROOT / "wiki" / "patterns"
SKILL_IMPACT_FILE = VAULT_ROOT / "wiki" / "skill-impact.md"


def get_next_pattern_id() -> str:
    """既存のPATファイルから次の連番ID（例: PAT-002）を算出する"""
    PATTERNS_DIR.mkdir(parents=True, exist_ok=True)
    existing_files = list(PATTERNS_DIR.glob("PAT-*.md"))
    max_num = 0
    for f in existing_files:
        m = re.match(r"PAT-(\d+)", f.name)
        if m:
            max_num = max(max_num, int(m.group(1)))
    return f"PAT-{max_num + 1:03d}"


def record_failure_and_rollback(
    iteration: str,
    skill_target: str,
    proposed_action: str,
    baseline_acc: str,
    candidate_acc: str,
    error_title: str,
    root_cause: str,
    lesson: str,
    raw_log_filename: str,
):
    """失敗パターンノートを作成し、skill-impact.md に拒否ログを記録する"""
    pattern_id = get_next_pattern_id()
    pattern_filename = f"{pattern_id}_{error_title.replace(' ', '-').lower()}.md"
    pattern_file_path = PATTERNS_DIR / pattern_filename

    # 1. wiki/patterns/ に新規パターンノートを作成
    pattern_md = f"""---
id: {pattern_id}
type: failure
detected_iteration: {iteration}
status: active
---

# Failure Pattern: {error_title}

## 発生事象・根本原因
{root_cause}

## 得られた教訓（Lesson）
{lesson}

## 関連ログ・対象スキル
- 実行ログ: [[raw/{raw_log_filename}]]
- 対象スキル: [[skills/{skill_target}/SKILL]]
"""
    pattern_file_path.write_text(pattern_md, encoding="utf-8")
    print(f"[OK] 新規失敗パターンを作成: {pattern_file_path.name}")

    # 2. wiki/skill-impact.md にテーブル行と詳細を追記
    impact_entry = f"""| {iteration} | `{skill_target}` | {proposed_action} | {baseline_acc} | {candidate_acc} | **REJECTED** | [[diff-{iteration}]] |

### {iteration} Rejection Details
- **Reason**: {error_title}
- **Wiki Pattern Linked**: [[wiki/patterns/{pattern_filename[:-3]}]]
- **Lesson**: {lesson}

"""
    with open(SKILL_IMPACT_FILE, "a", encoding="utf-8") as f:
        f.write(impact_entry)
    print(f"[OK] wiki/skill-impact.md に拒否ログを追記しました")


if __name__ == "__main__":
    # テスト実行（失敗時のシミュレーション）
    record_failure_and_rollback(
        iteration="iter-03",
        skill_target="data-extraction",
        proposed_action="Strict regex validation",
        baseline_acc="53.2%",
        candidate_acc="47.8%",
        error_title="regex-backtracking-timeout",
        root_cause="正規表現の破綻（Catastrophic Backtracking）により処理がハングアップした。",
        lesson="正規表現による完全一致検証を廃止し、トークンベースの分割パースを採用すること。",
        raw_log_filename="2026-10-05_task-001.md",
    )    

    SKILLS_DIR = VAULT_ROOT / "skills"


def accept_skill_update(
    iteration: str,
    skill_target: str,
    new_version: str,
    proposed_action: str,
    baseline_acc: str,
    candidate_acc: str,
    description: str,
    updated_instructions: str,
    related_pattern_id: str,
):
    """検証成功時: skills/ の SKILL.md を更新し、skill-impact.md に ACCEPTED を記録する"""
    skill_folder = SKILLS_DIR / skill_target
    skill_folder.mkdir(parents=True, exist_ok=True)
    skill_file_path = skill_folder / "SKILL.md"

    today_str = datetime.datetime.now().strftime("%Y-%m-%d")

    # 1. skills/<target>/SKILL.md を正式更新
    skill_md = f"""---
name: {skill_target}
description: "{description}"
version: {new_version}
updated: {today_str}
---

# {skill_target.replace('-', ' ').title()} Workflow

## 実行プロトコル (Version {new_version})
{updated_instructions}

## 改善の根拠 (Rationale)
- 解決パターン: [[wiki/patterns/{related_pattern_id}]]
- 採択イテレーション: {iteration}
"""
    skill_file_path.write_text(skill_md, encoding="utf-8")
    print(f"[OK] スキルを正式更新しました: {skill_file_path.name} (v{new_version})")

    # 2. wiki/skill-impact.md に ACCEPTED 行と詳細を追記
    impact_entry = f"""| {iteration} | `{skill_target}` | {proposed_action} | {baseline_acc} | {candidate_acc} | **ACCEPTED** | [[diff-{iteration}]] |

### {iteration} Acceptance Details
- **Action**: {proposed_action}
- **Accuracy Gain**: {baseline_acc} -> {candidate_acc}
- **Resolved Wiki Pattern**: [[wiki/patterns/{related_pattern_id}]]

"""
    with open(SKILL_IMPACT_FILE, "a", encoding="utf-8") as f:
        f.write(impact_entry)
    print(f"[OK] wiki/skill-impact.md に採択ログを追記しました")


if __name__ == "__main__":
    # 成功パターンのテスト実行
    accept_skill_update(
        iteration="iter-04",
        skill_target="data-extraction",
        new_version="1.2",
        proposed_action="Token-based stream parsing",
        baseline_acc="47.8%",
        candidate_acc="65.4%",
        description="長文ファイルからのストリーム型構造化データ抽出",
        updated_instructions="""1. 対象ファイルを2,000トークンごとにストリーム分割する。
2. 正規表現を使わず、トークンベースのASTパーサーで要点を抽出する。
   - *Rationale: [[wiki/patterns/PAT-002_regex-backtracking-timeout|正規表現タイムアウト防止]]*
3. 抽出結果をスキーマ定義に沿ってJSON形式で統合出力する。""",
        related_pattern_id="PAT-002_regex-backtracking-timeout",
    )