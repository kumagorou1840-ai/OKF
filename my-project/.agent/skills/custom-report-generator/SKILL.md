---
name: custom-report-generator
description: 収集したデータやログを読み込み、指定されたフォーマットのマークダウンレポートを自動生成する手順。
---

# Custom Report Generator Skill

## 概要
ユーザーからの指示やプロジェクト内の未処理データに基づき、構造化されたレポートを自動生成するための手順。

## 実行ステップ
1. **データ収集:** プロジェクト内の `02_Logs/` または指定されたパスから対象データをスキャンする。
2. **構造化:** 以下のテンプレート（`templates/report_template.md`）に沿って項目を整理する。
3. **ファイル出力:** 生成したコンテンツを `06_Reports/` フォルダ内にタイムスタンプ付きのファイル名で保存する。
```bash
   python .agent/skills/custom-report-generator/scripts/generate_report.py
```
   
## 制約事項
- 出力するファイル名の形式は `YYYY-MM-DD_report.md` とする。
- 専門用語やデータ値に矛盾がないか自己検証（セルフレビュー）を行うこと。