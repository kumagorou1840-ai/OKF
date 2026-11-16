#!/usr/bin/env python3
"""
src/etl_sync.py
SQLite (`property_management.db`) から賃貸契約・家賃データを読み取り専用（URI `mode=ro`）で抽出し、
Pydantic v2 (`RentalRecordInput`) で全件バリデーションした上で、
DuckDB (`data/rental_data.duckdb`) の `rental_records` テーブルへ冪等同期（DELETE + INSERT）するETLスクリプト。
"""

from __future__ import annotations

import hashlib
import sqlite3
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

import duckdb
from pydantic import BaseModel, Field, ValidationError

# プロジェクトルートを sys.path に追加（CLI直接実行対応）
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.db import (
    DEFAULT_DB_PATH,
    LOG_FILE_PATH,
    DatabaseOperationError,
    RentalRecordInput,
    log_structured_event,
)

DEFAULT_SQLITE_PATH = PROJECT_ROOT / "property_management.db"
DEFAULT_TARGET_MONTHS = [f"2026-{m:02d}" for m in range(1, 13)]


class ETLSyncResult(BaseModel):
    """ETL同期処理の実行結果サマリーモデル"""

    sqlite_path: str = Field(..., description="抽出元SQLiteパス")
    duckdb_path: str = Field(..., description="同期先DuckDBパス")
    extracted_contracts: int = Field(..., ge=0, description="SQLiteから抽出した契約行件数")
    inserted_records: int = Field(..., ge=0, description="DuckDBへ投入した月次展開レコード件数")
    skipped_records: int = Field(..., ge=0, description="バリデーションエラー・欠損によりスキップした件数")


def _derive_property_id(raw_prop_id: Optional[str], property_name: Optional[str]) -> str:
    """property_id が未設定の場合に property_name から決定論的にIDを生成する"""
    if raw_prop_id and str(raw_prop_id).strip():
        return str(raw_prop_id).strip()
    if property_name and str(property_name).strip():
        digest = hashlib.md5(str(property_name).strip().encode("utf-8")).hexdigest()[:4].upper()
        return f"P-{digest}"
    return ""


def _determine_is_occupied(flag: Optional[str], tenant_name: Optional[str]) -> bool:
    """契約フラグと入居者名から稼働状態（True: 入居中 / False: 空室）を判定する"""
    flag_upper = (str(flag).strip().upper() if flag is not None else "")
    if flag_upper in {"VACANT", "EMPTY", "空室", "退去済"}:
        return False
    if tenant_name is not None and str(tenant_name).strip() == "" and flag_upper == "":
        return False
    return True


def _extract_renewal_month(renewal_date: Optional[str]) -> str:
    """renewal_date ('YYYY-MM-DD' または 'YYYY-MM') から 'YYYY-MM' を抽出する"""
    if not renewal_date:
        return "9999-12"
    text = str(renewal_date).strip()
    if len(text) >= 7 and text[4] == "-":
        return text[:7]
    return "9999-12"


def sync_sqlite_to_duckdb(
    sqlite_path: Path = DEFAULT_SQLITE_PATH,
    duckdb_path: Path = DEFAULT_DB_PATH,
    target_months: Optional[Sequence[str]] = None,
    log_path: Path = LOG_FILE_PATH,
) -> ETLSyncResult:
    """
    SQLite (`mode=ro`) から契約データを抽出し、Pydantic v2 (`RentalRecordInput`) で検証の上、
    DuckDB (`rental_records`) へトランザクション制御（DELETE + INSERT）で冪等同期する。
    """
    months = list(target_months) if target_months is not None else list(DEFAULT_TARGET_MONTHS)

    if not sqlite_path.exists():
        log_structured_event(
            level="ERROR",
            event="etl_sqlite_missing",
            message=f"抽出元のSQLiteファイルが存在しません: {sqlite_path}",
            details={"sqlite_path": str(sqlite_path)},
            log_path=log_path,
        )
        raise DatabaseOperationError(f"抽出元SQLiteファイルが存在しません: {sqlite_path}")

    # 1. SQLite から読み取り専用 (URI mode=ro) でデータ抽出
    sqlite_uri = f"file:{sqlite_path.resolve().as_posix()}?mode=ro"
    raw_contracts: List[Dict[str, Any]] = []

    try:
        conn_sq = sqlite3.connect(sqlite_uri, uri=True)
        conn_sq.row_factory = sqlite3.Row
        try:
            cur = conn_sq.cursor()
            table_check = cur.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='contracts'"
            ).fetchone()
            if not table_check:
                log_structured_event(
                    level="ERROR",
                    event="etl_contracts_table_missing",
                    message="SQLite内に contracts テーブルが存在しません。",
                    details={"sqlite_path": str(sqlite_path)},
                    log_path=log_path,
                )
                raise DatabaseOperationError("SQLite内に contracts テーブルが存在しません。")

            rows = cur.execute("SELECT * FROM contracts ORDER BY contract_id").fetchall()
            raw_contracts = [dict(r) for r in rows]
        finally:
            conn_sq.close()
    except DatabaseOperationError:
        raise
    except Exception as exc:
        log_structured_event(
            level="ERROR",
            event="etl_sqlite_read_error",
            message=f"SQLite読み取り中にエラーが発生しました: {exc}",
            details={"sqlite_path": str(sqlite_path), "error_type": type(exc).__name__},
            log_path=log_path,
        )
        raise DatabaseOperationError(f"SQLite読み取りエラー: {exc}") from exc

    # 2. 変換 & Pydantic v2 (`RentalRecordInput`) 全件バリデーション
    valid_records: List[RentalRecordInput] = []
    skipped_count = 0

    for contract in raw_contracts:
        contract_id = contract.get("contract_id", "UNKNOWN")
        prop_name = contract.get("property_name")
        prop_id = _derive_property_id(contract.get("property_id"), prop_name)
        room_no = contract.get("room_number")
        current_rent = contract.get("current_rent")
        new_rent = contract.get("new_rent")
        renewal_ym = _extract_renewal_month(contract.get("renewal_date"))
        is_occupied = _determine_is_occupied(contract.get("flag"), contract.get("tenant_name"))

        # 必須フィールドの事前欠損チェック（契約単位で1回判定し、不正ならスキップ）
        if (
            prop_name is None
            or room_no is None
            or current_rent is None
            or new_rent is None
        ):
            skipped_count += 1
            log_structured_event(
                level="WARNING",
                event="etl_record_skipped_null",
                message=f"契約レコードに必須カラムの欠損(NULL)があるためスキップしました: {contract_id}",
                details={"contract_id": contract_id, "raw_contract": contract},
                log_path=log_path,
            )
            continue

        contract_valid_for_months: List[RentalRecordInput] = []
        contract_failed = False

        for ym in months:
            applied_rent = new_rent if ym >= renewal_ym else current_rent
            try:
                rec = RentalRecordInput(
                    property_id=str(prop_id),
                    property_name=str(prop_name),
                    year_month=ym,
                    unit_number=str(room_no),
                    is_occupied=is_occupied,
                    monthly_rent=applied_rent,
                )
                contract_valid_for_months.append(rec)
            except ValidationError as val_exc:
                contract_failed = True
                skipped_count += 1
                log_structured_event(
                    level="WARNING",
                    event="etl_record_validation_failed",
                    message=f"Pydantic v2 バリデーションエラーのため契約レコードをスキップしました: {contract_id}",
                    details={
                        "contract_id": contract_id,
                        "year_month": ym,
                        "errors": val_exc.errors(),
                    },
                    log_path=log_path,
                )
                break

        if not contract_failed:
            valid_records.extend(contract_valid_for_months)

    # 3. DuckDB への冪等ロード（トランザクション制御: DELETE + INSERT）
    try:
        duckdb_path.parent.mkdir(parents=True, exist_ok=True)
        with duckdb.connect(str(duckdb_path)) as conn_duck:
            conn_duck.execute(
                """
                CREATE TABLE IF NOT EXISTS rental_records (
                    property_id VARCHAR NOT NULL,
                    property_name VARCHAR NOT NULL,
                    year_month VARCHAR NOT NULL,
                    unit_number VARCHAR NOT NULL,
                    is_occupied BOOLEAN NOT NULL,
                    monthly_rent INTEGER NOT NULL
                )
                """
            )

            conn_duck.execute("BEGIN TRANSACTION")
            try:
                if months:
                    placeholders = ", ".join(["?"] * len(months))
                    conn_duck.execute(
                        f"DELETE FROM rental_records WHERE year_month IN ({placeholders})",
                        months,
                    )
                else:
                    conn_duck.execute("DELETE FROM rental_records")

                if valid_records:
                    insert_tuples = [
                        (
                            r.property_id,
                            r.property_name,
                            r.year_month,
                            r.unit_number,
                            r.is_occupied,
                            r.monthly_rent,
                        )
                        for r in valid_records
                    ]
                    conn_duck.executemany(
                        """
                        INSERT INTO rental_records (
                            property_id, property_name, year_month, unit_number, is_occupied, monthly_rent
                        ) VALUES (?, ?, ?, ?, ?, ?)
                        """,
                        insert_tuples,
                    )
                conn_duck.execute("COMMIT")
            except Exception:
                conn_duck.execute("ROLLBACK")
                raise

    except Exception as exc:
        log_structured_event(
            level="ERROR",
            event="etl_duckdb_load_error",
            message=f"DuckDBへのロード中にエラーが発生しました: {exc}",
            details={"duckdb_path": str(duckdb_path), "error_type": type(exc).__name__},
            log_path=log_path,
        )
        raise DatabaseOperationError(f"DuckDBロードエラー: {exc}") from exc

    result = ETLSyncResult(
        sqlite_path=str(sqlite_path),
        duckdb_path=str(duckdb_path),
        extracted_contracts=len(raw_contracts),
        inserted_records=len(valid_records),
        skipped_records=skipped_count,
    )

    log_structured_event(
        level="INFO",
        event="etl_sync_completed",
        message="SQLiteからDuckDBへのETL同期が正常に完了しました。",
        details=result.model_dump(),
        log_path=log_path,
    )
    return result


def main() -> int:
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")

    res = sync_sqlite_to_duckdb()
    print("=" * 68)
    print("[OK] SQLite -> DuckDB ETL Sync Completed")
    print("=" * 68)
    print(f"  - Source SQLite    : {res.sqlite_path} (mode=ro)")
    print(f"  - Target DuckDB    : {res.duckdb_path}")
    print(f"  - Extracted Rows   : {res.extracted_contracts}")
    print(f"  - Inserted Records : {res.inserted_records} (12 months)")
    print(f"  - Skipped Records  : {res.skipped_records}")
    print("=" * 68)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
