#!/usr/bin/env python3
"""
src/db.py
DuckDB (data/rental_data.duckdb) から物件別・月別の家賃収入と稼働率を集計するデータベース処理モジュール。

要件:
1. DuckDBから物件別・月別の家賃収入と稼働率を集計するクエリを実装
2. 入出力のデータ構造は Pydantic v2 の BaseModel で厳密に型定義
3. DB接続エラーやデータ欠損時は例外をキャッチし、`logs/app.log` に構造化ログ（JSON形式）を出力
"""

from __future__ import annotations

import json
import logging
import re
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional, Sequence

import duckdb
from pydantic import BaseModel, Field, ValidationError, field_validator, model_validator

# プロジェクトルートとデフォルトパス設定
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DB_PATH = PROJECT_ROOT / "data" / "rental_data.duckdb"
DEFAULT_SQLITE_PATH = PROJECT_ROOT / "property_management.db"
LOG_FILE_PATH = PROJECT_ROOT / "logs" / "app.log"


# ============================================================================
# 1. 構造化ロガー設定 (`logs/app.log`)
# ============================================================================

def get_structured_logger(log_path: Path = LOG_FILE_PATH) -> logging.Logger:
    """`logs/app.log` に JSON 構造化ログを出力するロガーを取得する"""
    log_path.parent.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger(f"rental_dashboard.{log_path}")
    logger.setLevel(logging.INFO)

    # 重複ハンドラ防止
    target_path_str = str(log_path.resolve())
    has_handler = any(
        isinstance(h, logging.FileHandler) and getattr(h, "baseFilename", None) == target_path_str
        for h in logger.handlers
    )
    if not has_handler:
        file_handler = logging.FileHandler(target_path_str, encoding="utf-8")
        file_handler.setFormatter(logging.Formatter("%(message)s"))
        logger.addHandler(file_handler)

    return logger


def log_structured_event(
    level: str,
    event: str,
    message: str,
    details: Optional[Dict[str, Any]] = None,
    log_path: Path = LOG_FILE_PATH,
) -> None:
    """構造化ログ（JSON 1行形式）を `logs/app.log` に書き込む"""
    logger = get_structured_logger(log_path)
    payload = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "level": level.upper(),
        "event": event,
        "message": message,
        "details": details or {},
    }
    json_line = json.dumps(payload, ensure_ascii=False)
    if level.upper() == "ERROR":
        logger.error(json_line)
    elif level.upper() == "WARNING":
        logger.warning(json_line)
    else:
        logger.info(json_line)


# ============================================================================
# 2. Pydantic v2 スキーマ定義（入出力の厳密な型定義）
# ============================================================================

YEAR_MONTH_PATTERN = r"^\d{4}-(0[1-9]|1[0-2])$"


class RentalRecordInput(BaseModel):
    """DB格納・シード投入用の生データ入力スキーマ（部屋・月次単位または物件・月次単位）"""

    property_id: str = Field(..., min_length=1, description="物件ID")
    property_name: str = Field(..., min_length=1, description="物件名")
    year_month: str = Field(..., pattern=YEAR_MONTH_PATTERN, description="対象年月 (YYYY-MM)")
    unit_number: str = Field(..., min_length=1, description="部屋番号")
    is_occupied: bool = Field(..., description="稼働状態（True: 入居中 / False: 空室）")
    monthly_rent: int = Field(..., ge=0, description="月額家賃（円・空室時も契約想定賃料または0）")

    @field_validator("property_id", "property_name", "unit_number")
    @classmethod
    def validate_non_empty(cls, v: str) -> str:
        cleaned = v.strip()
        if not cleaned:
            raise ValueError("空白のみの文字列は許可されません。")
        return cleaned


class RentalQueryFilter(BaseModel):
    """集計クエリ用の入力フィルターモデル"""

    db_path: Path = Field(default=DEFAULT_DB_PATH, description="DuckDBファイルパス")
    property_names: Optional[List[str]] = Field(
        default=None, description="フィルタ対象の物件名リスト（Noneまたは空リストの場合は全物件）"
    )
    start_month: Optional[str] = Field(
        default=None, pattern=YEAR_MONTH_PATTERN, description="開始年月 (YYYY-MM)"
    )
    end_month: Optional[str] = Field(
        default=None, pattern=YEAR_MONTH_PATTERN, description="終了年月 (YYYY-MM)"
    )

    @model_validator(mode="after")
    def check_month_order(self) -> "RentalQueryFilter":
        if self.start_month and self.end_month and self.start_month > self.end_month:
            raise ValueError(
                f"start_month ({self.start_month}) は end_month ({self.end_month}) 以下である必要があります。"
            )
        return self


class MonthlyRentalSummary(BaseModel):
    """物件別・月別の集計結果出力スキーマ"""

    property_name: str = Field(..., min_length=1, description="物件名")
    year_month: str = Field(..., pattern=YEAR_MONTH_PATTERN, description="対象年月 (YYYY-MM)")
    total_units: int = Field(..., gt=0, description="総戸数")
    occupied_units: int = Field(..., ge=0, description="稼働戸数")
    vacant_units: int = Field(default=0, ge=0, description="空室戸数")
    rent_revenue: int = Field(..., ge=0, description="月間家賃収入合計（円）")
    vacancy_loss: int = Field(default=0, ge=0, description="月間空室損失額・機会損失合計（円）")
    occupancy_rate: float = Field(..., ge=0.0, le=100.0, description="稼働率（%：0.0〜100.0）")

    @model_validator(mode="after")
    def validate_units_consistency(self) -> "MonthlyRentalSummary":
        if self.occupied_units > self.total_units:
            raise ValueError(
                f"稼働戸数 ({self.occupied_units}) が総戸数 ({self.total_units}) を超えています。"
            )
        return self


class PropertyVacancyLossSummary(BaseModel):
    """物件別の空室損失額（機会損失）集計スキーマ"""

    property_name: str = Field(..., min_length=1, description="物件名")
    total_vacant_unit_months: int = Field(..., ge=0, description="期間内の延べ空室戸月数")
    total_vacancy_loss: int = Field(..., ge=0, description="期間内の空室損失額合計（円）")
    potential_revenue: int = Field(..., ge=0, description="満室想定家賃収入合計（円）")
    loss_rate: float = Field(..., ge=0.0, le=100.0, description="機会損失率（%：0.0〜100.0）")


class TableInspectFilter(BaseModel):
    """DBテーブル閲覧・検索用の入力フィルタスキーマ"""

    source_type: Literal["duckdb_rental_records", "sqlite_contracts"] = Field(
        ..., description="取得対象のDB・テーブル種別"
    )
    db_path: Path = Field(..., description="対象DBファイルパス")
    keyword: Optional[str] = Field(default=None, description="部分一致検索キーワード（物件名・部屋番号・入居者名等）")
    mask_sensitive: bool = Field(default=True, description="連絡先等の機密情報をマスキングするかどうか")


class ContractMasterRecord(BaseModel):
    """SQLite `contracts` テーブルの生データ閲覧用Pydanticスキーマ"""

    contract_id: str = Field(..., min_length=1, description="契約ID")
    property_id: str = Field(..., min_length=1, description="物件ID")
    property_name: str = Field(..., min_length=1, description="物件名")
    room_number: str = Field(..., min_length=1, description="部屋番号")
    tenant_name: str = Field(default="", description="入居者名")
    current_rent: int = Field(..., ge=0, description="現家賃（円）")
    new_rent: int = Field(..., ge=0, description="新家賃（円）")
    renewal_date: str = Field(default="", description="契約更新日")
    contact: str = Field(default="", description="連絡先電話番号")
    flag: str = Field(default="ACTIVE", description="ステータスフラグ")
    memo: str = Field(default="", description="備考メモ")


# ============================================================================
# 3. データベース初期化・シード生成 & 集計クエリ実装
# ============================================================================

class DatabaseOperationError(RuntimeError):
    """DB接続失敗・テーブル欠損・データ欠損時のカスタム例外"""


def initialize_sample_duckdb(
    db_path: Path = DEFAULT_DB_PATH,
    force_recreate: bool = False,
    log_path: Path = LOG_FILE_PATH,
) -> Path:
    """`data/rental_data.duckdb` が存在しない（または空の）場合に札幌3物件×12ヶ月のサンプルデータを構築する"""
    try:
        db_path.parent.mkdir(parents=True, exist_ok=True)
        with duckdb.connect(str(db_path)) as conn:
            if force_recreate:
                conn.execute("DROP TABLE IF EXISTS rental_records")

            conn.execute(
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

            existing_count = conn.execute("SELECT COUNT(*) FROM rental_records").fetchone()[0]
            if existing_count > 0 and not force_recreate:
                return db_path

            # 札幌市内の3物件 × 2026年1月〜12月（12ヶ月）のシードデータ
            properties = [
                ("P001", "北18条レジデンス", 10, 58000, [9, 9, 10, 10, 10, 10, 9, 9, 10, 10, 10, 10]),
                ("P002", "大通パークサイドコート", 12, 75000, [10, 11, 12, 12, 11, 11, 11, 10, 11, 12, 12, 12]),
                ("P003", "円山グリーンハイツ", 8, 64000, [7, 7, 8, 8, 8, 7, 7, 7, 8, 8, 8, 8]),
            ]
            months = [f"2026-{m:02d}" for m in range(1, 13)]

            validated_rows: List[tuple] = []
            for prop_id, prop_name, total_u, base_rent, occ_list in properties:
                for m_idx, ym in enumerate(months):
                    occ_count = occ_list[m_idx]
                    for u_idx in range(1, total_u + 1):
                        is_occ = u_idx <= occ_count
                        # 空室時も各部屋の本来の募集家賃（想定賃料）を保持し、機会損失を算出可能にする
                        unit_rent = base_rent + (u_idx % 3) * 2000
                        rec = RentalRecordInput(
                            property_id=prop_id,
                            property_name=prop_name,
                            year_month=ym,
                            unit_number=f"{100 + u_idx}",
                            is_occupied=is_occ,
                            monthly_rent=unit_rent,
                        )
                        validated_rows.append(
                            (
                                rec.property_id,
                                rec.property_name,
                                rec.year_month,
                                rec.unit_number,
                                rec.is_occupied,
                                rec.monthly_rent,
                            )
                        )

            conn.executemany(
                """
                INSERT INTO rental_records (
                    property_id, property_name, year_month, unit_number, is_occupied, monthly_rent
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                validated_rows,
            )

        log_structured_event(
            level="INFO",
            event="db_initialized",
            message="DuckDBサンプルデータの初期化が完了しました。",
            details={"db_path": str(db_path), "inserted_rows": len(validated_rows)},
            log_path=log_path,
        )
        return db_path

    except Exception as exc:
        log_structured_event(
            level="ERROR",
            event="db_init_error",
            message=f"DuckDB初期化中にエラーが発生しました: {exc}",
            details={"db_path": str(db_path), "error_type": type(exc).__name__},
            log_path=log_path,
        )
        raise DatabaseOperationError(f"DuckDB初期化エラー: {exc}") from exc


def list_property_names(
    db_path: Path = DEFAULT_DB_PATH,
    log_path: Path = LOG_FILE_PATH,
) -> List[str]:
    """DB内のユニークな物件名一覧を取得する"""
    if not db_path.exists():
        log_structured_event(
            level="ERROR",
            event="db_file_missing",
            message=f"DuckDBファイルが存在しません: {db_path}",
            details={"db_path": str(db_path)},
            log_path=log_path,
        )
        raise DatabaseOperationError(f"DuckDBファイルが存在しません: {db_path}")

    try:
        with duckdb.connect(str(db_path), read_only=True) as conn:
            rows = conn.execute(
                """
                SELECT DISTINCT property_name
                FROM rental_records
                WHERE property_name IS NOT NULL
                ORDER BY property_name
                """
            ).fetchall()
            return [r[0] for r in rows]
    except Exception as exc:
        log_structured_event(
            level="ERROR",
            event="db_list_properties_error",
            message=f"物件一覧取得中にエラーが発生しました: {exc}",
            details={"db_path": str(db_path), "error_type": type(exc).__name__},
            log_path=log_path,
        )
        raise DatabaseOperationError(f"物件一覧取得エラー: {exc}") from exc


def fetch_monthly_rental_summary(
    query_filter: RentalQueryFilter,
    log_path: Path = LOG_FILE_PATH,
) -> List[MonthlyRentalSummary]:
    """
    DuckDBから物件別・月別の家賃収入と稼働率を集計し、Pydantic v2 モデルリストとして返す。
    DB接続エラーやデータ欠損（NULL混入・0件等）時は構造化ログを出力して例外を送出する。
    """
    db_path = query_filter.db_path
    if not db_path.exists():
        log_structured_event(
            level="ERROR",
            event="db_connection_error",
            message=f"指定されたDuckDBファイルが存在しません: {db_path}",
            details={"db_path": str(db_path)},
            log_path=log_path,
        )
        raise DatabaseOperationError(f"DuckDBファイルが存在しません: {db_path}")

    try:
        with duckdb.connect(str(db_path), read_only=True) as conn:
            # 1. 欠損値（NULL）レコードのチェックとログ記録
            missing_check_sql = """
                SELECT COUNT(*)
                FROM rental_records
                WHERE property_name IS NULL
                   OR year_month IS NULL
                   OR is_occupied IS NULL
                   OR monthly_rent IS NULL
            """
            missing_count = conn.execute(missing_check_sql).fetchone()[0]
            if missing_count > 0:
                log_structured_event(
                    level="ERROR",
                    event="data_missing_detected",
                    message=f"rental_records テーブルに {missing_count} 件の欠損（NULL）データが含まれています。",
                    details={"db_path": str(db_path), "missing_rows": int(missing_count)},
                    log_path=log_path,
                )
                raise DatabaseOperationError(
                    f"データ欠損エラー: {missing_count} 件のNULLレコードが検出されました。"
                )

            # 2. フィルタ条件の組み立て
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
                    COUNT(*) AS total_units,
                    SUM(CASE WHEN is_occupied THEN 1 ELSE 0 END) AS occupied_units,
                    SUM(CASE WHEN NOT is_occupied THEN 1 ELSE 0 END) AS vacant_units,
                    COALESCE(SUM(CASE WHEN is_occupied THEN monthly_rent ELSE 0 END), 0) AS rent_revenue,
                    COALESCE(SUM(CASE WHEN NOT is_occupied THEN monthly_rent ELSE 0 END), 0) AS vacancy_loss,
                    ROUND(
                        SUM(CASE WHEN is_occupied THEN 1.0 ELSE 0.0 END) * 100.0 / NULLIF(COUNT(*), 0),
                        2
                    ) AS occupancy_rate
                FROM rental_records
                {where_sql}
                GROUP BY property_name, year_month
                ORDER BY year_month ASC, property_name ASC
            """

            raw_rows = conn.execute(agg_sql, params).fetchall()

            if not raw_rows:
                log_structured_event(
                    level="WARNING",
                    event="empty_aggregation_result",
                    message="指定された条件に一致する集計データが0件でした。",
                    details={
                        "db_path": str(db_path),
                        "property_names": query_filter.property_names,
                        "start_month": query_filter.start_month,
                        "end_month": query_filter.end_month,
                    },
                    log_path=log_path,
                )
                return []

            results: List[MonthlyRentalSummary] = []
            for row in raw_rows:
                summary = MonthlyRentalSummary(
                    property_name=str(row[0]),
                    year_month=str(row[1]),
                    total_units=int(row[2]),
                    occupied_units=int(row[3]),
                    vacant_units=int(row[4]),
                    rent_revenue=int(row[5]),
                    vacancy_loss=int(row[6]),
                    occupancy_rate=float(row[7]),
                )
                results.append(summary)

            log_structured_event(
                level="INFO",
                event="aggregation_success",
                message="物件別・月別の家賃収入および稼働率の集計が完了しました。",
                details={"record_count": len(results), "db_path": str(db_path)},
                log_path=log_path,
            )
            return results

    except DatabaseOperationError:
        raise
    except ValidationError as val_exc:
        log_structured_event(
            level="ERROR",
            event="pydantic_validation_error",
            message=f"集計結果のPydantic型検証に失敗しました: {val_exc}",
            details={"db_path": str(db_path), "errors": val_exc.errors()},
            log_path=log_path,
        )
        raise DatabaseOperationError(f"データ型検証エラー: {val_exc}") from val_exc
    except Exception as exc:
        log_structured_event(
            level="ERROR",
            event="db_query_error",
            message=f"DuckDBクエリ実行中にエラーが発生しました: {exc}",
            details={"db_path": str(db_path), "error_type": type(exc).__name__},
            log_path=log_path,
        )
        raise DatabaseOperationError(f"DuckDBクエリ実行エラー: {exc}") from exc


def fetch_property_vacancy_loss(
    query_filter: RentalQueryFilter,
    log_path: Path = LOG_FILE_PATH,
) -> List[PropertyVacancyLossSummary]:
    """
    DuckDBから物件別の空室損失額（機会損失: is_occupied = FALSE 時の想定家賃合計）を集計し、
    Pydantic v2 モデルリストとして返す。
    """
    db_path = query_filter.db_path
    if not db_path.exists():
        log_structured_event(
            level="ERROR",
            event="db_connection_error",
            message=f"指定されたDuckDBファイルが存在しません: {db_path}",
            details={"db_path": str(db_path)},
            log_path=log_path,
        )
        raise DatabaseOperationError(f"DuckDBファイルが存在しません: {db_path}")

    try:
        with duckdb.connect(str(db_path), read_only=True) as conn:
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

            loss_sql = f"""
                SELECT
                    property_name,
                    SUM(CASE WHEN NOT is_occupied THEN 1 ELSE 0 END) AS total_vacant_unit_months,
                    COALESCE(SUM(CASE WHEN NOT is_occupied THEN monthly_rent ELSE 0 END), 0) AS total_vacancy_loss,
                    COALESCE(SUM(monthly_rent), 0) AS potential_revenue,
                    ROUND(
                        COALESCE(SUM(CASE WHEN NOT is_occupied THEN monthly_rent ELSE 0 END), 0) * 100.0
                        / NULLIF(SUM(monthly_rent), 0),
                        2
                    ) AS loss_rate
                FROM rental_records
                {where_sql}
                GROUP BY property_name
                ORDER BY total_vacancy_loss DESC, property_name ASC
            """

            raw_rows = conn.execute(loss_sql, params).fetchall()
            results = [
                PropertyVacancyLossSummary(
                    property_name=str(row[0]),
                    total_vacant_unit_months=int(row[1]),
                    total_vacancy_loss=int(row[2]),
                    potential_revenue=int(row[3]),
                    loss_rate=float(row[4] or 0.0),
                )
                for row in raw_rows
            ]

            log_structured_event(
                level="INFO",
                event="vacancy_loss_aggregation_success",
                message="物件別の空室損失額（機会損失）の集計が完了しました。",
                details={"property_count": len(results), "db_path": str(db_path)},
                log_path=log_path,
            )
            return results

    except Exception as exc:
        log_structured_event(
            level="ERROR",
            event="vacancy_loss_query_error",
            message=f"空室損失額クエリ実行中にエラーが発生しました: {exc}",
            details={"db_path": str(db_path), "error_type": type(exc).__name__},
            log_path=log_path,
        )
        raise DatabaseOperationError(f"空室損失額クエリ実行エラー: {exc}") from exc


def _mask_phone_number(contact: str) -> str:
    """電話番号の中間桁をマスキングする（例: 090-1111-2222 -> 090-****-2222）"""
    if not contact:
        return ""
    return re.sub(r"(\d{2,4})-\d{2,4}-(\d{4})", r"\1-****-\2", contact)


def fetch_duckdb_rental_records(
    inspect_filter: TableInspectFilter,
    log_path: Path = LOG_FILE_PATH,
) -> List[RentalRecordInput]:
    """
    DuckDB (`rental_records` テーブル) を read_only=True で取得し、キーワード検索を適用して
    Pydantic v2 (`RentalRecordInput`) リストとして返す。
    """
    db_path = inspect_filter.db_path
    if not db_path.exists():
        log_structured_event(
            level="ERROR",
            event="inspect_duckdb_missing",
            message=f"閲覧対象のDuckDBファイルが存在しません: {db_path}",
            details={"db_path": str(db_path)},
            log_path=log_path,
        )
        raise DatabaseOperationError(f"DuckDBファイルが存在しません: {db_path}")

    try:
        with duckdb.connect(str(db_path), read_only=True) as conn:
            table_check = conn.execute(
                "SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'rental_records'"
            ).fetchone()[0]
            if table_check == 0:
                log_structured_event(
                    level="ERROR",
                    event="inspect_duckdb_table_missing",
                    message="DuckDB内に rental_records テーブルが存在しません。",
                    details={"db_path": str(db_path)},
                    log_path=log_path,
                )
                raise DatabaseOperationError("DuckDB内に rental_records テーブルが存在しません。")

            kw = (inspect_filter.keyword or "").strip()
            params: List[Any] = []
            where_sql = ""
            if kw:
                like_pat = f"%{kw}%"
                where_sql = """
                    WHERE property_id ILIKE ?
                       OR property_name ILIKE ?
                       OR year_month ILIKE ?
                       OR unit_number ILIKE ?
                """
                params = [like_pat, like_pat, like_pat, like_pat]

            sql = f"""
                SELECT
                    property_id,
                    property_name,
                    year_month,
                    unit_number,
                    is_occupied,
                    monthly_rent
                FROM rental_records
                {where_sql}
                ORDER BY year_month ASC, property_id ASC, unit_number ASC
            """
            rows = conn.execute(sql, params).fetchall()
            results = [
                RentalRecordInput(
                    property_id=str(r[0]),
                    property_name=str(r[1]),
                    year_month=str(r[2]),
                    unit_number=str(r[3]),
                    is_occupied=bool(r[4]),
                    monthly_rent=int(r[5]),
                )
                for r in rows
            ]

            log_structured_event(
                level="INFO",
                event="inspect_duckdb_success",
                message="DuckDB rental_records のデータ閲覧取得が完了しました。",
                details={"count": len(results), "keyword": kw, "db_path": str(db_path)},
                log_path=log_path,
            )
            return results

    except DatabaseOperationError:
        raise
    except Exception as exc:
        log_structured_event(
            level="ERROR",
            event="inspect_duckdb_error",
            message=f"DuckDBデータ閲覧取得中にエラーが発生しました: {exc}",
            details={"db_path": str(db_path), "error_type": type(exc).__name__},
            log_path=log_path,
        )
        raise DatabaseOperationError(f"DuckDBデータ閲覧エラー: {exc}") from exc


def fetch_sqlite_contracts(
    inspect_filter: TableInspectFilter,
    log_path: Path = LOG_FILE_PATH,
) -> List[ContractMasterRecord]:
    """
    SQLite (`property_management.db` の `contracts` テーブル) を URI `mode=ro`（読み取り専用）で取得し、
    キーワード検索・機密マスキングを適用して Pydantic v2 (`ContractMasterRecord`) リストとして返す。
    """
    db_path = inspect_filter.db_path
    if not db_path.exists():
        log_structured_event(
            level="ERROR",
            event="inspect_sqlite_missing",
            message=f"閲覧対象のSQLiteファイルが存在しません: {db_path}",
            details={"db_path": str(db_path)},
            log_path=log_path,
        )
        raise DatabaseOperationError(f"SQLiteファイルが存在しません: {db_path}")

    sqlite_uri = f"file:{db_path.resolve().as_posix()}?mode=ro"
    try:
        conn = sqlite3.connect(sqlite_uri, uri=True)
        conn.row_factory = sqlite3.Row
        try:
            cur = conn.cursor()
            table_check = cur.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='contracts'"
            ).fetchone()
            if not table_check:
                log_structured_event(
                    level="ERROR",
                    event="inspect_sqlite_table_missing",
                    message="SQLite内に contracts テーブルが存在しません。",
                    details={"db_path": str(db_path)},
                    log_path=log_path,
                )
                raise DatabaseOperationError("SQLite内に contracts テーブルが存在しません。")

            kw = (inspect_filter.keyword or "").strip()
            params: List[Any] = []
            where_sql = ""
            if kw:
                like_pat = f"%{kw}%"
                where_sql = """
                    WHERE contract_id LIKE ?
                       OR property_name LIKE ?
                       OR room_number LIKE ?
                       OR COALESCE(tenant_name, '') LIKE ?
                       OR COALESCE(flag, '') LIKE ?
                       OR COALESCE(memo, '') LIKE ?
                """
                params = [like_pat] * 6

            sql = f"""
                SELECT
                    contract_id,
                    COALESCE(property_id, 'P-000') AS property_id,
                    property_name,
                    room_number,
                    COALESCE(tenant_name, '') AS tenant_name,
                    current_rent,
                    new_rent,
                    COALESCE(renewal_date, '') AS renewal_date,
                    COALESCE(contact, '') AS contact,
                    COALESCE(flag, 'ACTIVE') AS flag,
                    COALESCE(memo, '') AS memo
                FROM contracts
                {where_sql}
                ORDER BY contract_id ASC
            """
            rows = cur.execute(sql, params).fetchall()

            results: List[ContractMasterRecord] = []
            for r in rows:
                raw_contact = str(r["contact"] or "")
                contact_val = _mask_phone_number(raw_contact) if inspect_filter.mask_sensitive else raw_contact
                results.append(
                    ContractMasterRecord(
                        contract_id=str(r["contract_id"]),
                        property_id=str(r["property_id"]),
                        property_name=str(r["property_name"]),
                        room_number=str(r["room_number"]),
                        tenant_name=str(r["tenant_name"]),
                        current_rent=int(r["current_rent"]),
                        new_rent=int(r["new_rent"]),
                        renewal_date=str(r["renewal_date"]),
                        contact=contact_val,
                        flag=str(r["flag"]),
                        memo=str(r["memo"]),
                    )
                )

            log_structured_event(
                level="INFO",
                event="inspect_sqlite_success",
                message="SQLite contracts のデータ閲覧取得が完了しました。",
                details={"count": len(results), "keyword": kw, "db_path": str(db_path)},
                log_path=log_path,
            )
            return results
        finally:
            conn.close()

    except DatabaseOperationError:
        raise
    except Exception as exc:
        log_structured_event(
            level="ERROR",
            event="inspect_sqlite_error",
            message=f"SQLiteデータ閲覧取得中にエラーが発生しました: {exc}",
            details={"db_path": str(db_path), "error_type": type(exc).__name__},
            log_path=log_path,
        )
        raise DatabaseOperationError(f"SQLiteデータ閲覧エラー: {exc}") from exc


if __name__ == "__main__":
    path = initialize_sample_duckdb(force_recreate=True)
    summaries = fetch_monthly_rental_summary(RentalQueryFilter(db_path=path))
    losses = fetch_property_vacancy_loss(RentalQueryFilter(db_path=path))
    print(f"Initialized {path} -> {len(summaries)} monthly summary rows, {len(losses)} property vacancy loss rows.")
