"""
차트 컴포넌트
"""
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st
from typing import List, Dict, Any, Optional

from dashboard.config import settings
from dashboard.models import AssetAllocation
from dashboard.utils import format_currency, format_percentage


class ChartComponents:
    """차트 컴포넌트 클래스"""

    @staticmethod
    def create_pie_chart(
        data: pd.DataFrame,
        values_col: str,
        names_col: str,
        title: str,
        color_sequence: Optional[List[str]] = None,
        hole: float = 0.3,
        height: Optional[int] = None
    ) -> go.Figure:
        """
        파이 차트 생성

        Args:
            data (pd.DataFrame): 데이터프레임
            values_col (str): 값 컬럼명
            names_col (str): 이름 컬럼명
            title (str): 차트 제목
            color_sequence (Optional[List[str]]): 색상 순서
            hole (float): 도넛 홀 크기
            height (Optional[int]): 차트 높이

        Returns:
            go.Figure: 파이 차트 객체
        """
        if color_sequence is None:
            color_sequence = settings.THEME_COLORS.values()

        fig = px.pie(
            data_frame=data,
            values=values_col,
            names=names_col,
            title=title,
            color_discrete_sequence=color_sequence[:len(data)],
            hole=hole
        )

        fig.update_traces(
            textposition="inside",
            textinfo="percent+label",
            hovertemplate="<b>%{label}</b><br>금액: ₩%{value:,.0f}<br>비중: %{percent}<extra></extra>"
        )

        fig.update_layout(
            height=height or settings.CHART_HEIGHT,
            showlegend=False,
            template=settings.CHART_TEMPLATE,
            paper_bgcolor="rgba(15, 23, 42, 0)",
            plot_bgcolor="rgba(15, 23, 42, 0)",
            font_color=settings.THEME_COLORS["text"]
        )

        return fig

    @staticmethod
    def create_bar_chart(
        data: pd.DataFrame,
        x_col: str,
        y_col: str,
        title: str,
        orientation: str = "v",
        color_col: Optional[str] = None,
        text_col: Optional[str] = None,
        height: Optional[int] = None
    ) -> go.Figure:
        """
        막대 차트 생성

        Args:
            data (pd.DataFrame): 데이터프레임
            x_col (str): X축 컬럼명
            y_col (str): Y축 컬럼명
            title (str): 차트 제목
            orientation (str): 차트 방향 ('v' 또는 'h')
            color_col (Optional[str]): 색상 컬럼명
            text_col (Optional[str]): 텍스트 컬럼명
            height (Optional[int]): 차트 높이

        Returns:
            go.Figure: 막대 차트 객체
        """
        color_sequence = list(settings.THEME_COLORS.values())

        if orientation == "h":
            fig = px.bar(
                data_frame=data.sort_values(y_col, ascending=True),
                x=y_col,
                y=x_col,
                orientation="h",
                title=title,
                color=color_col or x_col,
                color_discrete_sequence=color_sequence[:len(data)],
                text=text_col or y_col
            )
            fig.update_traces(texttemplate="%{text:.0f}%", textposition="inside")
            fig.update_xaxes(title_text="평가금액 (KRW)")
            fig.update_yaxes(title_text="자산유형")
        else:
            fig = px.bar(
                data_frame=data,
                x=x_col,
                y=y_col,
                title=title,
                color=color_col or x_col,
                color_discrete_sequence=color_sequence[:len(data)],
                text=text_col or y_col
            )
            fig.update_traces(texttemplate="%{text:.0f}%", textposition="inside")
            fig.update_xaxes(title_text="자산유형")
            fig.update_yaxes(title_text="평가금액 (KRW)")

        fig.update_layout(
            height=height or 500,
            showlegend=False,
            template=settings.CHART_TEMPLATE,
            paper_bgcolor="rgba(15, 23, 42, 0)",
            plot_bgcolor="rgba(15, 23, 42, 0)",
            font_color=settings.THEME_COLORS["text"],
            xaxis=dict(gridcolor="rgba(30, 41, 59, 0.5)", tickcolor=settings.THEME_COLORS["text"]),
            yaxis=dict(gridcolor="rgba(30, 41, 59, 0.5)", tickcolor=settings.THEME_COLORS["text"])
        )

        return fig

    @staticmethod
    def create_line_chart(
        data: pd.DataFrame,
        x_col: str,
        y_cols: List[str],
        title: str,
        colors: Optional[List[str]] = None,
        height: Optional[int] = None
    ) -> go.Figure:
        """
        꺾은 선 차트 생성

        Args:
            data (pd.DataFrame): 데이터프레임
            x_col (str): X축 컬럼명
            y_cols (List[str]): Y축 컬럼명 리스트
            title (str): 차트 제목
            colors (Optional[List[str]]): 색상 리스트
            height (Optional[int]): 차트 높이

        Returns:
            go.Figure: 꺾은 선 차트 객체
        """
        fig = go.Figure()

        if colors is None:
            colors = [settings.THEME_COLORS["success"], settings.THEME_COLORS["primary"]]

        for i, y_col in enumerate(y_cols):
            color = colors[i % len(colors)]
            fig.add_trace(
                go.Scatter(
                    x=data[x_col],
                    y=data[y_col],
                    name=y_col,
                    line=dict(color=color, width=3),
                    mode="lines+markers"
                )
            )

        fig.update_layout(
            title=title,
            xaxis_title="날짜",
            yaxis_title="금액 (KRW)",
            template=settings.CHART_TEMPLATE,
            height=height or settings.CHART_HEIGHT,
            showlegend=True,
            paper_bgcolor="rgba(15, 23, 42, 0)",
            plot_bgcolor="rgba(15, 23, 42, 0)",
            font_color=settings.THEME_COLORS["text"]
        )

        return fig

    @staticmethod
    def create_cash_flow_chart(data: pd.DataFrame) -> go.Figure:
        """
        현금 흐름 차트 생성

        Args:
            data (pd.DataFrame): 현금 흐름 데이터

        Returns:
            go.Figure: 현금 흐름 차트
        """
        return ChartComponents.create_line_chart(
            data=data,
            x_col="날짜",
            y_cols=["현금", "예적금"],
            title="최근 현금 현황 추이",
            colors=[settings.THEME_COLORS["success"], settings.THEME_COLORS["primary"]]
        )

    @staticmethod
    def create_asset_structure_chart(
        cash_value: float,
        investment_value: float
    ) -> go.Figure:
        """
        자산 구조 차트 생성 (현금 vs 투자자산)

        Args:
            cash_value (float): 현금 가치
            investment_value (float): 투자자산 가치

        Returns:
            go.Figure: 자산 구조 차트
        """
        if cash_value + investment_value <= 0:
            # 빈 차트 생성
            fig = go.Figure()
            fig.update_layout(
                title="현금 vs 투자자산",
                template=settings.CHART_TEMPLATE,
                height=settings.CHART_HEIGHT,
                paper_bgcolor="rgba(15, 23, 42, 0)",
                plot_bgcolor="rgba(15, 23, 42, 0)",
                font_color=settings.THEME_COLORS["text"]
            )
            return fig

        data = pd.DataFrame({
            "자산유형": ["현금성자산", "투자자산"],
            "금액": [cash_value, investment_value]
        })

        return ChartComponents.create_pie_chart(
            data=data,
            values_col="금액",
            names_col="자산유형",
            title="현금 vs 투자자산",
            color_sequence=[settings.THEME_COLORS["success"], settings.THEME_COLORS["primary"]]
        )

    @staticmethod
    def create_investment_allocation_chart(
        allocations: List[AssetAllocation]
    ) -> go.Figure:
        """
        투자자산 분배 차트 생성

        Args:
            allocations (List[AssetAllocation]): 자산 분배 리스트

        Returns:
            go.Figure: 투자자산 분배 차트
        """
        if not allocations:
            # 빈 차트 생성
            fig = go.Figure()
            fig.update_layout(
                title="투자자산 분배",
                template=settings.CHART_TEMPLATE,
                height=settings.CHART_HEIGHT,
                paper_bgcolor="rgba(15, 23, 42, 0)",
                plot_bgcolor="rgba(15, 23, 42, 0)",
                font_color=settings.THEME_COLORS["text"]
            )
            return fig

        data = pd.DataFrame([
            {
                "asset_category": alloc.asset_category,
                "total_market_value": alloc.total_market_value
            }
            for alloc in allocations
        ])

        color_sequence = list(settings.THEME_COLORS.values())

        return ChartComponents.create_pie_chart(
            data=data,
            values_col="total_market_value",
            names_col="asset_category",
            title="투자자산 분배",
            color_sequence=color_sequence[:len(data)]
        )

    @staticmethod
    def render_chart(fig: go.Figure, use_container_width: bool = True, width: str = "stretch"):
        """
        차트 렌더링

        Args:
            fig (go.Figure): 차트 객체
            use_container_width (bool): 컨테이너 너비 사용 여부
            width (str): 너비 설정
        """
        st.plotly_chart(fig, use_container_width=use_container_width, width=width)