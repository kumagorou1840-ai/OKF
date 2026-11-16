#!/usr/bin/env python3
"""
src/models_finance.py
賃貸経営の「修繕履歴・収支シミュレーション機能」における共通 Pydantic v2 スキーマ定義。
全サブエージェント（Agent A: repair_db.py, Agent B: yield_calc.py, Agent C: test_finance_swarm.py）が
参照する単一の型契約（Single Source of Truth）。
"""

from __future__ import annotations

from typing import Dict
from pydantic import BaseModel, Field, field_validator

YEAR_MONTH_PATTERN = r"^\d{4}-(0[1-9]|1[0-2])$"

DEFAULT_PROPERTY_PRICES: Dict[str, int] = {
    "メゾン札幌北": 28_000_000,
    "コーポ大通東": 32_000_000,
    "円山グリーンハイツ": 35_000_000,
    "北18条レジデンス": 30_000_000,
    "大通パークサイドコート": 42_000_000,
}
FALLBACK_PROPERTY_PRICE: int = 30_000_000


class RepairExpenseInput(BaseModel):
    """修繕費明細の入力・シード用スキーマ"""

    property_id: str = Field(..., min_length=1, description="物件ID")
    property_name: str = Field(..., min_length=1, description="物件名")
    year_month: str = Field(..., pattern=YEAR_MONTH_PATTERN, description="対象年月 (YYYY-MM)")
    category: str = Field(..., min_length=1, description="修繕カテゴリ（給湯器・配管、原状回復、共用部等）")
    repair_cost: int = Field(..., ge=0, description="修繕費用（円・マイナス不可）")
    description: str = Field(default="", description="修繕内容の詳細メモ")

    @field_validator("property_id", "property_name", "category")
    @classmethod
    def check_not_blank(cls, v: str) -> str:
        cleaned = v.strip()
        if not cleaned:
            raise ValueError("空白のみの文字列は許可されません。")
        return cleaned


class MonthlyRepairSummary(BaseModel):
    """物件別・月別の修繕費集計出力スキーマ（Agent A -> Agent B 連携用）"""

    property_name: str = Field(..., min_length=1, description="物件名")
    year_month: str = Field(..., pattern=YEAR_MONTH_PATTERN, description="対象年月 (YYYY-MM)")
    repair_count: int = Field(..., ge=0, description="月間修繕件数")
    total_repair_cost: int = Field(..., ge=0, description="月間修繕費合計（円）")


class NetYieldSummary(BaseModel):
    """物件別の実質利回り（NOIベース）算出結果スキーマ（Agent B 出力用）"""

    property_name: str = Field(..., min_length=1, description="物件名")
    gross_revenue: int = Field(..., ge=0, description="期間内の家賃収入合計（円）")
    total_repair_cost: int = Field(..., ge=0, description="期間内の修繕費合計（円）")
    other_operating_expenses: int = Field(default=0, ge=0, description="その他運営経費合計（円）")
    noi: int = Field(..., description="純営業収益 NOI = gross_revenue - total_repair_cost - other_operating_expenses（円）")
    property_price: int = Field(..., ge=0, description="物件取得価格・投資額（円）")
    gross_yield_pct: float = Field(..., ge=0.0, description="表面利回り（%：gross_revenue / property_price * 100）")
    net_yield_pct: float = Field(..., description="実質利回り（NOIベース %：noi / property_price * 100）")
