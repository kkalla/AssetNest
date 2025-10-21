"""
보유 종목 페이지
"""
import pandas as pd
import streamlit as st
from typing import Dict, Any, Optional, List

from dashboard.api import holdings_api
from dashboard.components import MetricComponents, LayoutComponents
from dashboard.models import HoldingData, DataFrameConverter
from dashboard.utils import cache_with_ttl, format_currency, format_percentage, StateManager


class HoldingsPage:
    """보유 종목 페이지 클래스"""

    @staticmethod
    @cache_with_ttl(ttl_seconds=300)
    def fetch_holdings_data(
        account: Optional[str] = None,
        market: Optional[str] = None
    ) -> Optional[List[Dict[str, Any]]]:
        """보유 종목 데이터 조회"""
        try:
            from logger import data_logger
            data_logger.info(
                f"📋 보유 종목 데이터 조회 시작 - 계정: {account or '전체'}, 시장: {market or '전체'}"
            )

            holdings = holdings_api.get_holdings(account, market)

            if holdings:
                data_logger.info(f"✅ 보유 종목 데이터 조회 성공 - {len(holdings)}개 종목")
            return holdings
        except Exception as e:
            from logger import data_logger
            data_logger.error(f"💥 보유 종목 조회 실패: {str(e)}")
            st.error(f"보유 종목 조회 중 오류가 발생했습니다: {e}")
            return []

    @staticmethod
    def render_filters() -> Dict[str, Any]:
        """필터 섹션 렌더링"""
        filters = {
            "min_value": {
                "type": "number",
                "label": "최소 평가금액 (만원)",
                "default": StateManager.get_filter("holdings", "min_value", 0),
                "min": 0,
                "step": 100
            },
            "min_return": {
                "type": "number",
                "label": "최소 수익률 (%)",
                "default": StateManager.get_filter("holdings", "min_return", -100.0),
                "min": -100.0,
                "max": 1000.0,
                "step": 1.0
            },
            "max_return": {
                "type": "number",
                "label": "최대 수익률 (%)",
                "default": StateManager.get_filter("holdings", "max_return", 1000.0),
                "min": -100.0,
                "max": 1000.0,
                "step": 1.0
            }
        }

        filtered_values = LayoutComponents.create_filter_section("상세 필터", filters)

        # 필터 값 저장
        for key, value in filtered_values.items():
            StateManager.update_filter("holdings", key, value)

        return filtered_values

    @staticmethod
    def apply_filters(
        holdings: List[Dict[str, Any]],
        filters: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """필터 적용"""
        if not holdings:
            return []

        min_value = filters.get("min_value", 0) * 10000  # 만원 → 원
        min_return = filters.get("min_return", -100.0)
        max_return = filters.get("max_return", 1000.0)

        filtered_holdings = []
        for holding in holdings:
            market_value = holding.get("market_value", 0)
            return_rate = holding.get("return_rate", 0)

            if (market_value >= min_value and
                min_return <= return_rate <= max_return):
                filtered_holdings.append(holding)

        return filtered_holdings

    @staticmethod
    def render_summary_metrics(holdings: List[Dict[str, Any]]):
        """요약 메트릭 렌더링"""
        MetricComponents.create_holdings_summary_metrics(holdings)

    @staticmethod
    def render_holdings_table(holdings: List[Dict[str, Any]]):
        """보유 종목 테이블 렌더링"""
        if not holdings:
            LayoutComponents.create_empty_state("선택한 조건에 해당하는 보유 종목이 없습니다.")
            return

        # 데이터 모델로 변환
        holding_models = [HoldingData.from_dict(h) for h in holdings]

        # 데이터프레임으로 변환
        df = DataFrameConverter.holdings_to_dataframe(holding_models)

        if df.empty:
            LayoutComponents.create_empty_state("데이터를 변환할 수 없습니다.")
            return

        # 표시용 데이터 포맷팅
        display_df = df.copy()
        display_df["avg_price_krw"] = display_df["avg_price_krw"].apply(format_currency)
        display_df["current_price_krw"] = display_df["current_price_krw"].apply(format_currency)
        display_df["market_value"] = display_df["market_value"].apply(format_currency)
        display_df["unrealized_pnl"] = display_df["unrealized_pnl"].apply(format_currency)
        display_df["return_rate"] = display_df["return_rate"].apply(format_percentage)

        # 컬럼 설정
        column_config = {
            "company": "종목명",
            "account": "계좌",
            "market": "지역",
            "amount": "보유수량",
            "avg_price_krw": "평균단가",
            "current_price_krw": "현재가",
            "market_value": "평가금액",
            "unrealized_pnl": "평가손익",
            "return_rate": "수익률"
        }

        # 데이터 테이블 표시
        LayoutComponents.create_data_table(
            display_df,
            column_config=column_config,
            width="stretch"
        )

    @staticmethod
    def render_top_performers(holdings: List[Dict[str, Any]]):
        """상위/하위 퍼포머 렌더링"""
        if len(holdings) < 2:
            return

        st.subheader("🏆 수익률 순위")

        # 수익률 기준 정렬
        sorted_holdings = sorted(holdings, key=lambda x: x.get("return_rate", 0), reverse=True)

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**📈 상위 퍼포머 (Top 5)**")
            top_performers = sorted_holdings[:5]

            for i, holding in enumerate(top_performers, 1):
                company = holding.get("company", "Unknown")
                return_rate = holding.get("return_rate", 0)
                market_value = holding.get("market_value", 0)

                st.metric(
                    label=f"{i}. {company}",
                    value=format_percentage(return_rate),
                    delta=format_currency(market_value)
                )

        with col2:
            st.markdown("**📉 하위 퍼포머 (Bottom 5)**")
            bottom_performers = sorted_holdings[-5:] if len(sorted_holdings) > 5 else sorted_holdings

            for i, holding in enumerate(reversed(bottom_performers), 1):
                company = holding.get("company", "Unknown")
                return_rate = holding.get("return_rate", 0)
                market_value = holding.get("market_value", 0)

                st.metric(
                    label=f"{i}. {company}",
                    value=format_percentage(return_rate),
                    delta=format_currency(market_value),
                    delta_color="inverse" if return_rate < 0 else "normal"
                )

    @staticmethod
    def render_sector_analysis(holdings: List[Dict[str, Any]]):
        """섹터별 분석 렌더링"""
        if not holdings:
            return

        st.subheader("📊 섹터별 분석")

        # 계좌별 집계
        account_summary = {}
        for holding in holdings:
            account = holding.get("account", "Unknown")
            market_value = holding.get("market_value", 0)
            pnl = holding.get("unrealized_pnl", 0)

            if account not in account_summary:
                account_summary[account] = {
                    "total_value": 0,
                    "total_pnl": 0,
                    "count": 0
                }

            account_summary[account]["total_value"] += market_value
            account_summary[account]["total_pnl"] += pnl
            account_summary[account]["count"] += 1

        if account_summary:
            # 데이터프레임 생성
            summary_data = []
            for account, data in account_summary.items():
                return_rate = (data["total_pnl"] / data["total_value"] * 100) if data["total_value"] > 0 else 0
                summary_data.append({
                    "계좌": account,
                    "보유종목수": data["count"],
                    "총 평가금액": data["total_value"],
                    "총 평가손익": data["total_pnl"],
                    "수익률": return_rate
                })

            df = pd.DataFrame(summary_data)

            # 정렬
            df = df.sort_values("총 평가금액", ascending=False)

            # 포맷팅
            display_df = df.copy()
            display_df["총 평가금액"] = display_df["총 평가금액"].apply(format_currency)
            display_df["총 평가손익"] = display_df["총 평가손익"].apply(format_currency)
            display_df["수익률"] = display_df["수익률"].apply(format_percentage)

            # 컬럼 설정
            column_config = {
                "계좌": "계좌명",
                "보유종목수": "보유종목수",
                "총 평가금액": "총 평가금액",
                "총 평가손익": "총 평가손익",
                "수익률": "수익률"
            }

            LayoutComponents.create_data_table(
                display_df,
                column_config=column_config,
                hide_index=True
            )

    @staticmethod
    def render_export_options(holdings: List[Dict[str, Any]]):
        """내보내기 옵션 렌더링"""
        st.subheader("📤 내보내기")

        col1, col2 = st.columns(2)

        with col1:
            if st.button("📊 Excel로 내보내기", use_container_width=True):
                if holdings:
                    try:
                        # 데이터프레임 생성
                        holding_models = [HoldingData.from_dict(h) for h in holdings]
                        df = DataFrameConverter.holdings_to_dataframe(holding_models)

                        # 엑셀 파일 생성 (간단한 CSV 다운로드로 대체)
                        csv = df.to_csv(index=False, encoding='utf-8-sig')
                        st.download_button(
                            label="💾 CSV 다운로드",
                            data=csv,
                            file_name="holdings_data.csv",
                            mime="text/csv"
                        )
                    except Exception as e:
                        st.error(f"내보내기 실패: {e}")
                else:
                    st.warning("내보낼 데이터가 없습니다.")

        with col2:
            if st.button("📈 리포트 생성", use_container_width=True):
                st.info("리포트 생성 기능은 준비 중입니다.")

    @staticmethod
    def render():
        """보유 종목 페이지 렌더링"""
        # 데이터 조회
        holdings_data = HoldingsPage.fetch_holdings_data()

        if not holdings_data:
            LayoutComponents.create_warning_box(
                "데이터 로딩 실패",
                "보유 종목 데이터를 불러올 수 없습니다. API 서버가 실행 중인지 확인해주세요.",
                "⚠️"
            )
            return

        # 필터 섹션
        filters = HoldingsPage.render_filters()

        # 필터 적용
        filtered_holdings = HoldingsPage.apply_filters(holdings_data, filters)

        # 요약 메트릭
        HoldingsPage.render_summary_metrics(filtered_holdings)

        st.markdown("---")

        # 보유 종목 테이블
        st.subheader(f"📊 보유 종목 상세 ({len(filtered_holdings)}개)")
        HoldingsPage.render_holdings_table(filtered_holdings)

        if filtered_holdings:
            st.markdown("---")

            # 추가 분석 탭
            tab1, tab2, tab3 = st.tabs(["🏆 수익률 순위", "📊 섹터별 분석", "📤 내보내기"])

            with tab1:
                HoldingsPage.render_top_performers(filtered_holdings)

            with tab2:
                HoldingsPage.render_sector_analysis(filtered_holdings)

            with tab3:
                HoldingsPage.render_export_options(filtered_holdings)