---
id: PAT-003
type: failure
detected_iteration: iter-03
status: active
---

# Failure Pattern: regex-backtracking-timeout

## 発生事象・根本原因
正規表現の破綻（Catastrophic Backtracking）により処理がハングアップした。

## 得られた教訓（Lesson）
正規表現による完全一致検証を廃止し、トークンベースの分割パースを採用すること。

## 関連ログ・対象スキル
- 実行ログ: [[raw/2026-10-05_task-001.md]]
- 対象スキル: [[skills/data-extraction/SKILL]]
