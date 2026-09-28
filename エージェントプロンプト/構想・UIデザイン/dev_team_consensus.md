# AgyFit 開発側合意書 (dev_team_consensus)

本ドキュメントは、`dev_team`（実装担当：Developer、テスト担当：QA_Reviewer）の間で合意された、AgyFitにおけるデータベース定義および業務仕様に関する結論をまとめたものです。

---

## 1. 開発チーム内の合意プロセス

*   **論点: 過去実績データの保護**
    *   **Developer**: 実装のシンプルさから `ON DELETE CASCADE` による物理削除を予定していたが、ビジネス価値（よっちゃんのこれまでのトレーニング履歴の保全）を最大化するためには不適当であると認識。
    *   **QA_Reviewer**: 物理削除はデータの整合性を保ちやすいが、本アプリにおいては「過去の実績が消える」ことはデータ不整合と同等の品質低下であると指摘。
    *   **結論**: `training_masters` テーブルに `is_active` カラムを追加し、**「論理削除」**に変更する。

---

## 2. 合意された技術仕様

### ① データベース構造の拡張 (`db.py`)
*   `training_masters` テーブルに `is_active INTEGER NOT NULL DEFAULT 1` を追加。
*   種目削除時は `DELETE` クエリの代わりに `logical_delete_master` を使用し、`is_active = 0` に更新する。
*   `training_logs` に対する `ON DELETE CASCADE` 制約は残す（仮にマスタが物理削除された場合の浮いたログ防止のため）。

### ② APIのバリデーションとレスポンス仕様 (`main.py` / `schemas.py`)
*   **マスタ一覧取得 (`GET /api/training/masters`)**:
    *   デフォルトでは `is_active = 1` の有効な種目のみを返す。
    *   `include_inactive=true` パラメータが指定された場合のみ、非アクティブな種目も含めて返す（設定画面の管理用）。
*   **実績一括保存 (`POST /api/training/logs/bulk`)**:
    *   送信された `training_id` が `is_active = 0`（非アクティブ）の場合、および存在しないIDの場合は、**`400 Bad Request`** を返して書き込みを拒否する。
*   **グラフデータ取得 (`GET /api/training/chart-data`)**:
    *   非アクティブ化された種目であっても、指定期間内に実績ログが存在する限り、グラフ描画対象として抽出する。
    *   レスポンスのシリーズデータに `"is_active": false` メタデータを付与し、フロントエンド側で識別できるようにする。

### ③ フロントエンドUIの表示制御 (`static/index.html`)
*   **入力フォーム**: 有効な種目（`is_active: 1`）のみを表示。
*   **グラフ描画 (Chart.js)**:
    *   `is_active === false` のシリーズは、凡例に `[アーカイブ]` を追加。
    *   折れ線グラフのスタイルを「半透明（透過度アップ）」かつ「点線（`borderDash`）」として描画し、視覚的なアーカイブ状態を明確にする。
    *   非アクティブ種目の目標値ガイドライン（水平点線）は、グラフのノイズ削減のため非表示とする。

---

## 3. 品質保証テストプラン

合意された品質水準を満たしていることを、以下のテストコード（`pytest`）を実行して確認する。

1.  `test_db_lifecycle`:
    *   マスタ登録、実績ログ保存、および論理削除の挙動を検証。
    *   論理削除後、有効な一覧からは非表示になり、全体一覧には `is_active = 0` で残り、ログが削除されていないことをアサート。
2.  `test_masters_api`:
    *   APIを介したマスタ作成・論理削除、およびフィルタリングの動作を検証。
3.  `test_logs_and_chart_api`:
    *   非アクティブな種目に対する `POST /api/training/logs/bulk` が `400 Bad Request` になることを検証。
    *   `chart-data` のレスポンスにアーカイブ種目のデータが残っており、`is_active` フラグが正しく設定されていることを検証。

---

## 4. 承認署名

*   **実装担当 (Developer)**: 合意された設計に則り、コードの実装を完了。
*   **テスト担当 (QA_Reviewer)**: すべてのテスト（`test_db.py`, `test_api.py`）がPASSすることを確認・承認。
