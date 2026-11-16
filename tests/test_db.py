#!/usr/bin/env python3
"""
tests/test_db.py
`src/db.py` の DuckDB 集計ロジック・Pydantic v2 バリデーション・構造化エラーログ出力の単体テストスイート。
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import duckdb
import pytest
from pydantic import ValidationError

from src.db import (
    ContractMasterRecord,
    DatabaseOperationError,
    MonthlyRentalSummary,
    PropertyVacancyLossSummary,
    RentalQueryFilter,
    RentalRecordInput,
    TableInspectFilter,
    fetch_duckdb_rental_records,
    fetch_monthly_rental_summary,
    fetch_property_vacancy_loss,
    fetch_sqlite_contracts,
    initialize_sample_duckdb,
    list_property_names,
)


def test_initialize_and_aggregate_all(tmp_path: Path) -> None:
    """サンプルDB初期化と全物件・全期間の集計ロジック検証"""
    db_file = tmp_path / "rental_data.duckdb"
    log_file = tmp_path / "app.log"

    initialize_sample_duckdb(db_path=db_file, force_recreate=True, log_path=log_file)
    assert db_file.exists()

    props = list_property_names(db_path=db_file, log_path=log_file)
    assert len(props) == 3
    assert "北18条レジデンス" in props

    summaries = fetch_monthly_rental_summary(
        RentalQueryFilter(db_path=db_file),
        log_path=log_file,
    )
    # 3物件 × 12ヶ月 = 36レコード
    assert len(summaries) == 36
    assert all(isinstance(s, MonthlyRentalSummary) for s in summaries)

    # 北18条レジデンスの 2026-01 は 10戸中9戸稼働 (稼働率 90.0%, 空室1戸で vacancy_loss > 0)
    jan_p1 = next(
        s for s in summaries if s.property_name == "北18条レジデンス" and s.year_month == "2026-01"
    )
    assert jan_p1.total_units == 10
    assert jan_p1.occupied_units == 9
    assert jan_p1.vacant_units == 1
    assert jan_p1.occupancy_rate == 90.0
    assert jan_p1.rent_revenue > 0
    assert jan_p1.vacancy_loss > 0

    # 物件別の空室損失額（機会損失）集計の検証
    losses = fetch_property_vacancy_loss(
        RentalQueryFilter(db_path=db_file),
        log_path=log_file,
    )
    assert len(losses) == 3
    assert all(isinstance(item, PropertyVacancyLossSummary) for item in losses)
    assert all(item.total_vacancy_loss > 0 for item in losses)
    # 降順ソートの検証
    assert losses[0].total_vacancy_loss >= losses[1].total_vacancy_loss >= losses[2].total_vacancy_loss


def test_filter_by_property_and_month_range(tmp_path: Path) -> None:
    """物件名フィルタおよび年月レンジフィルタの正確性検証"""
    db_file = tmp_path / "rental_data.duckdb"
    log_file = tmp_path / "app.log"
    initialize_sample_duckdb(db_path=db_file, force_recreate=True, log_path=log_file)

    q_filter = RentalQueryFilter(
        db_path=db_file,
        property_names=["円山グリーンハイツ"],
        start_month="2026-03",
        end_month="2026-05",
    )
    summaries = fetch_monthly_rental_summary(q_filter, log_path=log_file)

    assert len(summaries) == 3
    assert [s.year_month for s in summaries] == ["2026-03", "2026-04", "2026-05"]
    assert all(s.property_name == "円山グリーンハイツ" for s in summaries)
    # 2026-03〜05 は 8戸中8戸稼働 = 100.0%
    assert all(s.occupancy_rate == 100.0 for s in summaries)


def test_pydantic_v2_strict_validation() -> None:
    """Pydantic v2 による入出力モデルの異常値・整合性バリデーション検証"""
    # 1. 不正な年月フォーマット
    with pytest.raises(ValidationError):
        RentalRecordInput(
            property_id="P01",
            property_name="テスト物件",
            year_month="2026/13",
            unit_number="101",
            is_occupied=True,
            monthly_rent=50000,
        )

    # 2. start_month > end_month の逆転エラー
    with pytest.raises(ValidationError):
        RentalQueryFilter(
            start_month="2026-08",
            end_month="2026-04",
        )

    # 3. 稼働戸数 > 総戸数 の整合性エラー
    with pytest.raises(ValidationError):
        MonthlyRentalSummary(
            property_name="テスト物件",
            year_month="2026-01",
            total_units=5,
            occupied_units=6,
            rent_revenue=300000,
            occupancy_rate=100.0,
        )


def test_missing_db_and_corrupted_null_logging(tmp_path: Path) -> None:
    """DB未存在時およびNULLデータ欠損時の例外キャッチと logs/app.log への構造化ログ出力検証"""
    log_file = tmp_path / "app.log"
    missing_db = tmp_path / "non_existent.duckdb"

    # 1. 存在しないDBファイルへの接続エラー検証
    with pytest.raises(DatabaseOperationError, match="存在しません"):
        fetch_monthly_rental_summary(RentalQueryFilter(db_path=missing_db), log_path=log_file)

    assert log_file.exists()
    log_lines = [json.loads(line) for line in log_file.read_text(encoding="utf-8").splitlines()]
    assert any(entry["event"] == "db_connection_error" and entry["level"] == "ERROR" for entry in log_lines)

    # 2. NULL欠損データ混入時の検知と構造化ログ出力検証
    corrupt_db = tmp_path / "corrupt.duckdb"
    with duckdb.connect(str(corrupt_db)) as conn:
        conn.execute(
            """
            CREATE TABLE rental_records (
                property_id VARCHAR,
                property_name VARCHAR,
                year_month VARCHAR,
                unit_number VARCHAR,
                is_occupied BOOLEAN,
                monthly_rent INTEGER
            )
            """
        )
        conn.execute(
            "INSERT INTO rental_records VALUES ('P001', NULL, '2026-01', '101', TRUE, 60000)"
        )

    with pytest.raises(DatabaseOperationError, match="データ欠損エラー"):
        fetch_monthly_rental_summary(RentalQueryFilter(db_path=corrupt_db), log_path=log_file)

    log_lines_after = [json.loads(line) for line in log_file.read_text(encoding="utf-8").splitlines()]
    assert any(entry["event"] == "data_missing_detected" and entry["level"] == "ERROR" for entry in log_lines_after)


def test_inspect_duckdb_and_sqlite_tables(tmp_path: Path) -> None:
    """第3タブ用: DuckDB / SQLite 生データ閲覧・キーワード検索・機密マスキング・異常系ログの検証"""
    import sqlite3

    duck_file = tmp_path / "rental_data.duckdb"
    sqlite_file = tmp_path / "property_management.db"
    log_file = tmp_path / "app.log"

    # 1. DuckDB 閲覧とキーワード検索
    initialize_sample_duckdb(db_path=duck_file, force_recreate=True, log_path=log_file)
    all_duck = fetch_duckdb_rental_records(
        TableInspectFilter(source_type="duckdb_rental_records", db_path=duck_file),
        log_path=log_file,
    )
    assert len(all_duck) == 360

    filtered_duck = fetch_duckdb_rental_records(
        TableInspectFilter(
            source_type="duckdb_rental_records",
            db_path=duck_file,
            keyword="北18条",
        ),
        log_path=log_file,
    )
    assert len(filtered_duck) == 120
    assert all(r.property_name == "北18条レジデンス" for r in filtered_duck)

    # 2. SQLite 閲覧・キーワード検索・電話番号マスキング検証
    conn = sqlite3.connect(str(sqlite_file))
    conn.execute(
        """
        CREATE TABLE contracts (
            contract_id TEXT PRIMARY KEY,
            property_id TEXT,
            property_name TEXT,
            room_number TEXT,
            tenant_name TEXT,
            current_rent INTEGER,
            new_rent INTEGER,
            renewal_date TEXT,
            contact TEXT,
            flag TEXT,
            memo TEXT
        )
        """
    )
    conn.execute(
        "INSERT INTO contracts VALUES ('C-101', 'P-01', 'メゾン札幌北', '101', '鈴木 一郎', 50000, 52000, '2026-12-01', '090-1111-2222', 'ACTIVE', 'メモ')"
    )
    conn.execute(
        "INSERT INTO contracts VALUES ('C-102', 'P-02', 'コーポ大通東', '202', '佐藤 花子', 60000, 60000, '2026-10-01', '080-3333-4444', 'ACTIVE', 'メモ')"
    )
    conn.commit()
    conn.close()

    # マスクON（デフォルト）
    masked_contracts = fetch_sqlite_contracts(
        TableInspectFilter(
            source_type="sqlite_contracts",
            db_path=sqlite_file,
            keyword="鈴木",
            mask_sensitive=True,
        ),
        log_path=log_file,
    )
    assert len(masked_contracts) == 1
    assert isinstance(masked_contracts[0], ContractMasterRecord)
    assert masked_contracts[0].contact == "090-****-2222"

    # マスクOFF
    unmasked_contracts = fetch_sqlite_contracts(
        TableInspectFilter(
            source_type="sqlite_contracts",
            db_path=sqlite_file,
            keyword="鈴木",
            mask_sensitive=False,
        ),
        log_path=log_file,
    )
    assert unmasked_contracts[0].contact == "090-1111-2222"

    # 3. 異常系（存在しないSQLiteパス・テーブル欠損）の検証
    with pytest.raises(DatabaseOperationError, match="存在しません"):
        fetch_sqlite_contracts(
            TableInspectFilter(source_type="sqlite_contracts", db_path=tmp_path / "missing.db"),
            log_path=log_file,
        )

    log_entries = [json.loads(line) for line in log_file.read_text(encoding="utf-8").splitlines()]
    assert any(e["event"] == "inspect_sqlite_missing" and e["level"] == "ERROR" for e in log_entries)
