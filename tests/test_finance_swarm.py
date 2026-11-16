#!/usr/bin/env python3
"""
tests/test_finance_swarm.py
修繕履歴・収支シミュレーション機能（models_finance.py / repair_db.py / yield_calc.py）の単体・統合テストスイート（Agent C 設計実装）。
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import duckdb
import pytest
from pydantic import ValidationError

from src.db import DatabaseOperationError, MonthlyRentalSummary, RentalQueryFilter
from src.models_finance import (
    MonthlyRepairSummary,
    NetYieldSummary,
    RepairExpenseInput,
)
from src.repair_db import fetch_monthly_repair_summary, initialize_sample_repairs
from src.yield_calc import calculate_net_yield_summaries


def test_repair_expense_pydantic_validation() -> None:
    """1. RepairExpenseInput および NetYieldSummary の Pydantic v2 バリデーション検証"""
    # マイナスの repair_cost
    with pytest.raises(ValidationError):
        RepairExpenseInput(
            property_id="P001",
            property_name="メゾン札幌北",
            year_month="2026-01",
            category="給湯器交換",
            repair_cost=-5000,
            description="異常値テスト",
        )

    # 不正な year_month フォーマット
    with pytest.raises(ValidationError):
        RepairExpenseInput(
            property_id="P001",
            property_name="メゾン札幌北",
            year_month="2026-13",
            category="給湯器交換",
            repair_cost=50000,
            description="不正年月テスト",
        )

    # 空白のみの property_name
    with pytest.raises(ValidationError):
        RepairExpenseInput(
            property_id="P001",
            property_name="   ",
            year_month="2026-01",
            category="原状回復",
            repair_cost=30000,
            description="空白物件名テスト",
        )

    # NetYieldSummary: マイナスの property_price
    with pytest.raises(ValidationError):
        NetYieldSummary(
            property_name="メゾン札幌北",
            gross_revenue=1_000_000,
            total_repair_cost=100_000,
            noi=900_000,
            property_price=-1000,
            gross_yield_pct=3.5,
            net_yield_pct=3.2,
        )

    # NetYieldSummary: マイナスの gross_revenue
    with pytest.raises(ValidationError):
        NetYieldSummary(
            property_name="メゾン札幌北",
            gross_revenue=-500,
            total_repair_cost=100_000,
            noi=-100_500,
            property_price=28_000_000,
            gross_yield_pct=0.0,
            net_yield_pct=-0.36,
        )


def test_repair_db_initialize_and_aggregation(tmp_path: Path) -> None:
    """2. 修繕費DuckDBの初期化・月次集計・フィルタ・異常系（未存在DB・NULL混入）とログ出力検証"""
    db_path = tmp_path / "test.duckdb"
    log_path = tmp_path / "app.log"

    # サンプルデータの初期化と全件集計
    initialized_path = initialize_sample_repairs(
        db_path=db_path,
        force_recreate=True,
        log_path=log_path,
    )
    assert initialized_path == db_path
    assert db_path.exists()

    all_summaries = fetch_monthly_repair_summary(
        RentalQueryFilter(db_path=db_path),
        log_path=log_path,
    )
    assert len(all_summaries) > 0
    assert all(isinstance(item, MonthlyRepairSummary) for item in all_summaries)
    assert all(item.repair_count >= 0 and item.total_repair_cost >= 0 for item in all_summaries)

    # 物件フィルタ・期間フィルタの検証
    target_prop = all_summaries[0].property_name
    filtered_summaries = fetch_monthly_repair_summary(
        RentalQueryFilter(
            db_path=db_path,
            property_names=[target_prop],
            start_month="2026-02",
            end_month="2026-06",
        ),
        log_path=log_path,
    )
    assert len(filtered_summaries) > 0
    assert all(item.property_name == target_prop for item in filtered_summaries)
    assert all("2026-02" <= item.year_month <= "2026-06" for item in filtered_summaries)

    # 異常系①: 存在しないDBパスに対する DatabaseOperationError とログ記録
    missing_db = tmp_path / "non_existent_repair.duckdb"
    with pytest.raises(DatabaseOperationError):
        fetch_monthly_repair_summary(
            RentalQueryFilter(db_path=missing_db),
            log_path=log_path,
        )

    assert log_path.exists()
    log_entries = [
        json.loads(line)
        for line in log_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert any(entry.get("level") == "ERROR" for entry in log_entries)

    # 異常系②: NULL混入テーブル（repair_records）に対する DatabaseOperationError とログ記録
    corrupt_db = tmp_path / "corrupt_repair.duckdb"
    corrupt_log = tmp_path / "corrupt_app.log"
    with duckdb.connect(str(corrupt_db)) as conn:
        conn.execute(
            """
            CREATE TABLE repair_records (
                property_id VARCHAR,
                property_name VARCHAR,
                year_month VARCHAR,
                category VARCHAR,
                repair_cost INTEGER,
                description VARCHAR
            )
            """
        )
        conn.execute(
            "INSERT INTO repair_records VALUES ('P001', NULL, '2026-01', '配管修理', NULL, 'NULL混入テスト')"
        )

    with pytest.raises(DatabaseOperationError, match="修繕データ欠損エラー"):
        fetch_monthly_repair_summary(
            RentalQueryFilter(db_path=corrupt_db),
            log_path=corrupt_log,
        )

    assert corrupt_log.exists()
    corrupt_entries = [
        json.loads(line)
        for line in corrupt_log.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert any(entry.get("event") == "repair_data_missing_detected" for entry in corrupt_entries)


def test_yield_calc_normal_and_zero_division() -> None:
    """3. 実質利回り（NOI）計算の正常系およびゼロ除算回避（空リスト・物件価格0）検証"""
    rental_samples = [
        MonthlyRentalSummary(
            property_name="メゾン札幌北",
            year_month="2026-01",
            total_units=10,
            occupied_units=9,
            vacant_units=1,
            rent_revenue=540_000,
            vacancy_loss=60_000,
            occupancy_rate=90.0,
        ),
        MonthlyRentalSummary(
            property_name="メゾン札幌北",
            year_month="2026-02",
            total_units=10,
            occupied_units=10,
            vacant_units=0,
            rent_revenue=600_000,
            vacancy_loss=0,
            occupancy_rate=100.0,
        ),
    ]
    repair_samples = [
        MonthlyRepairSummary(
            property_name="メゾン札幌北",
            year_month="2026-01",
            repair_count=2,
            total_repair_cost=140_000,
        ),
    ]

    # 正常系検証（物件価格 20,000,000円: 家賃計 1,140,000円、修繕費計 140,000円、NOI 1,000,000円）
    results = calculate_net_yield_summaries(
        rental_summaries=rental_samples,
        repair_summaries=repair_samples,
        property_prices={"メゾン札幌北": 20_000_000},
    )
    assert len(results) == 1
    summary = results[0]
    assert isinstance(summary, NetYieldSummary)
    assert summary.property_name == "メゾン札幌北"
    assert summary.gross_revenue == 1_140_000
    assert summary.total_repair_cost == 140_000
    assert summary.noi == 1_000_000
    assert summary.property_price == 20_000_000
    assert summary.gross_yield_pct == pytest.approx(5.7, rel=1e-3)
    assert summary.net_yield_pct == pytest.approx(5.0, rel=1e-3)

    # ゼロ除算回避検証①: 空リストを渡した際に [] が返ること
    empty_results = calculate_net_yield_summaries([], [])
    assert empty_results == []

    # ゼロ除算回避検証②: 物件価格 0 を渡した際に ZeroDivisionError にならず 0.0% となること
    zero_price_results = calculate_net_yield_summaries(
        rental_summaries=rental_samples,
        repair_summaries=repair_samples,
        property_prices={"メゾン札幌北": 0},
    )
    assert len(zero_price_results) == 1
    zero_summary = zero_price_results[0]
    assert zero_summary.property_price == 0
    assert zero_summary.gross_yield_pct == 0.0
    assert zero_summary.net_yield_pct == 0.0
