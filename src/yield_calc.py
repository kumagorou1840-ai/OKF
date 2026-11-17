#!/usr/bin/env python3
"""
src/yield_calc.py
家賃収入集計（MonthlyRentalSummary）と修繕費集計（MonthlyRepairSummary）から、
物件別の純営業収益（NOI）・表面利回り・実質利回り（NetYieldSummary）を算出する純粋関数モジュール（Agent B 設計実装）。
"""

from __future__ import annotations

from collections import defaultdict
from typing import Dict, List, Optional, Sequence

from src.db import MonthlyRentalSummary
from src.models_finance import (
    DEFAULT_MANAGEMENT_FEE_RATE,
    DEFAULT_MONTHLY_OTHER_EXPENSES,
    DEFAULT_PROPERTY_PRICES,
    DEFAULT_WINTER_SNOW_SURCHARGE,
    FALLBACK_MONTHLY_OTHER_EXPENSE,
    FALLBACK_PROPERTY_PRICE,
    MonthlyRepairSummary,
    NetYieldSummary,
    WINTER_SNOW_MONTHS,
)


def estimate_sapporo_other_expenses(
    rental_summaries: Sequence[MonthlyRentalSummary],
    monthly_fixed_expenses: Optional[Dict[str, Optional[int]]] = None,
    management_fee_rate: float = DEFAULT_MANAGEMENT_FEE_RATE,
    winter_snow_surcharge: int = DEFAULT_WINTER_SNOW_SURCHARGE,
) -> Dict[str, int]:
    """
    物件別の家賃収入と対象月数から、札幌の運営経費（管理委託費＋固定費＋冬期除雪/RH加算）を算出する。
    欠損値（None）や負値は安全にフォールバック/0クリップする。
    """
    if not rental_summaries:
        return {}

    fixed_map = (
        monthly_fixed_expenses
        if monthly_fixed_expenses is not None
        else DEFAULT_MONTHLY_OTHER_EXPENSES
    )
    safe_rate = max(0.0, float(management_fee_rate))
    safe_surcharge = max(0, int(winter_snow_surcharge))

    totals: Dict[str, int] = defaultdict(int)
    for rental in rental_summaries:
        prop_name = rental.property_name
        raw_fixed = fixed_map.get(prop_name, FALLBACK_MONTHLY_OTHER_EXPENSE)
        monthly_fixed = FALLBACK_MONTHLY_OTHER_EXPENSE if raw_fixed is None else max(0, int(raw_fixed))
        mgmt_fee = int(round(max(0, rental.rent_revenue) * safe_rate))

        month_part = rental.year_month.split("-")[1] if "-" in rental.year_month else ""
        snow_cost = safe_surcharge if month_part in WINTER_SNOW_MONTHS else 0

        totals[prop_name] += mgmt_fee + monthly_fixed + snow_cost

    return dict(totals)


def calculate_net_yield_summaries(
    rental_summaries: Sequence[MonthlyRentalSummary],
    repair_summaries: Sequence[MonthlyRepairSummary],
    property_prices: Optional[Dict[str, int]] = None,
    other_expenses: Optional[Dict[str, Optional[int]]] = None,
) -> List[NetYieldSummary]:
    """
    物件別の家賃収入と修繕費・その他運営経費からNOI（純営業収益）および表面・実質利回りを算出する。
    """
    if not rental_summaries and not repair_summaries:
        return []

    revenue_by_prop: Dict[str, int] = defaultdict(int)
    repair_by_prop: Dict[str, int] = defaultdict(int)
    property_names: set[str] = set()

    for rental in rental_summaries:
        prop_name = rental.property_name
        property_names.add(prop_name)
        revenue_by_prop[prop_name] += rental.rent_revenue

    for repair in repair_summaries:
        prop_name = repair.property_name
        property_names.add(prop_name)
        repair_by_prop[prop_name] += repair.total_repair_cost

    price_map = property_prices if property_prices is not None else DEFAULT_PROPERTY_PRICES
    expense_map = other_expenses or {}

    results: List[NetYieldSummary] = []
    for prop_name in property_names:
        gross_revenue = revenue_by_prop[prop_name]
        total_repair_cost = repair_by_prop[prop_name]
        raw_other_exp = expense_map.get(prop_name, 0)
        other_exp = 0 if raw_other_exp is None else max(0, int(raw_other_exp))
        raw_price = price_map.get(prop_name, FALLBACK_PROPERTY_PRICE)
        property_price = FALLBACK_PROPERTY_PRICE if raw_price is None else max(0, int(raw_price))

        noi = gross_revenue - total_repair_cost - other_exp

        if property_price > 0:
            gross_yield_pct = round(gross_revenue * 100.0 / property_price, 2)
            net_yield_pct = round(noi * 100.0 / property_price, 2)
        else:
            gross_yield_pct = 0.0
            net_yield_pct = 0.0

        summary = NetYieldSummary(
            property_name=prop_name,
            gross_revenue=gross_revenue,
            total_repair_cost=total_repair_cost,
            other_operating_expenses=other_exp,
            noi=noi,
            property_price=property_price,
            gross_yield_pct=gross_yield_pct,
            net_yield_pct=net_yield_pct,
        )
        results.append(summary)

    results.sort(key=lambda item: (-item.net_yield_pct, item.property_name))
    return results
