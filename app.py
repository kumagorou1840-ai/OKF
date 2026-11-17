#!/usr/bin/env python3
"""
app.py
DuckDB (data/rental_data.duckdb) の物件別・月別 家賃収入＆稼働率および
空室損失額（機会損失）、さらに DuckDB / SQLite の生テーブル閲覧・検索を
Plotly と Streamlit で可視化するダッシュボードアプリケーション。

要件:
- 物件名でフィルタリングできるサイドバー
- タブ1: 月次推移の棒グラフ（家賃収入）・折れ線グラフ（稼働率）（Plotly）
- タブ2: 物件別の空室損失額（機会損失）の棒グラフ＆月別内訳（Plotly）
- タブ3: DuckDB (`rental_records`) と SQLite (`contracts`) の一覧表示・キーワード検索・CSVダウンロード
- エラー発生時の例外キャッチと logs/app.log への構造化ログ記録
"""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

from src.db import (
    DEFAULT_DB_PATH,
    DEFAULT_SQLITE_PATH,
    LOG_FILE_PATH,
    DatabaseOperationError,
    RentalQueryFilter,
    TableInspectFilter,
    fetch_duckdb_rental_records,
    fetch_monthly_rental_summary,
    fetch_property_vacancy_loss,
    fetch_sqlite_contracts,
    initialize_sample_duckdb,
    list_property_names,
    log_structured_event,
)
from src.repair_db import fetch_monthly_repair_summary, initialize_sample_repairs
from src.yield_calc import calculate_net_yield_summaries, estimate_sapporo_other_expenses


def build_combined_chart(df: pd.DataFrame) -> go.Figure:
    """物件別の月次家賃収入（棒グラフ）と平均稼働率（折れ線グラフ）の2軸複合チャートを生成"""
    monthly_avg_occ = (
        df.groupby("year_month", as_index=False)
        .agg(
            total_occupied=("occupied_units", "sum"),
            total_units=("total_units", "sum"),
        )
    )
    monthly_avg_occ["avg_occupancy_rate"] = (
        monthly_avg_occ["total_occupied"] * 100.0 / monthly_avg_occ["total_units"]
    ).round(2)

    fig = make_subplots(specs=[[{"secondary_y": True}]])

    for prop_name, group_df in df.groupby("property_name"):
        fig.add_trace(
            go.Bar(
                x=group_df["year_month"],
                y=group_df["rent_revenue"],
                name=f"{prop_name} (家賃収入)",
                hovertemplate="<b>%{x}</b><br>物件: " + prop_name + "<br>家賃収入: ¥%{y:,.0f}<extra></extra>",
            ),
            secondary_y=False,
        )

    fig.add_trace(
        go.Scatter(
            x=monthly_avg_occ["year_month"],
            y=monthly_avg_occ["avg_occupancy_rate"],
            name="全体稼働率 (%)",
            mode="lines+markers",
            line=dict(color="#FF4B4B", width=3),
            marker=dict(size=8),
            hovertemplate="<b>%{x}</b><br>全体稼働率: %{y:.2f}%<extra></extra>",
        ),
        secondary_y=True,
    )

    fig.update_layout(
        title="📊 月次家賃収入（棒グラフ）＆ 全体稼働率推移（折れ線）",
        barmode="group",
        template="plotly_white",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        height=460,
    )
    fig.update_xaxes(title_text="対象年月 (YYYY-MM)")
    fig.update_yaxes(title_text="月間家賃収入 (円)", secondary_y=False, tickprefix="¥", tickformat=",")
    fig.update_yaxes(title_text="稼働率 (%)", secondary_y=True, range=[0, 105], ticksuffix="%")

    return fig


def render_db_inspector_tab() -> None:
    """第3タブ：🗄️ DBデータ閲覧・検索（DuckDB / SQLite 読み取り専用ビューア）"""
    st.subheader("🗄️ データベース生テーブル閲覧・キーワード検索 (Read-Only)")

    col_src, col_kw, col_mask = st.columns([2, 2, 1])
    with col_src:
        source_label = st.radio(
            "閲覧するデータベース・テーブルを選択",
            options=[
                "🦆 DuckDB: rental_records (月次展開データ)",
                "🗄️ SQLite: contracts (契約マスターデータ)",
            ],
            horizontal=False,
        )
    with col_kw:
        keyword = st.text_input(
            "🔎 キーワード検索（物件名・部屋番号・入居者名・年月・契約ID）",
            value="",
            placeholder="例: メゾン札幌北 / 101 / 鈴木 / VACANT / 2026-07",
        )
    with col_mask:
        mask_sensitive = st.checkbox(
            "🔒 電話番号をマスク",
            value=True,
            help="AGENTS.md の機密情報保護ルールに基づき、電話番号の中間桁を **** でマスクします。",
        )

    try:
        if source_label.startswith("🦆"):
            inspect_filter = TableInspectFilter(
                source_type="duckdb_rental_records",
                db_path=DEFAULT_DB_PATH,
                keyword=keyword,
                mask_sensitive=mask_sensitive,
            )
            records = fetch_duckdb_rental_records(inspect_filter)
            if not records:
                st.warning("条件に一致する DuckDB `rental_records` データは 0 件です。")
                return

            df_raw = pd.DataFrame([r.model_dump() for r in records])
            st.caption(f"表示件数: **{len(df_raw):,} 件** （ソース: `{DEFAULT_DB_PATH.name}` / `read_only=True`）")

            df_display = df_raw.rename(
                columns={
                    "property_id": "物件ID",
                    "property_name": "物件名",
                    "year_month": "対象年月",
                    "unit_number": "部屋番号",
                    "is_occupied": "入居中",
                    "monthly_rent": "月額家賃 (円)",
                }
            )
            st.dataframe(df_display, use_container_width=True, height=420)

            csv_bytes = df_display.to_csv(index=False).encode("utf-8-sig")
            st.download_button(
                label="📥 DuckDB 検索結果を CSV ダウンロード",
                data=csv_bytes,
                file_name="duckdb_rental_records_export.csv",
                mime="text/csv",
            )

        else:
            inspect_filter = TableInspectFilter(
                source_type="sqlite_contracts",
                db_path=DEFAULT_SQLITE_PATH,
                keyword=keyword,
                mask_sensitive=mask_sensitive,
            )
            records = fetch_sqlite_contracts(inspect_filter)
            if not records:
                st.warning("条件に一致する SQLite `contracts` データは 0 件です。")
                return

            df_raw = pd.DataFrame([r.model_dump() for r in records])
            st.caption(f"表示件数: **{len(df_raw):,} 件** （ソース: `{DEFAULT_SQLITE_PATH.name}` / `mode=ro`）")

            df_display = df_raw.rename(
                columns={
                    "contract_id": "契約ID",
                    "property_id": "物件ID",
                    "property_name": "物件名",
                    "room_number": "部屋番号",
                    "tenant_name": "入居者名",
                    "current_rent": "現家賃 (円)",
                    "new_rent": "新家賃 (円)",
                    "renewal_date": "契約更新日",
                    "contact": "連絡先",
                    "flag": "ステータス",
                    "memo": "備考メモ",
                }
            )
            st.dataframe(df_display, use_container_width=True, height=420)

            csv_bytes = df_display.to_csv(index=False).encode("utf-8-sig")
            st.download_button(
                label="📥 SQLite 検索結果を CSV ダウンロード",
                data=csv_bytes,
                file_name="sqlite_contracts_export.csv",
                mime="text/csv",
            )

    except DatabaseOperationError as db_err:
        st.error(f"DBデータ閲覧中にエラーが発生しました: {db_err}")
    except Exception as exc:
        log_structured_event(
            level="ERROR",
            event="ui_inspect_tab_error",
            message=f"DB閲覧タブで予期せぬエラーが発生しました: {exc}",
            details={"keyword": keyword, "source": source_label},
        )
        st.error(f"予期せぬエラーが発生しました: {exc}")


def main() -> None:
    st.set_page_config(
        page_title="不動産賃貸 家賃収入・稼働率・空室損失ダッシュボード",
        page_icon="🏢",
        layout="wide",
    )

    st.title("🏢 不動産賃貸 物件別・月次 家賃収入＆空室損失ダッシュボード")
    st.caption(
        f"DuckDB: `{DEFAULT_DB_PATH}` | SQLite: `{DEFAULT_SQLITE_PATH}` | Log: `{LOG_FILE_PATH}`"
    )

    try:
        if not DEFAULT_DB_PATH.exists():
            initialize_sample_duckdb(DEFAULT_DB_PATH)

        all_properties = list_property_names(DEFAULT_DB_PATH)
    except DatabaseOperationError as db_err:
        st.error(f"データベース初期化・接続エラーが発生しました: {db_err}")
        return
    except Exception as exc:
        log_structured_event(
            level="ERROR",
            event="ui_unexpected_error",
            message=f"UI起動時に予期せぬエラーが発生しました: {exc}",
            details={"error_type": type(exc).__name__},
        )
        st.error(f"予期せぬエラーが発生しました: {exc}")
        return

    # --- サイドバー（物件名・期間フィルタ） ---
    st.sidebar.header("🔍 フィルタ設定")
    selected_properties = st.sidebar.multiselect(
        "対象物件を選択",
        options=all_properties,
        default=all_properties,
        help="表示したい物件を1つ以上選択してください。",
    )

    month_options = [f"2026-{m:02d}" for m in range(1, 13)]
    start_month, end_month = st.sidebar.select_slider(
        "対象期間 (YYYY-MM)",
        options=month_options,
        value=(month_options[0], month_options[-1]),
    )

    if not selected_properties:
        st.warning("サイドバーから少なくとも1つの物件を選択してください。")
        return

    # --- データ集計クエリ実行（Pydantic v2 検証付き） ---
    try:
        query_filter = RentalQueryFilter(
            db_path=DEFAULT_DB_PATH,
            property_names=selected_properties,
            start_month=start_month,
            end_month=end_month,
        )
        summaries = fetch_monthly_rental_summary(query_filter)
        vacancy_losses = fetch_property_vacancy_loss(query_filter)
    except Exception as exc:
        log_structured_event(
            level="ERROR",
            event="ui_query_error",
            message=f"集計クエリ実行エラー: {exc}",
            details={"selected_properties": selected_properties},
        )
        st.error(f"データ集計中にエラーが発生しました: {exc}")
        return

    if not summaries:
        st.info("指定された条件に一致するデータがありません。")
        return

    df = pd.DataFrame([s.model_dump() for s in summaries])
    df_loss = pd.DataFrame([v.model_dump() for v in vacancy_losses])

    # --- KPI サマリーカード ---
    total_rev = int(df["rent_revenue"].sum())
    total_loss = int(df["vacancy_loss"].sum())
    avg_occ = float(
        (df["occupied_units"].sum() * 100.0 / df["total_units"].sum()).round(2)
    )
    latest_month = df["year_month"].max()
    latest_rev = int(df[df["year_month"] == latest_month]["rent_revenue"].sum())

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("💰 期間累計 家賃収入", f"¥{total_rev:,}")
    col2.metric("💸 期間累計 空室損失額（機会損失）", f"¥{total_loss:,}")
    col3.metric("📈 期間平均 稼働率", f"{avg_occ:.2f}%")
    col4.metric(f"🗓️ 最新月 ({latest_month}) 家賃収入", f"¥{latest_rev:,}")

    st.divider()

    # --- 4タブ構成 ---
    tab_main, tab_vacancy, tab_finance, tab_inspect = st.tabs(
        [
            "📊 家賃収入・稼働率推移",
            "💸 空室損失額（機会損失）分析",
            "🛠️ 修繕履歴・実質利回り（NOI）シミュレーション",
            "🗄️ DBデータ閲覧・検索",
        ]
    )

    with tab_main:
        st.plotly_chart(build_combined_chart(df), use_container_width=True)

        col_bar, col_line = st.columns(2)
        with col_bar:
            fig_bar = px.bar(
                df,
                x="year_month",
                y="rent_revenue",
                color="property_name",
                barmode="group",
                title="🏢 物件別・月次家賃収入（棒グラフ）",
                labels={
                    "year_month": "対象年月",
                    "rent_revenue": "家賃収入 (円)",
                    "property_name": "物件名",
                },
                template="plotly_white",
            )
            fig_bar.update_yaxes(tickprefix="¥", tickformat=",")
            st.plotly_chart(fig_bar, use_container_width=True)

        with col_line:
            fig_line = px.line(
                df,
                x="year_month",
                y="occupancy_rate",
                color="property_name",
                markers=True,
                title="📈 物件別・月次稼働率推移（折れ線グラフ）",
                labels={
                    "year_month": "対象年月",
                    "occupancy_rate": "稼働率 (%)",
                    "property_name": "物件名",
                },
                template="plotly_white",
            )
            fig_line.update_yaxes(range=[0, 105], ticksuffix="%")
            st.plotly_chart(fig_line, use_container_width=True)

        with st.expander("📋 物件別・月別 集計データ一覧（Pydantic v2 検証済）", expanded=False):
            st.dataframe(
                df.rename(
                    columns={
                        "property_name": "物件名",
                        "year_month": "対象年月",
                        "total_units": "総戸数",
                        "occupied_units": "稼働戸数",
                        "vacant_units": "空室戸数",
                        "rent_revenue": "家賃収入 (円)",
                        "vacancy_loss": "空室損失額 (円)",
                        "occupancy_rate": "稼働率 (%)",
                    }
                ),
                use_container_width=True,
            )

    with tab_vacancy:
        st.subheader("💸 物件別の空室損失額（機会損失）サマリー")
        col_loss_bar, col_loss_monthly = st.columns(2)

        with col_loss_bar:
            fig_prop_loss = px.bar(
                df_loss,
                x="property_name",
                y="total_vacancy_loss",
                color="property_name",
                text_auto=",.0f",
                title="🏢 物件別・期間累計 空室損失額（棒グラフ）",
                labels={
                    "property_name": "物件名",
                    "total_vacancy_loss": "累計空室損失額 (円)",
                },
                template="plotly_white",
            )
            fig_prop_loss.update_yaxes(tickprefix="¥", tickformat=",")
            fig_prop_loss.update_traces(
                hovertemplate="<b>%{x}</b><br>累計空室損失額: ¥%{y:,.0f}<extra></extra>"
            )
            st.plotly_chart(fig_prop_loss, use_container_width=True)

        with col_loss_monthly:
            fig_monthly_loss = px.bar(
                df,
                x="year_month",
                y="vacancy_loss",
                color="property_name",
                barmode="group",
                title="🗓️ 物件別・月次 空室損失額の推移（棒グラフ）",
                labels={
                    "year_month": "対象年月",
                    "vacancy_loss": "月間空室損失額 (円)",
                    "property_name": "物件名",
                },
                template="plotly_white",
            )
            fig_monthly_loss.update_yaxes(tickprefix="¥", tickformat=",")
            st.plotly_chart(fig_monthly_loss, use_container_width=True)

        st.dataframe(
            df_loss.rename(
                columns={
                    "property_name": "物件名",
                    "total_vacant_unit_months": "延べ空室戸月数 (戸・月)",
                    "total_vacancy_loss": "累計空室損失額 (円)",
                    "potential_revenue": "満室想定家賃収入 (円)",
                    "loss_rate": "機会損失率 (%)",
                }
            ),
            use_container_width=True,
        )

    with tab_finance:
        st.subheader("🛠️ 物件別・修繕履歴 ＆ 実質利回り（NOIベース）シミュレーション")
        try:
            initialize_sample_repairs(DEFAULT_DB_PATH)
            repair_summaries = fetch_monthly_repair_summary(query_filter)
            other_expenses = estimate_sapporo_other_expenses(summaries)
            yield_summaries = calculate_net_yield_summaries(
                summaries,
                repair_summaries,
                other_expenses=other_expenses,
            )
            st.caption("※ その他経費には管理委託費（5%）＋共用部固定費＋冬期（11〜3月）除雪・RH加算を含めています。")

            if yield_summaries:
                df_yield = pd.DataFrame([y.model_dump() for y in yield_summaries])
                col_y1, col_y2 = st.columns(2)
                with col_y1:
                    fig_yield = px.bar(
                        df_yield,
                        x="property_name",
                        y=["gross_yield_pct", "net_yield_pct"],
                        barmode="group",
                        title="📈 物件別 表面利回り vs 実質利回り（NOIベース %）",
                        labels={
                            "property_name": "物件名",
                            "value": "利回り (%)",
                            "variable": "指標",
                        },
                        template="plotly_white",
                    )
                    fig_yield.update_yaxes(ticksuffix="%")
                    st.plotly_chart(fig_yield, use_container_width=True)

                with col_y2:
                    if repair_summaries:
                        df_rep = pd.DataFrame([r.model_dump() for r in repair_summaries])
                        fig_rep = px.bar(
                            df_rep,
                            x="year_month",
                            y="total_repair_cost",
                            color="property_name",
                            barmode="group",
                            title="🔧 物件別・月次 修繕費推移（棒グラフ）",
                            labels={
                                "year_month": "対象年月",
                                "total_repair_cost": "修繕費合計 (円)",
                                "property_name": "物件名",
                            },
                            template="plotly_white",
                        )
                        fig_rep.update_yaxes(tickprefix="¥", tickformat=",")
                        st.plotly_chart(fig_rep, use_container_width=True)
                    else:
                        st.info("選択された期間・物件の修繕履歴はありません（修繕費 ¥0）。")

                st.dataframe(
                    df_yield.rename(
                        columns={
                            "property_name": "物件名",
                            "gross_revenue": "期間家賃収入 (円)",
                            "total_repair_cost": "期間修繕費合計 (円)",
                            "other_operating_expenses": "その他経費 (円)",
                            "noi": "純営業収益 NOI (円)",
                            "property_price": "想定物件価格 (円)",
                            "gross_yield_pct": "表面利回り (%)",
                            "net_yield_pct": "実質利回り NOI (%)",
                        }
                    ),
                    use_container_width=True,
                )
        except Exception as exc:
            st.error(f"修繕・利回りシミュレーション中にエラーが発生しました: {exc}")

    with tab_inspect:
        render_db_inspector_tab()


if __name__ == "__main__":
    main()
