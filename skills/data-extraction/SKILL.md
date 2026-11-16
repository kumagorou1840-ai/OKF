---
name: data-extraction
description: "失敗パターン(PAT-004)を解消した堅牢なJSON抽出プロトコル"
version: 1.3
updated: 2026-10-06
---

# Data Extraction Workflow

## 実行プロトコル (Version 1.3)
1. 対象ファイルを2,000トークンごとにストリーム分割する。
2. 正規表現によるJSONテキスト抽出・パースを完全に排除し、組み込みJSONパーサーおよびトークンベースASTパースを採用する。
   - *Rationale: [[wiki/patterns/PAT-004_regex-json-timeout|正規表現タイムアウト・不一致防止]]*
3. 入力データの事前長さ検証とスキーマ互換性チェックを行い、タイムアウトやバックトラックを抑止する。
4. 抽出結果を厳格なスキーマ定義に沿って検証し、構造化データ（JSON）として統合出力する。

## 改善の根拠 (Rationale)
- 解決済みパターン: [[wiki/patterns/PAT-004_regex-json-timeout]]
- 過去解決パターン: [[wiki/patterns/PAT-002_regex-backtracking-timeout]]
- 採択イテレーション: iter-05
