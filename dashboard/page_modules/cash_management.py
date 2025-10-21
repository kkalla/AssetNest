"""
현금 관리 페이지
"""
import pandas as pd
import streamlit as st
from typing import Dict, Any, Optional, List
from datetime import datetime, date

from dashboard.api import cash_api
from dashboard.components import MetricComponents, ChartComponents, LayoutComponents, FormComponents
from dashboard.models import CashBalance, TimeDeposit, DataFrameConverter
from dashboard.utils import cache_with_ttl, format_currency, format_percentage, StateManager


class CashManagementPage:
    """현금 관리 페이지 클래스"""

    @staticmethod
    @cache_with_ttl(ttl_seconds=300)
    def fetch_cash_summary() -> Optional[Dict[str, Any]]:
        """현금 관리 요약 정보 조회"""
        try:
            from logger import data_logger
            data_logger.info("💰 현금 관리 요약 정보 조회 시작")

            data = cash_api.get_summary()

            if data:
                data_logger.info("✅ 현금 관리 요약 정보 조회 성공")
            return data
        except Exception as e:
            from logger import data_logger
            data_logger.error(f"💥 현금 관리 요약 조회 실패: {str(e)}")
            st.error(f"현금 관리 요약 조회 중 오류가 발생했습니다: {e}")
            return None

    @staticmethod
    @cache_with_ttl(ttl_seconds=300)
    def fetch_cash_balances(account: Optional[str] = None) -> Optional[List[Dict[str, Any]]]:
        """증권사별 예수금 정보 조회"""
        try:
            from logger import data_logger
            data_logger.info(f"💰 증권사별 예수금 정보 조회 시작 - 계정: {account or '전체'}")

            balances = cash_api.get_balances(account)

            if balances:
                data_logger.info("✅ 증권사별 예수금 정보 조회 성공")
            return balances
        except Exception as e:
            from logger import data_logger
            data_logger.error(f"💥 증권사별 예수금 조회 실패: {str(e)}")
            st.error(f"증권사별 예수금 조회 중 오류가 발생했습니다: {e}")
            return []

    @staticmethod
    @cache_with_ttl(ttl_seconds=300)
    def fetch_time_deposits(account: Optional[str] = None) -> Optional[List[Dict[str, Any]]]:
        """예적금 정보 조회"""
        try:
            from logger import data_logger
            data_logger.info(f"💰 예적금 정보 조회 시작 - 계정: {account or '전체'}")

            deposits = cash_api.get_time_deposits(account)

            if deposits:
                data_logger.info("✅ 예적금 정보 조회 성공")
            return deposits
        except Exception as e:
            from logger import data_logger
            data_logger.error(f"💥 예적금 조회 실패: {str(e)}")
            st.error(f"예적금 조회 중 오류가 발생했습니다: {e}")
            return []

    @staticmethod
    def render_cash_summary_metrics(cash_summary: Dict[str, Any]):
        """현금 요약 메트릭 렌더링"""
        MetricComponents.create_cash_summary_metrics(cash_summary)

    @staticmethod
    def render_current_cash_management(cash_summary: Dict[str, Any]):
        """현재 현금 관리 렌더링"""
        st.subheader("📈 현재 현금 관리")

        latest_bs = cash_summary.get("latest_bs_entry")

        if latest_bs:
            # 현재 현금 정보 표시
            st.info(f"최신 업데이트: {latest_bs.get('date', 'N/A')}")

            MetricComponents.create_current_cash_metrics(latest_bs)

            # 현금 업데이트 섹션
            st.subheader("💸 현재 현금 업데이트")

            form_data = FormComponents.create_current_cash_update_form(latest_bs.get("cash", 0))

            if st.button("💰 현재 현금 업데이트", type="primary", use_container_width=True):
                if cash_api.update_current_cash(form_data["cash"], form_data["reason"]):
                    StateManager.clear_all_cache()
                    st.success("현재 현금이 성공적으로 업데이트되었습니다!")
                    st.rerun()

            # 현금 흐름 정보
            CashManagementPage.render_cash_flow_chart()

            # 합계 계산
            total_cash = (
                latest_bs.get("cash", 0) +
                latest_bs.get("time_deposit", 0) +
                latest_bs.get("security_cash_balance", 0)
            )
            st.metric("총 현금성자산", format_currency(total_cash))
        else:
            LayoutComponents.create_warning_box(
                "데이터 없음",
                "bs_timeseries 데이터가 없습니다. 먼저 현금을 업데이트해주세요.",
                "⚠️"
            )

    @staticmethod
    def render_cash_flow_chart():
        """현금 흐름 차트 렌더링"""
        st.subheader("📊 현금 흐름 분석")

        # 최근 7일간 추이 (데이터가 있다면)
        st.info("📈 최근 현금 변동 추이 (구현 예정)")

        # 차트 영역 (placeholder)
        chart_placeholder = pd.DataFrame({
            "날짜": [
                "2024-10-11", "2024-10-12", "2024-10-13",
                "2024-10-14", "2024-10-15", "2024-10-16", "2024-10-17",
            ],
            "현금": [28000000, 28500000, 29264236, 28500000, 29000000, 29200000, 29264236],
            "예적금": [17610000, 17610000, 17610000, 17610000, 17610000, 17610000, 17610000],
        })

        cash_flow_chart = ChartComponents.create_cash_flow_chart(chart_placeholder)
        ChartComponents.render_chart(cash_flow_chart)

    @staticmethod
    def render_cash_balances_management():
        """증권사별 예수금 관리 렌더링"""
        st.subheader("💳 증권사별 예수금 관리")

        # 예수금 데이터 조회
        cash_balances_data = CashManagementPage.fetch_cash_balances()

        if cash_balances_data:
            st.info(f"📋 현재 {len(cash_balances_data)}개 증권사 계좌의 예수금 정보")

            # 데이터 모델로 변환
            balance_models = [CashBalance.from_dict(b) for b in cash_balances_data]

            # 데이터프레임 생성
            balances_df = DataFrameConverter.cash_balances_to_dataframe(balance_models)

            if not balances_df.empty:
                # 데이터 테이블
                column_config = {
                    "account": "증권사",
                    "krw_formatted": "KRW 예수금",
                    "usd_formatted": "USD 예수금",
                    "total_krw": "총액 (KRW)"
                }

                LayoutComponents.create_data_table(
                    balances_df[["account", "krw_formatted", "usd_formatted", "total_krw"]],
                    column_config=column_config,
                    hide_index=True
                )

                # 예수금 업데이트 섹션
                CashManagementPage.render_cash_balance_update_form(cash_balances_data)
        else:
            LayoutComponents.create_empty_state("예수금 정보가 없습니다.")

    @staticmethod
    def render_cash_balance_update_form(cash_balances_data: List[Dict[str, Any]]):
        """예수금 업데이트 폼 렌더링"""
        st.subheader("✏️ 예수금 업데이트")

        if cash_balances_data:
            # 계좌 선택
            account_options = [cb["account"] for cb in cash_balances_data]
            selected_balance_account = st.selectbox(
                "업데이트할 계좌 선택",
                options=account_options,
                index=0
            )

            # 선택된 계좌의 현재 정보
            current_balance = next(
                (cb for cb in cash_balances_data if cb["account"] == selected_balance_account),
                None
            )

            if current_balance:
                form_data = FormComponents.create_cash_update_form(current_balance, selected_balance_account)

                if st.button("💾 예수금 업데이트", use_container_width=True):
                    if cash_api.update_balance(
                        selected_balance_account,
                        form_data["krw"],
                        form_data["usd"]
                    ):
                        StateManager.clear_all_cache()
                        st.success(f"{selected_balance_account} 계좌의 예수금이 성공적으로 업데이트되었습니다!")
                        st.rerun()

    @staticmethod
    def render_time_deposits_management():
        """예적금 관리 렌더링"""
        st.subheader("💎 예적금 관리")

        # 예적금 데이터 조회
        time_deposits_data = CashManagementPage.fetch_time_deposits()

        if time_deposits_data:
            st.info(f"📋 현재 {len(time_deposits_data)}개 예적금 정보")

            # 데이터 모델로 변환
            deposit_models = [TimeDeposit.from_dict(d) for d in time_deposits_data]

            # 데이터프레임 생성
            deposits_df = DataFrameConverter.time_deposits_to_dataframe(deposit_models)

            if not deposits_df.empty:
                # 데이터 테이블
                column_config = {
                    "account": "계좌",
                    "invest_prod_name": "상품명",
                    "market_value_formatted": "현재 평가액",
                    "invested_principal_formatted": "예치원금",
                    "maturity_date_formatted": "만기일",
                    "interest_rate_formatted": "이율"
                }

                LayoutComponents.create_data_table(
                    deposits_df[[
                        "account", "invest_prod_name", "market_value_formatted",
                        "invested_principal_formatted", "maturity_date_formatted", "interest_rate_formatted"
                    ]],
                    column_config=column_config,
                    hide_index=True
                )

                # 예적금 관리 섹션
                CashManagementPage.render_time_deposit_management_form(time_deposits_data)
        else:
            LayoutComponents.create_empty_state("예적금 정보가 없습니다.")

    @staticmethod
    def render_time_deposit_management_form(time_deposits_data: List[Dict[str, Any]]):
        """예적금 관리 폼 렌더링"""
        st.subheader("⚙️ 예적금 관리")

        operation = st.selectbox(
            "작업 선택",
            ["예적금 추가", "예적금 수정", "예적금 삭제"]
        )

        if operation == "예적금 추가":
            CashManagementPage.render_create_time_deposit_form()

        elif operation == "예적금 수정":
            CashManagementPage.render_edit_time_deposit_form(time_deposits_data)

        elif operation == "예적금 삭제":
            CashManagementPage.render_delete_time_deposit_form(time_deposits_data)

    @staticmethod
    def render_create_time_deposit_form():
        """예적금 생성 폼 렌더링"""
        st.subheader("➕ 새 예적금 추가")

        form_data = FormComponents.create_time_deposit_form("create")

        if form_data:
            if cash_api.create_time_deposit(
                form_data["account"],
                form_data["invest_prod_name"],
                form_data["market_value"],
                form_data["invested_principal"],
                form_data["maturity_date"],
                form_data["interest_rate"]
            ):
                StateManager.clear_all_cache()
                st.success("예적금이 성공적으로 생성되었습니다!")
                st.rerun()

    @staticmethod
    def render_edit_time_deposit_form(time_deposits_data: List[Dict[str, Any]]):
        """예적금 수정 폼 렌더링"""
        st.subheader("✏️ 예적금 수정")

        if time_deposits_data:
            # 수정할 예적금 선택
            deposit_options = [
                f"{td['account']} - {td['invest_prod_name']}" for td in time_deposits_data
            ]
            deposit_to_edit = st.selectbox("수정할 예적금 선택", options=deposit_options)

            if deposit_to_edit:
                # 선택된 예적금 정보 파싱
                selected_deposit = next(
                    (td for td in time_deposits_data
                     if f"{td['account']} - {td['invest_prod_name']}" == deposit_to_edit),
                    None
                )

                if selected_deposit:
                    form_data = FormComponents.create_time_deposit_form("edit", selected_deposit)

                    if form_data:
                        if cash_api.update_time_deposit(
                            form_data["account"],
                            form_data["invest_prod_name"],
                            form_data["market_value"],
                            form_data["invested_principal"],
                            form_data["maturity_date"],
                            form_data["interest_rate"]
                        ):
                            StateManager.clear_all_cache()
                            st.success("예적금이 성공적으로 수정되었습니다!")
                            st.rerun()

    @staticmethod
    def render_delete_time_deposit_form(time_deposits_data: List[Dict[str, Any]]):
        """예적금 삭제 폼 렌더링"""
        st.subheader("🗑️ 예적금 삭제")

        if time_deposits_data:
            deposit_options = [
                f"{td['account']} - {td['invest_prod_name']}" for td in time_deposits_data
            ]
            deposit_to_delete = st.selectbox("삭제할 예적금 선택", options=deposit_options)

            if deposit_to_delete:
                # 선택된 예적금 정보 파싱
                parts = deposit_to_delete.split(" - ", 1)
                account, prod_name = parts[0], parts[1]

                if FormComponents.create_delete_confirmation(deposit_to_delete, "예적금"):
                    if cash_api.delete_time_deposit(account, prod_name):
                        StateManager.clear_all_cache()
                        st.success("예적금이 성공적으로 삭제되었습니다!")
                        st.rerun()

    @staticmethod
    def render():
        """현금 관리 페이지 렌더링"""
        # 데이터 조회
        cash_summary = CashManagementPage.fetch_cash_summary()

        if cash_summary:
            # 전체 현금 상태 요약
            st.subheader("📊 전체 현금 현황")
            CashManagementPage.render_cash_summary_metrics(cash_summary)

            st.markdown("---")

            # 탭으로 기능 분리
            tab1, tab2, tab3 = st.tabs([
                "💳 증권사 예수금", "💎 예적금 관리", "📈 현재 현금 관리"
            ])

            with tab1:
                CashManagementPage.render_cash_balances_management()

            with tab2:
                CashManagementPage.render_time_deposits_management()

            with tab3:
                CashManagementPage.render_current_cash_management(cash_summary)

        else:
            LayoutComponents.create_warning_box(
                "데이터 로딩 실패",
                "현금 관리 데이터를 불러올 수 없습니다. API 서버가 실행 중인지 확인해주세요.",
                "⚠️"
            )