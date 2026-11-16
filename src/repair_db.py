#!/usr/bin/env python3
"""
src/repair_db.py
DuckDB (data/rental_data.duckdb) の `repair_records` テーブルに対する
サンプル修繕データ初期化および物件別・月別の修繕費集計を行うモジュール（Agent A 設計実装）。
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, List

import duckdb
from pydantic import ValidationError

from src.db import (
    DEFAULT_DB_PATH,
    LOG_FILE_PATH,
    DatabaseOperationError,
    RentalQueryFilter,
    log_structured_event,
)
from src.models_finance import MonthlyRepairSummary, RepairExpenseInput


def initialize_sample_repairs(
    db_path: Path = DEFAULT_DB_PATH,
    force_recreate: bool = False,
    log_path: Path = LOG_FILE_PATH,
) -> Path:
    """
    DuckDB (`db_path`) に `repair_records` テーブルを作成し、
    レコードが0件（または `force_recreate=True`）の場合に2026年のサンプル修繕データを投入する。
    """
    try:
        db_path.parent.mkdir(parents=True, exist_ok=True)
        with duckdb.connect(str(db_path)) as conn:
            if force_recreate:
                conn.execute("DROP TABLE IF EXISTS repair_records")

            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS repair_records (
                    property_id VARCHAR NOT NULL,
                    property_name VARCHAR NOT NULL,
                    year_month VARCHAR NOT NULL,
                    category VARCHAR NOT NULL,
                    repair_cost INTEGER NOT NULL,
                    description VARCHAR
                )
                """
            )

            existing_count = conn.execute("SELECT COUNT(*) FROM repair_records").fetchone()[0]
            if existing_count > 0 and not force_recreate:
                log_structured_event(
                    "INFO",
                    "repair_db_initialized",
                    "既存の repair_records テーブルを使用します。",
                    details={"db_path": str(db_path), "existing_rows": int(existing_count)},
                    log_path=log_path,
                )
                return db_path

            raw_samples = [
                ("P001", "北18条レジデンス", "2026-01", "水抜き栓・配管", 35_000, "102号室 水抜き栓不良に伴うパッキン・スピンドル交換"),
                ("P001", "北18条レジデンス", "2026-03", "原状回復", 120_000, "105号室 退去に伴うクロス張替え・ハウスクリーニング"),
                ("P001", "北18条レジデンス", "2026-08", "給湯器・設備", 185_000, "108号室 ガス給湯器（FF式）本体交換"),
                ("P002", "大通パークサイドコート", "2026-02", "共用部・除雪設備", 65_000, "エントランス風除室ドアクローザー修繕・融雪マット点検"),
                ("P002", "大通パークサイドコート", "2026-04", "原状回復", 145_000, "203号室 退去原状回復（CF・壁紙全面貼替）"),
                ("P002", "大通パークサイドコート", "2026-09", "給湯器・設備", 92_000, "301号室 エアコン・換気扇交換工事"),
                ("P003", "円山グリーンハイツ", "2026-01", "水抜き栓・配管", 48_000, "101号室 凍結による給水管一部補修および水抜き栓修繕"),
                ("P003", "円山グリーンハイツ", "2026-06", "原状回復", 110_000, "202号室 退去時クロス原状回復・畳表替え"),
                ("P004", "メゾン札幌北", "2026-02", "給湯器・設備", 178_000, "103号室 給湯器交換工事（追い焚き付）"),
                ("P004", "メゾン札幌北", "2026-05", "原状回復", 95_000, "201号室 クロス原状回復・床ワックス剥離清掃"),
                ("P005", "コーポ大通東", "2026-03", "原状回復", 132_000, "104号室 退去原状回復・キッチン水栓シングルレバー化"),
                ("P005", "コーポ大通東", "2026-10", "水抜き栓・配管", 42_000, "冬季前の水抜き栓一斉点検・不良箇所修繕"),
            ]

            validated_rows: List[tuple] = []
            for prop_id, prop_name, ym, category, cost, desc in raw_samples:
                rec = RepairExpenseInput(
                    property_id=prop_id,
                    property_name=prop_name,
                    year_month=ym,
                    category=category,
                    repair_cost=cost,
                    description=desc,
                )
                validated_rows.append(
                    (
                        rec.property_id,
                        rec.property_name,
                        rec.year_month,
                        rec.category,
                        rec.repair_cost,
                        rec.description,
                    )
                )

            conn.executemany(
                """
                INSERT INTO repair_records (
                    property_id, property_name, year_month, category, repair_cost, description
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                validated_rows,
            )

        log_structured_event(
            "INFO",
            "repair_db_initialized",
            "DuckDB repair_records サンプルデータの初期化が完了しました。",
            details={"db_path": str(db_path), "inserted_rows": len(validated_rows)},
            log_path=log_path,
        )
        return db_path

    except Exception as exc:
        log_structured_event(
            "ERROR",
            "repair_db_init_error",
            f"repair_records 初期化中にエラーが発生しました: {exc}",
            details={"db_path": str(db_path), "error_type": type(exc).__name__},
            log_path=log_path,
        )
        raise DatabaseOperationError(f"修繕DB初期化エラー: {exc}") from exc


def fetch_monthly_repair_summary(
    query_filter: RentalQueryFilter,
    log_path: Path = LOG_FILE_PATH,
) -> List[MonthlyRepairSummary]:
    """
    DuckDB (`repair_records`) から物件別・月別の修繕件数と修繕費合計を集計し、
    `MonthlyRepairSummary` のリストとして返す。
    """
    db_path = query_filter.db_path
    if not db_path.exists():
        log_structured_event(
            "ERROR",
            "repair_db_missing",
            f"指定されたDuckDBファイルが存在しません: {db_path}",
            details={"db_path": str(db_path)},
            log_path=log_path,
        )
        raise DatabaseOperationError(f"DuckDBファイルが存在しません: {db_path}")

    try:
        with duckdb.connect(str(db_path), read_only=True) as conn:
            table_check = conn.execute(
                "SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'repair_records'"
            ).fetchone()[0]
            if table_check == 0:
                log_structured_event(
                    "ERROR",
                    "repair_table_missing",
                    "DuckDB内に repair_records テーブルが存在しません。",
                    details={"db_path": str(db_path)},
                    log_path=log_path,
                )
                raise DatabaseOperationError("DuckDB内に repair_records テーブルが存在しません。")

            missing_check_sql = """
                SELECT COUNT(*)
                FROM repair_records
                WHERE property_name IS NULL
                   OR year_month IS NULL
                   OR repair_cost IS NULL
            """
            missing_count = conn.execute(missing_check_sql).fetchone()[0]
            if missing_count > 0:
                log_structured_event(
                    "ERROR",
                    "repair_data_missing_detected",
                    f"repair_records テーブルに {missing_count} 件の欠損（NULL）データが含まれています。",
                    details={"db_path": str(db_path), "missing_rows": int(missing_count)},
                    log_path=log_path,
                )
                raise DatabaseOperationError(
                    f"修繕データ欠損エラー: {missing_count} 件のNULLレコードが検出されました。"
                )

            where_clauses: List[str] = []
            params: List[Any] = []

            if query_filter.property_names:
                placeholders = ", ".join(["?"] * len(query_filter.property_names))
                where_clauses.append(f"property_name IN ({placeholders})")
                params.extend(query_filter.property_names)

            if query_filter.start_month:
                where_clauses.append("year_month >= ?")
                params.append(query_filter.start_month)

            if query_filter.end_month:
                where_clauses.append("year_month <= ?")
                params.append(query_filter.end_month)

            where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

            agg_sql = f"""
                SELECT
                    property_name,
                    year_month,
                    COUNT(*) AS repair_count,
                    COALESCE(SUM(repair_cost), 0) AS total_repair_cost
                FROM repair_records
                {where_sql}
                GROUP BY property_name, year_month
                ORDER BY year_month ASC, property_name ASC
            """

            raw_rows = conn.execute(agg_sql, params).fetchall()

            results: List[MonthlyRepairSummary] = [
                MonthlyRepairSummary(
                    property_name=str(row[0]),
                    year_month=str(row[1]),
                    repair_count=int(row[2]),
                    total_repair_cost=int(row[3]),
                )
                for row in raw_rows
            ]

            log_structured_event(
                "INFO",
                "repair_aggregation_success",
                "物件別・月別の修繕費集計が完了しました。",
                details={"record_count": len(results), "db_path": str(db_path)},
                log_path=log_path,
            )
            return results

    except DatabaseOperationError:
        raise
    except ValidationError as val_exc:
        log_structured_event(
            "ERROR",
            "repair_pydantic_validation_error",
            f"修繕費集計結果のPydantic型検証に失敗しました: {val_exc}",
            details={"db_path": str(db_path), "errors": val_exc.errors()},
            log_path=log_path,
        )
        raise DatabaseOperationError(f"修繕データ型検証エラー: {val_exc}") from val_exc
    except Exception as exc:
        log_structured_event(
            "ERROR",
            "repair_query_error",
            f"repair_records クエリ実行中にエラーが発生しました: {exc}",
            details={"db_path": str(db_path), "error_type": type(exc).__name__},
            log_path=log_path,
        )
        raise DatabaseOperationError(f"修繕クエリ実行エラー: {exc}") from exc
