"""
자산 분배 페이지
"""
import pandas as pd
import streamlit as st
from typing import Dict, Any, Optional, List

from dashboard.api import portfolio_api
from dashboard.components import ChartComponents, LayoutComponents, FormComponents
from dashboard.config import settings
from dashboard.models import AssetAllocation, DataFrameConverter
from dashboard.utils import cache_with_ttl, format_currency, format_percentage


class AssetAllocationPage:
    """자산 분배 페이지 클래스"""

    @staticmethod
    @cache_with_ttl(ttl_seconds=300)
    def fetch_allocation_data(account: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """자산 분배 데이터 조회"""
        try:
            from logger import data_logger
            data_logger.info(f"📊 자산 분배 데이터 조회 시작 - 계정: {account or '전체'}")

            data = portfolio_api.get_allocation(account)

            if data:
                data_logger.info(f"✅ 자산 분배 데이터 조회 성공")
            return data
        except Exception as e:
            from logger import data_logger
            data_logger.error(f"💥 자산 분배 데이터 조회 실패: {str(e)}")
            st.error(f"자산 분배 조회 중 오류가 발생했습니다: {e}")
            return None

    @staticmethod
    @cache_with_ttl(ttl_seconds=300)
    def fetch_overview_data(account: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """포트폴리오 개요 데이터 조회"""
        try:
            return portfolio_api.get_overview(account)
        except Exception as e:
            from logger import data_logger
            data_logger.error(f"💥 포트폴리오 개요 데이터 조회 실패: {str(e)}")
            return None

    @staticmethod
    def render_portfolio_summary(allocation_data: Dict[str, Any], overview_data: Dict[str, Any]):
        """포트폴리오 요약 렌더링"""
        if allocation_data and allocation_data.get("total_portfolio_value"):
            total_value = allocation_data["total_portfolio_value"]
            st.subheader(f"💰 총 포트폴리오 가치: {format_currency(total_value)}")

    @staticmethod
    def render_asset_structure_charts(overview_data: Dict[str, Any]):
        """자산 구조 차트 렌더링"""
        if not overview_data:
            return

        col1, col2 = st.columns(2)

        with col1:
            st.subheader("💰 현금 vs 투자자산 비율")
            cash_value = overview_data.get("cash_asset_value", 0)
            investment_value = overview_data.get("investment_asset_value", 0)

            if cash_value + investment_value > 0:
                asset_structure_chart = ChartComponents.create_asset_structure_chart(
                    cash_value, investment_value
                )
                ChartComponents.render_chart(asset_structure_chart)

                # 요약 정보
                cash_ratio = overview_data.get("cash_asset_ratio", 0)
                investment_ratio = overview_data.get("investment_asset_ratio", 0)
                st.info(
                    f"💰 현금: {format_currency(cash_value)} ({cash_ratio:.1f}%) | "
                    f"📈 투자: {format_currency(investment_value)} ({investment_ratio:.1f}%)"
                )
            else:
                LayoutComponents.create_empty_state("자산 데이터가 없습니다.")

        with col2:
            st.subheader("📊 투자자산 분배 비율")
            investment_allocations = overview_data.get("investment_allocations", [])

            if investment_allocations:
                investment_chart = ChartComponents.create_investment_allocation_chart(
                    investment_allocations
                )
                ChartComponents.render_chart(investment_chart)

                # 상위 3개 투자자산 요약
                allocations = [AssetAllocation.from_dict(alloc) for alloc in investment_allocations]
                alloc_df = DataFrameConverter.asset_allocations_to_dataframe(allocations)

                if not alloc_df.empty:
                    top_3_alloc = alloc_df.nlargest(3, "total_market_value")
                    summary_text = " | ".join([
                        f"{row['asset_category']}: {row['allocation_percentage']:.0f}%"
                        for _, row in top_3_alloc.iterrows()
                    ])
                    st.info(f"🏆 상위 분배: {summary_text}")
            else:
                LayoutComponents.create_empty_state("투자자산 분배 데이터가 없습니다.")

    @staticmethod
    def render_allocation_details(allocation_data: Dict[str, Any]):
        """자산 분배 상세 정보 렌더링"""
        if not allocation_data or not allocation_data.get("allocations"):
            LayoutComponents.create_empty_state("자산 분배 데이터가 없습니다.")
            return

        # 데이터프레임 생성
        allocations = allocation_data["allocations"]
        allocation_models = [AssetAllocation.from_dict(alloc) for alloc in allocations]
        alloc_df = DataFrameConverter.asset_allocations_to_dataframe(allocation_models)

        if alloc_df.empty:
            LayoutComponents.create_empty_state("데이터를 변환할 수 없습니다.")
            return

        # 바 차트
        st.subheader("📈 자산유형별 평가금액")
        bar_chart = ChartComponents.create_bar_chart(
            data=alloc_df.sort_values("total_market_value", ascending=True),
            x_col="total_market_value",
            y_col="asset_category",
            title="자산유형별 평가금액",
            orientation="h",
            text_col="allocation_percentage"
        )
        ChartComponents.render_chart(bar_chart)

        # 상세 테이블
        st.subheader("📋 자산유형별 상세 정보")

        # 분배율 순으로 정렬
        display_df = alloc_df.sort_values("allocation_percentage", ascending=False)

        column_config = {
            "asset_category": "자산유형",
            "holdings_count": "보유종목수",
            "total_market_value_formatted": "평가금액",
            "allocation_percentage_formatted": "분배율"
        }

        LayoutComponents.create_data_table(
            display_df[["asset_category", "holdings_count", "total_market_value_formatted", "allocation_percentage_formatted"]],
            column_config=column_config,
            width="stretch",
            hide_index=True
        )

    @staticmethod
    def render_cash_vs_investment_simulator(overview_data: Dict[str, Any]):
        """현금 vs 투자자산 시뮬레이터 렌더링"""
        if not overview_data:
            LayoutComponents.create_warning_box(
                "시뮬레이션 오류",
                "포트폴리오 데이터를 불러올 수 없어 시뮬레이터를 실행할 수 없습니다.",
                "⚠️"
            )
            return

        st.subheader("🎯 자산분배 시뮬레이터 - 현금 vs 투자자산")

        st.markdown("원하는 현금/투자자산 비율을 설정하면 목표 달성을 위한 매매 금액을 계산합니다.")

        # 현재 자산 정보 가져오기
        current_cash = overview_data.get("cash_asset_value", 0)
        current_investment = overview_data.get("investment_asset_value", 0)
        total_assets = current_cash + current_investment

        if total_assets <= 0:
            LayoutComponents.create_warning_box(
                "시뮬레이션 오류",
                "자산 데이터가 없어 시뮬레이션을 실행할 수 없습니다.",
                "⚠️"
            )
            return

        current_cash_ratio = round((current_cash / total_assets) * 100, 1)
        current_investment_ratio = round((current_investment / total_assets) * 100, 1)

        # 현재 비율 표시
        col1, col2 = st.columns(2)

        with col1:
            st.info(
                f"**현재 비율**\n\n💰 현금: {current_cash_ratio:.1f}% ({format_currency(current_cash)})\n\n"
                f"📈 투자: {current_investment_ratio:.1f}% ({format_currency(current_investment)})"
            )

        with col2:
            st.info(f"**총 자산**: {format_currency(total_assets)}")

        # 목표 비율 입력
        st.markdown("##### 목표 비율 설정")
        target_cash_ratio = st.slider(
            "목표 현금 비율 (%)",
            min_value=0.0,
            max_value=100.0,
            value=settings.DEFAULT_CASH_RATIO,
            step=0.5,
            help="원하는 현금 자산의 비율을 설정하세요. 투자자산은 자동으로 계산됩니다.",
        )

        target_investment_ratio = 100.0 - target_cash_ratio

        # 목표 금액 계산
        target_cash = total_assets * (target_cash_ratio / 100)
        target_investment = total_assets * (target_investment_ratio / 100)

        # 필요한 조정 금액 계산
        cash_adjustment = target_cash - current_cash
        investment_adjustment = target_investment - current_investment

        # 결과 표시
        st.markdown("##### 📊 시뮬레이션 결과")

        # 메트릭 형태로 결과 표시
        current_values = {"현금": current_cash_ratio, "투자": current_investment_ratio}
        target_values = {"현금": target_cash_ratio, "투자": target_investment_ratio}
        adjustment_values = {"현금": cash_adjustment, "투자": investment_adjustment}

        ChartComponents.MetricComponents.create_simulation_metrics(
            current_values, target_values, adjustment_values
        )

        # 실행 계획 표시
        if abs(cash_adjustment) >= 1000:
            st.markdown("##### 💡 실행 계획")

            if cash_adjustment > 0:
                # 현금을 늘려야 함 = 투자자산 매도
                st.warning(
                    f"📉 **투자자산 매도**: {format_currency(abs(cash_adjustment))} 상당의 주식/펀드를 매도하여 현금 비중을 높이세요."
                )
            else:
                # 투자자산을 늘려야 함 = 현금으로 매수
                st.success(
                    f"📈 **투자자산 매수**: {format_currency(abs(investment_adjustment))} 상당의 주식/펀드를 매수하여 투자 비중을 높이세요."
                )

            # 조정 후 예상 포트폴리오
            st.markdown("**조정 후 예상 포트폴리오**")
            adjustment_data = pd.DataFrame({
                "구분": ["현금", "투자"],
                "현재 금액": [current_cash, current_investment],
                "목표 금액": [target_cash, target_investment],
                "조정 금액": [cash_adjustment, investment_adjustment],
            })

            st.dataframe(
                adjustment_data.style.format({
                    "현재 금액": format_currency,
                    "목표 금액": format_currency,
                    "조정 금액": lambda x: format_currency(x) if x != 0 else "-",
                }),
                width="stretch",
                hide_index=True,
            )
        else:
            st.success("✅ 현재 비율이 목표 비율과 유사합니다. 조정이 필요하지 않습니다.")

    @staticmethod
    def render_investment_allocation_simulator(overview_data: Dict[str, Any]):
        """투자자산 분배 시뮬레이터 렌더링"""
        if not overview_data:
            LayoutComponents.create_warning_box(
                "시뮬레이션 오류",
                "포트폴리오 데이터를 불러올 수 없어 시뮬레이터를 실행할 수 없습니다.",
                "⚠️"
            )
            return

        st.subheader("🎯 자산분배 시뮬레이터 - 투자자산 상세 분배")

        st.markdown("투자자산별 목표 비율을 설정하면 매수/매도해야 할 금액을 계산합니다.")

        # 투자자산 분배 데이터 가져오기
        investment_allocations = overview_data.get("investment_allocations", [])

        if not investment_allocations:
            LayoutComponents.create_warning_box(
                "시뮬레이션 오류",
                "투자자산 분배 데이터가 없습니다.",
                "⚠️"
            )
            return

        # 현재 투자자산 총액
        current_investment = overview_data.get("investment_asset_value", 0)

        # 데이터프레임 생성
        allocation_models = [AssetAllocation.from_dict(alloc) for alloc in investment_allocations]
        alloc_df = DataFrameConverter.asset_allocations_to_dataframe(allocation_models)

        if alloc_df.empty:
            LayoutComponents.create_warning_box(
                "시뮬레이션 오류",
                "투자자산 데이터를 변환할 수 없습니다.",
                "⚠️"
            )
            return

        # 자산유형 리스트 생성
        asset_types = alloc_df["asset_category"].tolist()

        # 현재 비율 표시
        st.info(
            f"**총 투자자산**: {format_currency(current_investment)}\n\n"
            "아래에서 각 자산의 목표 비율을 입력하세요. 합계가 100%가 되어야 합니다."
        )

        # 목표 비율 입력 폼
        simulation_data = FormComponents.create_asset_allocation_simulator(
            current_data=overview_data,
            asset_types=asset_types,
            default_ratios=settings.DEFAULT_ASSET_ALLOCATION
        )

        if simulation_data["is_valid"]:
            # 시뮬레이션 결과 계산
            st.markdown("##### 📊 시뮬레이션 결과")

            # 조정 필요 금액 계산
            adjustments = []
            for _, row in alloc_df.iterrows():
                asset_category = row["asset_category"]
                current_value = row["total_market_value"]
                current_ratio = row["allocation_percentage"]
                target_ratio = simulation_data["target_ratios"].get(asset_category, 0)

                # 목표 금액 계산
                target_value = current_investment * (target_ratio / 100)
                adjustment = target_value - current_value

                adjustments.append({
                    "자산유형": asset_category,
                    "현재 비율": current_ratio,
                    "목표 비율": target_ratio,
                    "현재 금액": current_value,
                    "목표 금액": target_value,
                    "조정 금액": adjustment,
                })

            adjustment_df = pd.DataFrame(adjustments)

            # 정렬 (asset_order 기준)
            adjustment_df["sort_key"] = adjustment_df["자산유형"].apply(
                lambda x: settings.ASSET_ORDER.index(x) if x in settings.ASSET_ORDER else len(settings.ASSET_ORDER)
            )
            adjustment_df = adjustment_df.sort_values("sort_key").reset_index(drop=True)

            # 상세 조정 내역
            st.markdown("##### 💡 자산별 조정 계획")

            # 조정 후 예상 포트폴리오 테이블
            st.dataframe(
                adjustment_df.style.format({
                    "현재 비율": "{:.0f}%",
                    "목표 비율": "{:.0f}%",
                    "현재 금액": format_currency,
                    "목표 금액": format_currency,
                    "조정 금액": lambda x: format_currency(x) if x != 0 else "-",
                }),
                width="stretch",
                hide_index=True,
            )

        else:
            st.error("⚠️ 비율 합계가 100%가 되도록 조정해주세요.")

    @staticmethod
    def render():
        """자산 분배 페이지 렌더링"""
        # 데이터 조회
        allocation_data = AssetAllocationPage.fetch_allocation_data()
        overview_data = AssetAllocationPage.fetch_overview_data()

        if allocation_data and overview_data:
            # 포트폴리오 요약
            AssetAllocationPage.render_portfolio_summary(allocation_data, overview_data)

            st.markdown("---")

            # 자산 구조 차트
            AssetAllocationPage.render_asset_structure_charts(overview_data)

            st.markdown("---")

            # 자산 분배 상세 정보
            AssetAllocationPage.render_allocation_details(allocation_data)

            st.markdown("---")

            # 자산분배 시뮬레이터
            st.subheader("🎯 자산분배 시뮬레이터")

            # 탭으로 두 시뮬레이터 구분
            sim_tab1, sim_tab2 = st.tabs([
                "💰 현금 vs 투자자산", "📊 투자자산 상세 분배"
            ])

            with sim_tab1:
                AssetAllocationPage.render_cash_vs_investment_simulator(overview_data)

            with sim_tab2:
                AssetAllocationPage.render_investment_allocation_simulator(overview_data)

        else:
            LayoutComponents.create_warning_box(
                "데이터 로딩 실패",
                "자산 분배 데이터를 불러올 수 없습니다. API 서버가 실행 중인지 확인해주세요.",
                "⚠️"
            )