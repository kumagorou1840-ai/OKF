---
id: PAT-001
type: failure
detected_iteration: iter-01
status: mitigated
---

# Failure Pattern: Context Overflow in Sub-Agent

## 発生事象
長文ドキュメント処理時にコンテキスト長の上限を超過し、エージェントが途中で停止した。

## 根本原因
Inference Agentがドキュメント全体を一度のプロンプトに注入していたため。

## 関連ログ・スキル
- 実行ログ: [[raw/2026-10-05_task-001]]
- 改善適用スキル: [[skills/data-extraction/SKILL]]
