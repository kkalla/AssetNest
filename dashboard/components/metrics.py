"""
메트릭 컴포넌트
"""
import streamlit as st
from typing import Optional, Union, Dict, Any

from dashboard.config import settings
from dashboard.utils import format_currency, format_percentage


class MetricComponents:
    """메트릭 컴포넌트 클래스"""

    @staticmethod
    def create_metric(
        label: str,
        value: Union[str, int, float],
        delta: Optional[Union[str, int, float]] = None,
        delta_color: str = "normal",
        help_text: Optional[str] = None
    ):
        """
        기본 메트릭 컴포넌트 생성

        Args:
            label (str): 메트릭 라벨
            value (Union[str, int, float]): 메트릭 값
            delta (Optional[Union[str, int, float]]): 변화량
            delta_color (str): 변화량 색상 ("normal", "inverse", "off")
            help_text (Optional[str]): 도움말 텍스트
        """
        if help_text:
            st.metric(label=label, value=value, delta=delta, delta_color=delta_color, help=help_text)
        else:
            st.metric(label=label, value=value, delta=delta, delta_color=delta_color)

    @staticmethod
    def create_currency_metric(
        label: str,
        amount: float,
        currency: str = "KRW",
        delta_amount: Optional[float] = None,
        delta_currency: Optional[str] = None,
        delta_color: str = "normal"
    ):
        """
        통화 메트릭 컴포넌트 생성

        Args:
            label (str): 메트릭 라벨
            amount (float): 금액
            currency (str): 통화 코드
            delta_amount (Optional[float]): 변화량
            delta_currency (Optional[str]): 변화량 통화
            delta_color (str): 변화량 색상
        """
        formatted_value = format_currency(amount, currency)
        formatted_delta = None
        if delta_amount is not None:
            delta_curr = delta_currency or currency
            formatted_delta = format_currency(delta_amount, delta_curr)

        MetricComponents.create_metric(
            label=label,
            value=formatted_value,
            delta=formatted_delta,
            delta_color=delta_color
        )

    @staticmethod
    def create_percentage_metric(
        label: str,
        percentage: float,
        delta_percentage: Optional[float] = None,
        delta_color: str = "normal",
        precision: int = 2
    ):
        """
        퍼센트 메트릭 컴포넌트 생성

        Args:
            label (str): 메트릭 라벨
            percentage (float): 퍼센트 값
            delta_percentage (Optional[float]): 변화량
            delta_color (str): 변화량 색상
            precision (int): 소수점 자릿수
        """
        formatted_value = format_percentage(percentage, precision)
        formatted_delta = None
        if delta_percentage is not None:
            formatted_delta = format_percentage(delta_percentage, precision)

        MetricComponents.create_metric(
            label=label,
            value=formatted_value,
            delta=formatted_delta,
            delta_color=delta_color
        )

    @staticmethod
    def create_portfolio_metrics(overview_data: Dict[str, Any], columns_count: int = 4):
        """
        포트폴리오 개요 메트릭들 생성

        Args:
            overview_data (Dict[str, Any]): 포트폴리오 개요 데이터
            columns_count (int): 컬럼 수
        """
        cols = st.columns(columns_count)

        with cols[0]:
            MetricComponents.create_currency_metric(
                label="총 자산 (KRW)",
                amount=overview_data.get("total_value_krw", 0),
                delta_amount=overview_data.get("total_pnl_krw", 0)
            )

        with cols[1]:
            MetricComponents.create_percentage_metric(
                label="총 수익률",
                percentage=overview_data.get("total_return_rate", 0),
                delta_percentage=overview_data.get("total_return_rate", 0)
            )

        with cols[2]:
            MetricComponents.create_currency_metric(
                label="평가손익 (KRW)",
                amount=overview_data.get("total_pnl_krw", 0),
                delta_amount=overview_data.get("total_pnl_krw", 0)
            )

        with cols[3]:
            MetricComponents.create_currency_metric(
                label="총 자산 (USD)",
                amount=overview_data.get("total_value_usd", 0),
                currency="USD",
                delta_amount=overview_data.get("total_pnl_usd", 0),
                delta_currency="USD"
            )

    @staticmethod
    def create_cash_summary_metrics(cash_summary: Dict[str, Any], columns_count: int = 4):
        """
        현금 요약 메트릭들 생성

        Args:
            cash_summary (Dict[str, Any]): 현금 요약 데이터
            columns_count (int): 컬럼 수
        """
        cols = st.columns(columns_count)

        with cols[0]:
            MetricComponents.create_currency_metric(
                label="총 현금성자산",
                amount=cash_summary.get("total_cash", 0)
            )

        with cols[1]:
            MetricComponents.create_currency_metric(
                label="총 현금",
                amount=cash_summary.get("total_cash_balance", 0)
            )

        with cols[2]:
            MetricComponents.create_currency_metric(
                label="총 예적금",
                amount=cash_summary.get("total_time_deposit", 0)
            )

        with cols[3]:
            MetricComponents.create_currency_metric(
                label="총 증권사 예수금",
                amount=cash_summary.get("total_security_cash", 0)
            )

    @staticmethod
    def create_holdings_summary_metrics(holdings_data: list, columns_count: int = 3):
        """
        보유 종목 요약 메트릭들 생성

        Args:
            holdings_data (list): 보유 종목 데이터
            columns_count (int): 컬럼 수
        """
        if not holdings_data:
            return

        cols = st.columns(columns_count)

        # 총 보유 종목 수
        with cols[0]:
            MetricComponents.create_metric(
                label="보유 종목 수",
                value=len(holdings_data)
            )

        # 총 평가금액
        total_value = sum(item.get("market_value", 0) for item in holdings_data)
        with cols[1]:
            MetricComponents.create_currency_metric(
                label="총 평가금액",
                amount=total_value
            )

        # 총 평가손익
        total_pnl = sum(item.get("unrealized_pnl", 0) for item in holdings_data)
        with cols[2]:
            MetricComponents.create_currency_metric(
                label="총 평가손익",
                amount=total_pnl,
                delta_amount=total_pnl
            )

    @staticmethod
    def create_current_cash_metrics(latest_bs: Dict[str, Any], columns_count: int = 3):
        """
        현재 현금 메트릭들 생성

        Args:
            latest_bs (Dict[str, Any]): 최신 현금 데이터
            columns_count (int): 컬럼 수
        """
        cols = st.columns(columns_count)

        with cols[0]:
            MetricComponents.create_currency_metric(
                label="현재 현금",
                amount=latest_bs.get("cash", 0)
            )

        with cols[1]:
            MetricComponents.create_currency_metric(
                label="예적금",
                amount=latest_bs.get("time_deposit", 0)
            )

        with cols[2]:
            MetricComponents.create_currency_metric(
                label="증권사 예수금",
                amount=latest_bs.get("security_cash_balance", 0)
            )

        # 총 현금성자산
        total_cash = (
            latest_bs.get("cash", 0) +
            latest_bs.get("time_deposit", 0) +
            latest_bs.get("security_cash_balance", 0)
        )
        st.metric("총 현금성자산", format_currency(total_cash))

    @staticmethod
    def create_simulation_metrics(
        current_values: Dict[str, float],
        target_values: Dict[str, float],
        adjustment_values: Dict[str, float],
        columns_count: int = 3
    ):
        """
        시뮬레이션 결과 메트릭들 생성

        Args:
            current_values (Dict[str, float]): 현재 값들
            target_values (Dict[str, float]): 목표 값들
            adjustment_values (Dict[str, float]): 조정 값들
            columns_count (int): 컬럼 수
        """
        cols = st.columns(columns_count)

        # 목표 비율
        with cols[0]:
            st.markdown("**목표 비율**")
            for key, target in target_values.items():
                current = current_values.get(key, 0)
                delta = target - current
                MetricComponents.create_percentage_metric(
                    label=key,
                    percentage=target,
                    delta_percentage=delta,
                    delta_color="normal" if delta >= 0 else "inverse"
                )

        # 목표 금액
        with cols[1]:
            st.markdown("**목표 금액**")
            for key, target in target_values.items():
                MetricComponents.create_currency_metric(
                    label=key,
                    amount=target
                )

        # 필요한 조정
        with cols[2]:
            st.markdown("**필요한 조정**")
            for key, adjustment in adjustment_values.items():
                if abs(adjustment) < 1000:
                    MetricComponents.create_metric(
                        label=key,
                        value="✅ 조정 불필요"
                    )
                else:
                    is_positive = adjustment > 0
                    action = "증가 필요" if is_positive else "감소 필요"
                    delta_color = "normal" if not is_positive else "inverse"
                    MetricComponents.create_currency_metric(
                        label=f"{key} {action}",
                        amount=abs(adjustment),
                        delta="매수 필요" if not is_positive else "매도 필요",
                        delta_color=delta_color
                    )