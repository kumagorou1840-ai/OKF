#!/usr/bin/env python3
"""
tests/test_etl.py
`src/etl_sync.py` の単体テストスイート。
- 正常系（SQLite `mode=ro` 抽出 -> Pydantic検証 -> DuckDB投入、更新月前後の家賃切替、空室判定）
- 異常系（SQLite未存在、contractsテーブル未存在、不正・欠損データのスキップと構造化ログ出力）
- 冪等性（複数回重複実行してもDuckDB側の件数・集計結果が完全に一致すること）
"""

from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.db import (
    DatabaseOperationError,
    RentalQueryFilter,
    fetch_monthly_rental_summary,
    fetch_property_vacancy_loss,
)
from src.etl_sync import sync_sqlite_to_duckdb


def _create_test_sqlite(sqlite_path: Path, include_invalid: bool = False) -> None:
    """テスト用のSQLite `contracts` テーブルを作成するヘルパー"""
    conn = sqlite3.connect(str(sqlite_path))
    cur = conn.cursor()
    cur.execute(
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
    rows = [
        # 2026-07から 55,000 -> 58,000 に更新される稼働中部屋
        ("C-01", "P-01", "メゾン札幌北", "101", "鈴木 一郎", 55000, 58000, "2026-07-01", "090-0000", "ACTIVE", ""),
        # 空室部屋（機会損失 54,000円/月）
        ("C-02", "P-01", "メゾン札幌北", "102", "", 54000, 54000, "2026-01-01", "", "VACANT", "空室"),
    ]
    if include_invalid:
        rows.extend(
            [
                # 不正データ1: マイナスの家賃（Pydantic RentalRecordInput ge=0 違反）
                ("C-BAD1", "P-01", "メゾン札幌北", "103", "佐藤", -10000, -10000, "2026-01-01", "", "ACTIVE", ""),
                # 不正データ2: 物件名がNULL（必須欠損）
                ("C-BAD2", "P-02", None, "201", "田中", 60000, 60000, "2026-01-01", "", "ACTIVE", ""),
            ]
        )

    cur.executemany(
        "INSERT INTO contracts VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        rows,
    )
    conn.commit()
    conn.close()


def test_etl_normal_and_idempotency(tmp_path: Path) -> None:
    """正常系同期・更新月前後の家賃切替・および重複実行時の冪等性（DELETE + INSERT）検証"""
    sqlite_file = tmp_path / "test_prop.db"
    duckdb_file = tmp_path / "rental_data.duckdb"
    log_file = tmp_path / "app.log"

    _create_test_sqlite(sqlite_file, include_invalid=False)
    target_months = ["2026-06", "2026-07"]

    # 1回目の実行
    res1 = sync_sqlite_to_duckdb(
        sqlite_path=sqlite_file,
        duckdb_path=duckdb_file,
        target_months=target_months,
        log_path=log_file,
    )
    assert res1.extracted_contracts == 2
    assert res1.inserted_records == 4  # 2契約 × 2ヶ月
    assert res1.skipped_records == 0

    # 2回目・3回目の重複実行（冪等性の検証：件数が8件や12件に増えず4件のままであること）
    res2 = sync_sqlite_to_duckdb(
        sqlite_path=sqlite_file,
        duckdb_path=duckdb_file,
        target_months=target_months,
        log_path=log_file,
    )
    assert res2.inserted_records == 4

    summaries = fetch_monthly_rental_summary(
        RentalQueryFilter(db_path=duckdb_file),
        log_path=log_file,
    )
    assert len(summaries) == 2  # 1物件 × 2ヶ月

    june = next(s for s in summaries if s.year_month == "2026-06")
    july = next(s for s in summaries if s.year_month == "2026-07")

    # 6月は旧家賃 55,000円、7月は更新後新家賃 58,000円、空室損失はいずれも 54,000円
    assert june.rent_revenue == 55000
    assert june.vacancy_loss == 54000
    assert june.occupancy_rate == 50.0

    assert july.rent_revenue == 58000
    assert july.vacancy_loss == 54000
    assert july.occupancy_rate == 50.0

    losses = fetch_property_vacancy_loss(
        RentalQueryFilter(db_path=duckdb_file),
        log_path=log_file,
    )
    assert len(losses) == 1
    assert losses[0].total_vacancy_loss == 108000  # 54,000 × 2ヶ月


def test_etl_skips_invalid_records_and_logs(tmp_path: Path) -> None:
    """不正データ・欠損値混入時に該当レコードをスキップし、logs/app.log に構造化警告を残す検証"""
    sqlite_file = tmp_path / "test_invalid.db"
    duckdb_file = tmp_path / "rental_data.duckdb"
    log_file = tmp_path / "app.log"

    _create_test_sqlite(sqlite_file, include_invalid=True)

    res = sync_sqlite_to_duckdb(
        sqlite_path=sqlite_file,
        duckdb_path=duckdb_file,
        target_months=["2026-01", "2026-02"],
        log_path=log_file,
    )

    assert res.extracted_contracts == 4
    assert res.skipped_records == 2  # C-BAD1 と C-BAD2 の2件がスキップされる
    assert res.inserted_records == 4  # 正常な2契約 × 2ヶ月 = 4件のみ投入

    log_entries = [json.loads(line) for line in log_file.read_text(encoding="utf-8").splitlines()]
    events = {entry["event"] for entry in log_entries}
    assert "etl_record_skipped_null" in events
    assert "etl_record_validation_failed" in events
    assert "etl_sync_completed" in events


def test_etl_missing_sqlite_raises_and_logs(tmp_path: Path) -> None:
    """SQLiteファイルが存在しない場合の例外送出とエラーログ出力検証"""
    missing_sqlite = tmp_path / "no_such.db"
    duckdb_file = tmp_path / "rental_data.duckdb"
    log_file = tmp_path / "app.log"

    with pytest.raises(DatabaseOperationError, match="存在しません"):
        sync_sqlite_to_duckdb(
            sqlite_path=missing_sqlite,
            duckdb_path=duckdb_file,
            log_path=log_file,
        )

    log_entries = [json.loads(line) for line in log_file.read_text(encoding="utf-8").splitlines()]
    assert any(e["event"] == "etl_sqlite_missing" and e["level"] == "ERROR" for e in log_entries)
