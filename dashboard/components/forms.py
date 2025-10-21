"""
폼 컴포넌트
"""
import streamlit as st
from typing import List, Dict, Any, Optional, Callable
from datetime import datetime, date

from dashboard.config import settings
from dashboard.utils import StateManager


class FormComponents:
    """폼 컴포넌트 클래스"""

    @staticmethod
    def create_filter_section(title: str, filters: Dict[str, Any]):
        """
        필터 섹션 생성

        Args:
            title (str): 섹션 제목
            filters (Dict[str, Any]): 필터 설정

        Returns:
            Dict[str, Any]: 필터링된 값들
        """
        st.subheader(f"🔍 {title}")

        col_count = len(filters)
        cols = st.columns(col_count)

        filtered_values = {}
        for i, (key, config) in enumerate(filters.items()):
            with cols[i]:
                filter_type = config.get("type", "number")
                label = config.get("label", key)
                default_value = config.get("default", 0)

                if filter_type == "number":
                    min_val = config.get("min", 0)
                    max_val = config.get("max", 1000000)
                    step = config.get("step", 1)
                    filtered_values[key] = st.number_input(
                        label=label,
                        value=default_value,
                        min_value=min_val,
                        max_value=max_val,
                        step=step
                    )
                elif filter_type == "selectbox":
                    options = config.get("options", [])
                    filtered_values[key] = st.selectbox(
                        label=label,
                        options=options,
                        index=default_value if isinstance(default_value, int) else 0
                    )
                elif filter_type == "multiselect":
                    options = config.get("options", [])
                    filtered_values[key] = st.multiselect(
                        label=label,
                        options=options,
                        default=default_value if isinstance(default_value, list) else []
                    )

        return filtered_values

    @staticmethod
    def create_cash_update_form(current_balance: Dict[str, float], account: str) -> Dict[str, Any]:
        """
        현금 업데이트 폼 생성

        Args:
            current_balance (Dict[str, float]): 현재 잔고
            account (str): 계좌명

        Returns:
            Dict[str, Any]: 폼 데이터
        """
        st.subheader(f"✏️ {account} 계좌 현금 수정")

        col1, col2 = st.columns(2)

        with col1:
            st.info(f"현재 {account} 계좌")
            st.metric("KRW", f"₩{current_balance.get('krw', 0):,.0f}")
            st.metric("USD", f"${current_balance.get('usd', 0):,.2f}")

        with col2:
            st.write("새로운 금액 입력")
            new_krw = st.number_input(
                "새 KRW 예수금",
                value=float(current_balance.get("krw", 0)),
                min_value=0.0,
                format="%.0f",
                step=1000.0,
                key=f"new_krw_{account}"
            )
            new_usd = st.number_input(
                "새 USD 예수금",
                value=float(current_balance.get("usd", 0)),
                min_value=0.0,
                format="%.2f",
                step=0.01,
                key=f"new_usd_{account}"
            )

        return {
            "account": account,
            "krw": new_krw,
            "usd": new_usd
        }

    @staticmethod
    def create_time_deposit_form(
        mode: str = "create",
        default_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        예적금 폼 생성

        Args:
            mode (str): 모드 ("create", "edit")
            default_data (Optional[Dict[str, Any]]): 기본 데이터

        Returns:
            Dict[str, Any]: 폼 데이터
        """
        if mode == "create":
            st.subheader("➕ 새 예적금 추가")
        else:
            st.subheader("✏️ 예적금 수정")

        with st.form(f"time_deposit_form_{mode}"):
            # 계정명
            account = st.text_input(
                "계정명",
                value=default_data.get("account", "") if default_data else "",
                disabled=mode == "edit"
            )

            # 상품명
            prod_name = st.text_input(
                "상품명",
                value=default_data.get("invest_prod_name", "") if default_data else "",
                disabled=mode == "edit"
            )

            # 금액 정보
            col1, col2 = st.columns(2)
            with col1:
                market_value = st.number_input(
                    "현재 평가액",
                    min_value=0,
                    value=default_data.get("market_value", 1000000) if default_data else 1000000,
                    step=10000
                )
            with col2:
                invested_principal = st.number_input(
                    "예치원금",
                    min_value=0,
                    value=default_data.get("invested_principal", 1000000) if default_data else 1000000,
                    step=10000
                )

            # 선택적 정보
            col1, col2 = st.columns(2)
            with col1:
                maturity_date = st.date_input(
                    "만기일 (선택사)",
                    value=(
                        datetime.strptime(default_data.get("maturity_date"), "%Y-%m-%d").date()
                        if default_data and default_data.get("maturity_date")
                        else date.today()
                    )
                )
            with col2:
                interest_rate = st.number_input(
                    "이율 (%)",
                    min_value=0.0,
                    max_value=20.0,
                    value=default_data.get("interest_rate", 0.0) if default_data else 0.0,
                    step=0.1
                )

            submitted = st.form_submit_button(
                f"💾 예적금 {'생성' if mode == 'create' else '수정'}",
                use_container_width=True
            )

            if submitted:
                form_data = {
                    "account": account,
                    "invest_prod_name": prod_name,
                    "market_value": market_value,
                    "invested_principal": invested_principal,
                    "maturity_date": maturity_date,
                    "interest_rate": interest_rate
                }

                # 유효성 검사
                if not account or not prod_name:
                    st.error("계정명과 상품명은 필수 항목입니다.")
                    return None

                if market_value <= 0 or invested_principal <= 0:
                    st.error("평가액과 예치원금은 0보다 커야 합니다.")
                    return None

                return form_data

        return None

    @staticmethod
    def create_current_cash_update_form(current_cash: float) -> Dict[str, Any]:
        """
        현재 현금 업데이트 폼 생성

        Args:
            current_cash (float): 현재 현금

        Returns:
            Dict[str, Any]: 폼 데이터
        """
        st.subheader("💸 현재 현금 업데이트")

        col1, col2 = st.columns(2)

        with col1:
            new_cash = int(
                st.number_input(
                    "새 현금 금액",
                    min_value=0,
                    value=int(current_cash),
                    step=10000,
                    format="%d"
                )
            )

        with col2:
            reason = st.text_input(
                "변경 사유 (선택사)",
                placeholder="예: 월급 입금"
            )

        return {
            "cash": new_cash,
            "reason": reason
        }

    @staticmethod
    def create_asset_allocation_simulator(
        current_data: Dict[str, Any],
        asset_types: List[str],
        default_ratios: Optional[Dict[str, float]] = None
    ) -> Dict[str, Any]:
        """
        자산 분배 시뮬레이터 폼 생성

        Args:
            current_data (Dict[str, Any]): 현재 데이터
            asset_types (List[str]): 자산유형 리스트
            default_ratios (Optional[Dict[str, float]]): 기본 비율

        Returns:
            Dict[str, Any]: 시뮬레이션 데이터
        """
        if default_ratios is None:
            default_ratios = settings.DEFAULT_ASSET_ALLOCATION

        target_ratios = {}
        cols = st.columns(min(3, len(asset_types)))

        st.markdown("##### 목표 비율 설정")

        for idx, asset_type in enumerate(asset_types):
            col_idx = idx % min(3, len(asset_types))
            with cols[col_idx]:
                default_value = default_ratios.get(asset_type, 0)
                target_ratios[asset_type] = st.number_input(
                    f"{asset_type} (%)",
                    min_value=0,
                    max_value=100,
                    value=default_value,
                    step=1,
                    key=f"ratio_{asset_type}"
                )

        # 합계 검증
        total_ratio = sum(target_ratios.values())
        ratio_diff = abs(total_ratio - 100)

        if ratio_diff == 0:
            st.success(f"✅ 비율 합계: {total_ratio:.0f}% (정상)")
            is_valid = True
        else:
            st.warning(
                f"⚠️ 비율 합계: {total_ratio:.0f}% (100%가 되어야 합니다. 차이: {total_ratio - 100:.0f}%)"
            )
            is_valid = False

        return {
            "target_ratios": target_ratios,
            "total_ratio": total_ratio,
            "is_valid": is_valid,
            "current_data": current_data
        }

    @staticmethod
    def create_delete_confirmation(item_name: str, item_type: str = "항목") -> bool:
        """
        삭제 확인 폼 생성

        Args:
            item_name (str): 삭제할 항목명
            item_type (str): 항목 유형

        Returns:
            bool: 삭제 확인 여부
        """
        st.warning(f"⚠️ 정말로 삭제하시겠습니까? **{item_name}**")
        return st.button(f"🗑️ {item_type} 삭제", type="secondary")