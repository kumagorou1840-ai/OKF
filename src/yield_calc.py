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
    DEFAULT_PROPERTY_PRICES,
    FALLBACK_PROPERTY_PRICE,
    MonthlyRepairSummary,
    NetYieldSummary,
)


def calculate_net_yield_summaries(
    rental_summaries: Sequence[MonthlyRentalSummary],
    repair_summaries: Sequence[MonthlyRepairSummary],
    property_prices: Optional[Dict[str, int]] = None,
    other_expenses: Optional[Dict[str, int]] = None,
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
        other_exp = expense_map.get(prop_name, 0)
        property_price = price_map.get(prop_name, FALLBACK_PROPERTY_PRICE)

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
