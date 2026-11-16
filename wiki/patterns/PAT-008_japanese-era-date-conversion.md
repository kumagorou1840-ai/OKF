---
id: PAT-008
type: failure
detected_iteration: iter-08
status: active
---

# Failure Pattern: 契約書の和暦（令和・平成）混在による日付パース失敗

## 発生事象
「令和6年3月31日満了」「平成30年5月築」等の日付が `YYYY-MM-DD` 形式に変換されず、nullまたは誤った西暦（西暦6年等）として登録された。

## 根本原因
不動産契約書で標準的な元号（令和・平成・昭和）から西暦への変換テーブルおよび正規化処理がプロトコルに含まれていなかった。

## 得られた教訓（Lesson）
日付抽出前に和暦・西暦の相互変換マッピングを適用し、すべてISO 8601形式（YYYY-MM-DD）に統一するステップを設けること。

## 関連ログ・スキル
- 実行ログ: [[raw/2026-10-06_test-task-005.md]]
- 改善適用スキル: [[skills/data-extraction/SKILL]]