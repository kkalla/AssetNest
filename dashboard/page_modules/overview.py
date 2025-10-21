"""
포트폴리오 개요 페이지
"""
import streamlit as st
from typing import Dict, Any, Optional

from dashboard.api import portfolio_api
from dashboard.components import MetricComponents, ChartComponents, LayoutComponents
from dashboard.utils import cache_with_ttl, format_currency


class PortfolioOverviewPage:
    """포트폴리오 개요 페이지 클래스"""

    @staticmethod
    @cache_with_ttl(ttl_seconds=300)
    def fetch_portfolio_data(account: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """포트폴리오 데이터 조회"""
        try:
            from logger import data_logger
            data_logger.info(f"📊 포트폴리오 개요 데이터 조회 시작 - 계정: {account or '전체'}")

            data = portfolio_api.get_overview(account)

            if data:
                data_logger.info(f"✅ 포트폴리오 개요 데이터 조회 성공 - 총 자산: ₩{data.get('total_value_krw', 0):,.0f}")
            return data
        except Exception as e:
            from logger import data_logger
            data_logger.error(f"💥 포트폴리오 개요 데이터 조회 실패: {str(e)}")
            st.error(f"데이터 조회 중 오류가 발생했습니다: {e}")
            return None

    @staticmethod
    def render_portfolio_metrics(overview_data: Dict[str, Any]):
        """포트폴리오 메트릭 렌더링"""
        MetricComponents.create_portfolio_metrics(overview_data)

    @staticmethod
    def render_portfolio_charts(overview_data: Dict[str, Any]):
        """포트폴리오 차트 렌더링"""
        if not overview_data:
            return

        col1, col2 = st.columns(2)

        with col1:
            # 자산 구조 차트
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
            # 투자자산 분배 차트
            investment_allocations = overview_data.get("investment_allocations", [])

            if investment_allocations:
                investment_chart = ChartComponents.create_investment_allocation_chart(
                    investment_allocations
                )
                ChartComponents.render_chart(investment_chart)

                # 상위 3개 투자자산 요약
                from ..models import AssetAllocation, DataFrameConverter
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
    def render_quick_actions():
        """빠른 액션 렌더링"""
        st.subheader("⚡ 빠른 액션")

        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("🔄 데이터 새로고침", use_container_width=True):
                from ..utils import StateManager
                StateManager.clear_all_cache()
                st.success("캐시가 초기화되었습니다!")
                st.rerun()

        with col2:
            if st.button("📊 상세 분석", use_container_width=True):
                from ..utils import StateManager, PageType
                StateManager.navigate_to_page(PageType.HOLDINGS)

        with col3:
            if st.button("💰 현금 관리", use_container_width=True):
                from ..utils import StateManager, PageType
                StateManager.navigate_to_page(PageType.CASH_MANAGEMENT)

    @staticmethod
    def render_market_summary():
        """시장 요약 렌더링"""
        st.subheader("📈 시장 요약")

        # 여기에 시장 관련 요약 정보를 추가할 수 있습니다.
        # 예: 주요 지수, 환율 등

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**주요 지수**")
            # KOSPI, S&P 500 등 시장 지수 표시 (placeholder)
            st.info("📊 KOSPI: 2,501.32 (+0.82%)")
            st.info("📈 S&P 500: 4,512.58 (+0.45%)")

        with col2:
            st.markdown("**주요 통화**")
            # 주요 통화 환율 표시 (placeholder)
            st.info("💵 USD/KRW: 1,342.50 (+0.15%)")
            st.info("💶 EUR/KRW: 1,462.80 (-0.22%)")

    @staticmethod
    def render_recent_activity():
        """최근 활동 렌더링"""
        st.subheader("📝 최근 활동")

        # 여기에 최근 거래나 활동 내역을 추가할 수 있습니다.
        # 현재는 placeholder로 대체
        activities = [
            {"날짜": "2024-10-20", "활동": "삼성전자 매수", "금액": "₩5,000,000"},
            {"날짜": "2024-10-19", "활동": "현금 입금", "금액": "₩2,000,000"},
            {"날짜": "2024-10-18", "활동": "TDF 매수", "금액": "₩1,000,000"},
        ]

        if activities:
            import pandas as pd
            df = pd.DataFrame(activities)
            LayoutComponents.create_data_table(
                df,
                column_config={
                    "날짜": "날짜",
                    "활동": "활동 내용",
                    "금액": "금액"
                }
            )
        else:
            LayoutComponents.create_empty_state("최근 활동 내역이 없습니다.")

    @staticmethod
    def render():
        """포트폴리오 개요 페이지 렌더링"""
        # 데이터 조회
        overview_data = PortfolioOverviewPage.fetch_portfolio_data()

        if overview_data:
            # 메트릭 표시
            PortfolioOverviewPage.render_portfolio_metrics(overview_data)

            st.markdown("---")

            # 차트 표시
            PortfolioOverviewPage.render_portfolio_charts(overview_data)

            st.markdown("---")

            # 빠른 액션
            PortfolioOverviewPage.render_quick_actions()

            st.markdown("---")

            # 추가 정보 탭
            tab1, tab2, tab3 = st.tabs(["📈 시장 요약", "📝 최근 활동", "📋 상세 정보"])

            with tab1:
                PortfolioOverviewPage.render_market_summary()

            with tab2:
                PortfolioOverviewPage.render_recent_activity()

            with tab3:
                st.markdown("**포트폴리오 상세 정보**")

                # 상세 정보 표시
                detail_data = {
                    "항목": [
                        "총 자산 (KRW)",
                        "총 자산 (USD)",
                        "총 평가손익 (KRW)",
                        "총 수익률",
                        "현금성자산",
                        "투자자산",
                        "업데이트 시간"
                    ],
                    "값": [
                        format_currency(overview_data.get("total_value_krw", 0)),
                        format_currency(overview_data.get("total_value_usd", 0), "USD"),
                        format_currency(overview_data.get("total_pnl_krw", 0)),
                        f"{overview_data.get('total_return_rate', 0):.2f}%",
                        format_currency(overview_data.get("cash_asset_value", 0)),
                        format_currency(overview_data.get("investment_asset_value", 0)),
                        overview_data.get("updated_at", "N/A")
                    ]
                }

                import pandas as pd
                df = pd.DataFrame(detail_data)
                LayoutComponents.create_data_table(df, hide_index=True)

        else:
            LayoutComponents.create_warning_box(
                "데이터 로딩 실패",
                "포트폴리오 데이터를 불러올 수 없습니다. API 서버가 실행 중인지 확인해주세요.",
                "⚠️"
            )