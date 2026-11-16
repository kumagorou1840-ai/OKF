# GEMINI.md - 不動産賃貸経営データ基盤 & ダッシュボード設計指針

## 1. プロジェクト概要
DuckDB (`data/rental_data.duckdb`) と SQLite (`property_management.db`) を連携し、Pydantic v2 による厳密な型検証と Plotly × Streamlit によるインタラクティブ可視化を行う不動産賃貸経営ダッシュボード。

## 2. アーキテクチャ & モジュール構成
- `src/db.py`: 家賃収入・稼働率・空室損失額（機会損失）集計および DuckDB / SQLite 生データ閲覧（Read-Only）
- `src/etl_sync.py`: SQLite (`mode=ro`) から DuckDB (`rental_records`) への冪等同期（`DELETE` + `INSERT` トランザクション）
- `src/models_finance.py`: 修繕履歴・実質利回り（NOI）計算用の共通 Pydantic v2 スキーマ契約
- `src/repair_db.py`: 修繕費データ（`repair_records`）の初期化および月次集計
- `src/yield_calc.py`: 家賃収入と修繕費から純営業収益（NOI）・表面利回り・実質利回りを算出する純粋関数
- `app.py`: 4タブ構成の Streamlit × Plotly ダッシュボードUI
- `start_dashboard.bat`: ワンクリック ETL 同期＆ダッシュボード起動バッチ（ASCII + CRLF）

## 3. 厳守ルール（`@duckdb-streamlit-pipeline` 準拠）
1. **型安全（Right Is Right）**: すべての入出力は Pydantic v2 の `BaseModel` で検証し、生 `dict` の受け渡しを禁止する。
2. **元データ保護と機密マスキング**: SQLite 参照時は URI `mode=ro`、DuckDB 参照時は `read_only=True` を徹底し、電話番号等の個人情報はマスク表示する。実DBファイル（`*.db`, `*.duckdb`）やログ（`*.log`）は Git 管理外とする。
3. **構造化ログ**: 例外・データ欠損時は `logs/app.log` に JSON 1行形式で記録する。
4. **自律検証ループ**: 変更後は必ず `pytest tests/ -v` と `streamlit run app.py --server.headless true` の両方をパスさせる。
