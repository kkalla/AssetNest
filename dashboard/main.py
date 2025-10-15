import asyncio
import os
import sys
from datetime import datetime
from typing import Any, Dict, List

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import streamlit as st
from plotly.subplots import make_subplots

# 프로젝트 루트를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 로거 import
from logger import dashboard_logger, data_logger, get_dashboard_logger, ui_logger

# 페이지 설정
st.set_page_config(
    page_title="AssetNest 포트폴리오 대쉬보드",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded",
)

# 사이드바에 타이틀
st.sidebar.title("💼 AssetNest")
st.sidebar.markdown("효율적인 자산관리 대쉬보드")

# API 기본 URL
API_BASE_URL = "http://localhost:8000/api/v1"

# Streamlit 세션 초기화 시 로깅
if "dashboard_initialized" not in st.session_state:
    dashboard_logger.info("🚀 AssetNest 대시보드 세션 시작")
    ui_logger.info("🎨 UI 컴포넌트 초기화 중...")
    st.session_state.dashboard_initialized = True


def log_user_action(action: str, details: str = ""):
    """사용자 액션 로깅"""
    ui_logger.info(f"👤 사용자 액션: {action} {f'- {details}' if details else ''}")


def log_chart_render(chart_type: str, data_count: int = 0):
    """차트 렌더링 로깅"""
    ui_logger.info(
        f"📊 차트 렌더링: {chart_type} {f'({data_count}개 데이터)' if data_count else ''}"
    )


def log_page_navigation(page: str):
    """페이지 네비게이션 로깅"""
    ui_logger.info(f"🔄 페이지 이동: {page}")


@st.cache_data(ttl=300)  # 5분 캐시
def fetch_portfolio_overview(account=None):
    """포트폴리오 개요 데이터 조회"""
    try:
        data_logger.info(
            f"📊 포트폴리오 개요 데이터 조회 시작 - 계정: {account or '전체'}"
        )
        url = f"{API_BASE_URL}/portfolio/overview"
        params = {"account": account} if account else {}
        response = requests.get(url, params=params)

        if response.status_code == 200:
            data = response.json()
            data_logger.info(
                f"✅ 포트폴리오 개요 데이터 조회 성공 - 총 자산: ₩{data.get('total_value_krw', 0):,.0f}"
            )
            return data
        else:
            data_logger.error(f"❌ API 오류: {response.status_code} - {response.text}")
            st.error(f"API 오류: {response.status_code}")
            return None
    except Exception as e:
        data_logger.error(f"💥 포트폴리오 개요 데이터 조회 실패: {str(e)}")
        st.error(f"데이터 조회 중 오류가 발생했습니다: {e}")
        return None


@st.cache_data(ttl=300)
def fetch_holdings(account=None, market=None):
    """보유 종목 데이터 조회"""
    try:
        data_logger.info(
            f"📋 보유 종목 데이터 조회 시작 - 계정: {account or '전체'}, 시장: {market or '전체'}"
        )
        url = f"{API_BASE_URL}/holdings/"
        params = {}
        if account:
            params["account"] = account
        if market:
            params["market"] = market

        response = requests.get(url, params=params)

        if response.status_code == 200:
            holdings = response.json()
            data_logger.info(f"✅ 보유 종목 데이터 조회 성공 - {len(holdings)}개 종목")
            return holdings
        else:
            data_logger.error(f"❌ 보유 종목 API 오류: {response.status_code}")
            st.error(f"API 오류: {response.status_code}")
            return []
    except Exception as e:
        data_logger.error(f"💥 보유 종목 조회 실패: {str(e)}")
        st.error(f"보유 종목 조회 중 오류가 발생했습니다: {e}")
        return []


@st.cache_data(ttl=300)
def fetch_currency_rates():
    """환율 정보 조회"""
    try:
        data_logger.info("💱 환율 정보 조회 시작")
        url = f"{API_BASE_URL}/currency/rates"
        response = requests.get(url)

        if response.status_code == 200:
            rates = response.json()
            data_logger.info(f"✅ 환율 정보 조회 성공 - {len(rates)}개 통화")
            return rates
        else:
            data_logger.error(f"❌ 환율 정보 API 오류: {response.status_code}")
            return []
    except Exception as e:
        data_logger.error(f"💥 환율 정보 조회 실패: {str(e)}")
        st.error(f"환율 정보 조회 중 오류가 발생했습니다: {e}")
        return []


@st.cache_data(ttl=300)
def fetch_asset_allocation(account=None):
    """자산 분배 정보 조회"""
    try:
        url = f"{API_BASE_URL}/portfolio/allocation"
        params = {"account": account} if account else {}
        response = requests.get(url, params=params)

        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"자산 분배 API 오류: {response.status_code}")
            return None
    except Exception as e:
        st.error(f"자산 분배 조회 중 오류가 발생했습니다: {e}")
        return None


def refresh_stock_prices():
    """주식 가격 새로고침"""
    try:
        url = f"{API_BASE_URL}/stocks/refresh-prices"
        response = requests.post(url)

        if response.status_code == 200:
            st.success("주식 가격이 성공적으로 업데이트되었습니다!")
            st.cache_data.clear()  # 캐시 클리어
        else:
            st.error("가격 업데이트 중 오류가 발생했습니다.")
    except Exception as e:
        st.error(f"가격 업데이트 중 오류가 발생했습니다: {e}")


# 사이드바 - 계정 선택
st.sidebar.subheader("📊 필터 옵션")

# 포트폴리오 데이터 조회 (계정 목록을 위해)
portfolio_data = fetch_portfolio_overview()
available_accounts = portfolio_data.get("accounts", []) if portfolio_data else []

# 계정 선택
selected_account = st.sidebar.selectbox(
    "계정 선택", ["전체"] + available_accounts, index=0
)

# 실제 API 호출시 전체면 None 전달
account_filter = None if selected_account == "전체" else selected_account

# 지역 필터
market_filter = st.sidebar.selectbox("지역 선택", ["전체", "국내", "해외"], index=0)
market_api_filter = None if market_filter == "전체" else market_filter

# 새로고침 버튼
st.sidebar.subheader("⚙️ 데이터 관리")

col1, col2 = st.sidebar.columns(2)

with col1:
    if st.button("💰 가격 업데이트", type="primary"):
        with st.spinner("업데이트 중..."):
            refresh_stock_prices()

with col2:
    if st.button("🔄 새로고침"):
        st.cache_data.clear()
        st.experimental_rerun()

# 메인 컨텐츠
st.title("💼 AssetNest 포트폴리오 대쉬보드")

# 탭 생성
tab1, tab2, tab3, tab4, tab5 = st.tabs(
    ["📈 포트폴리오 개요", "💼 보유 종목", "🥧 자산 분배", "📊 성과 분석", "⚙️ 설정"]
)

# 포트폴리오 개요 탭
with tab1:
    st.header("📈 포트폴리오 개요")

    # 포트폴리오 데이터 조회
    overview_data = fetch_portfolio_overview(account_filter)

    if overview_data:
        # 상단 메트릭 카드들
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                label="총 자산 (KRW)",
                value=f"₩{overview_data['total_value_krw']:,.0f}",
                delta=f"₩{overview_data['total_pnl_krw']:,.0f}",
            )

        with col2:
            st.metric(
                label="총 수익률",
                value=f"{overview_data['total_return_rate']:.2f}%",
                delta=f"{overview_data['total_return_rate']:.2f}%",
            )

        with col3:
            st.metric(
                label="평가손익 (KRW)",
                value=f"₩{overview_data['total_pnl_krw']:,.0f}",
                delta=f"{overview_data['total_pnl_krw']:,.0f}",
            )

        with col4:
            st.metric(
                label="총 자산 (USD)",
                value=f"${overview_data['total_value_usd']:,.0f}",
                delta=f"${overview_data['total_pnl_usd']:,.0f}",
            )

        # 보유 종목 데이터 가져오기 (차트용)
        holdings_data = fetch_holdings(account_filter, market_api_filter)

        if holdings_data:
            # 데이터프레임 생성
            df = pd.DataFrame(holdings_data)

            # 차트 섹션
            col1, col2 = st.columns(2)

            with col1:
                st.subheader("🥧 계좌별 자산 분배")
                if len(df) > 0:
                    account_summary = (
                        df.groupby("account")["market_value"].sum().reset_index()
                    )
                    fig_pie = px.pie(
                        account_summary,
                        values="market_value",
                        names="account",
                        title="계좌별 자산 비중",
                    )
                    st.plotly_chart(fig_pie, use_container_width=True)

            with col2:
                st.subheader("🌍 지역별 자산 분배")
                if len(df) > 0:
                    market_summary = (
                        df.groupby("market")["market_value"].sum().reset_index()
                    )
                    fig_pie2 = px.pie(
                        market_summary,
                        values="market_value",
                        names="market",
                        title="지역별 자산 비중",
                    )
                    st.plotly_chart(fig_pie2, use_container_width=True)

            # 탑 보유 종목
            st.subheader("🏆 TOP 보유 종목")
            top_holdings = df.nlargest(10, "market_value")[
                ["company", "market_value", "return_rate", "market"]
            ].copy()
            top_holdings["market_value"] = top_holdings["market_value"].apply(
                lambda x: f"₩{x:,.0f}"
            )
            top_holdings["return_rate"] = top_holdings["return_rate"].apply(
                lambda x: f"{x:.2f}%"
            )

            st.dataframe(
                top_holdings,
                column_config={
                    "company": "종목명",
                    "market_value": "평가금액",
                    "return_rate": "수익률",
                    "market": "지역",
                },
                use_container_width=True,
            )

    else:
        st.warning(
            "포트폴리오 데이터를 불러올 수 없습니다. API 서버가 실행 중인지 확인해주세요."
        )

# 보유 종목 탭
with tab2:
    st.header("💼 보유 종목")

    # 보유 종목 데이터 조회
    holdings_data = fetch_holdings(account_filter, market_api_filter)

    if holdings_data:
        # 데이터프레임 생성
        df = pd.DataFrame(holdings_data)

        if len(df) > 0:
            # 요약 정보
            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric("보유 종목 수", len(df))

            with col2:
                total_value = df["market_value"].sum()
                st.metric("총 평가금액", f"₩{total_value:,.0f}")

            with col3:
                total_pnl = df["unrealized_pnl"].sum()
                st.metric("총 평가손익", f"₩{total_pnl:,.0f}")

            # 필터링 옵션
            st.subheader("🔍 상세 필터")

            col1, col2, col3 = st.columns(3)

            with col1:
                min_value = st.number_input("최소 평가금액 (만원)", value=0, step=100)

            with col2:
                min_return = st.number_input("최소 수익률 (%)", value=-100.0, step=1.0)

            with col3:
                max_return = st.number_input("최대 수익률 (%)", value=1000.0, step=1.0)

            # 필터 적용
            filtered_df = df[
                (df["market_value"] >= min_value * 10000)
                & (df["return_rate"] >= min_return)
                & (df["return_rate"] <= max_return)
            ].copy()

            # 표시용 데이터 포맷팅
            display_df = filtered_df[
                [
                    "company",
                    "account",
                    "market",
                    "amount",
                    "avg_price_krw",
                    "current_price_krw",
                    "market_value",
                    "unrealized_pnl",
                    "return_rate",
                ]
            ].copy()

            # 숫자 포맷팅
            display_df["avg_price_krw"] = display_df["avg_price_krw"].apply(
                lambda x: f"₩{x:,.0f}"
            )
            display_df["current_price_krw"] = display_df["current_price_krw"].apply(
                lambda x: f"₩{x:,.0f}"
            )
            display_df["market_value"] = display_df["market_value"].apply(
                lambda x: f"₩{x:,.0f}"
            )
            display_df["unrealized_pnl"] = display_df["unrealized_pnl"].apply(
                lambda x: f"₩{x:,.0f}"
            )
            display_df["return_rate"] = display_df["return_rate"].apply(
                lambda x: f"{x:.2f}%"
            )

            # 데이터 테이블 표시
            st.subheader(f"📊 보유 종목 상세 ({len(display_df)}개)")

            st.dataframe(
                display_df,
                column_config={
                    "company": "종목명",
                    "account": "계좌",
                    "market": "지역",
                    "amount": "보유수량",
                    "avg_price_krw": "평균단가",
                    "current_price_krw": "현재가",
                    "market_value": "평가금액",
                    "unrealized_pnl": "평가손익",
                    "return_rate": "수익률",
                },
                use_container_width=True,
            )

        else:
            st.info("선택한 조건에 해당하는 보유 종목이 없습니다.")

    else:
        st.warning("보유 종목 데이터를 불러올 수 없습니다.")

# 자산 분배 탭
with tab3:
    st.header("🥧 자산 분배")

    # 자산 분배 데이터 조회
    allocation_data = fetch_asset_allocation(account_filter)

    if allocation_data and allocation_data.get("allocations"):
        # 총 포트폴리오 가치 표시
        st.subheader(
            f"💰 총 포트폴리오 가치: ₩{allocation_data['total_portfolio_value']:,.0f}"
        )

        # 데이터프레임 생성
        allocations_df = pd.DataFrame(allocation_data["allocations"])

        if len(allocations_df) > 0:
            # 도넛차트
            st.subheader("🍩 자산유형별 분배")
            fig_donut = px.pie(
                allocations_df,
                values="total_market_value",
                names="asset_category",
                title="자산유형별 분배",
                color_discrete_sequence=px.colors.qualitative.Set3,
                hole=0.4,  # 도넛 모양
            )
            fig_donut.update_traces(textposition="inside", textinfo="percent+label")
            fig_donut.update_layout(height=600)
            st.plotly_chart(fig_donut, use_container_width=True)

            # 바 차트
            st.subheader("📈 자산유형별 평가금액")
            fig_bar = px.bar(
                allocations_df.sort_values("total_market_value", ascending=True),
                x="total_market_value",
                y="asset_category",
                orientation="h",
                title="자산유형별 평가금액",
                color="asset_category",
                color_discrete_sequence=px.colors.qualitative.Set2,
                text="allocation_percentage",
            )
            fig_bar.update_traces(texttemplate="%{text:.1f}%", textposition="inside")
            fig_bar.update_layout(showlegend=False, height=500)
            fig_bar.update_xaxis(title="평가금액 (KRW)")
            fig_bar.update_yaxis(title="자산유형")
            st.plotly_chart(fig_bar, use_container_width=True)

            # 상세 테이블
            st.subheader("📋 자산유형별 상세 정보")

            # 표시용 데이터 포맷팅
            display_allocations = allocations_df.copy()
            display_allocations["total_market_value_formatted"] = display_allocations[
                "total_market_value"
            ].apply(lambda x: f"₩{x:,.0f}")
            display_allocations["allocation_percentage_formatted"] = (
                display_allocations["allocation_percentage"].apply(
                    lambda x: f"{x:.2f}%"
                )
            )

            # 분배율 순으로 정렬
            display_allocations = display_allocations.sort_values(
                "allocation_percentage", ascending=False
            )

            st.dataframe(
                display_allocations[
                    [
                        "asset_category",
                        "holdings_count",
                        "total_market_value_formatted",
                        "allocation_percentage_formatted",
                    ]
                ],
                column_config={
                    "asset_category": "자산유형",
                    "holdings_count": "보유종목수",
                    "total_market_value_formatted": "평가금액",
                    "allocation_percentage_formatted": "분배율",
                },
                use_container_width=True,
                hide_index=True,
            )

            # 분배율 서머리
            st.subheader("📊 분배율 서머리")
            col1, col2, col3 = st.columns(3)

            with col1:
                equity_total = allocations_df[
                    allocations_df["asset_category"].str.contains("주식", na=False)
                ]["allocation_percentage"].sum()
                st.metric("주식 비중", f"{equity_total:.2f}%")

            with col2:
                bond_total = allocations_df[
                    allocations_df["asset_category"].str.contains("채권", na=False)
                ]["allocation_percentage"].sum()
                st.metric("채권 비중", f"{bond_total:.2f}%")

            with col3:
                other_total = 100 - equity_total - bond_total
                st.metric("기타 비중", f"{other_total:.2f}%")

        else:
            st.info("자산 분배 데이터가 없습니다.")

    else:
        st.warning(
            "자산 분배 데이터를 불러올 수 없습니다. API 서버가 실행 중인지 확인해주세요."
        )

# 성과 분석 탭
with tab4:
    st.header("📊 성과 분석")
    st.info("성과 분석 기능은 다음 단계에서 구현될 예정입니다.")

# 설정 탭
with tab5:
    st.header("⚙️ 설정")

    # 환율 정보
    st.subheader("💱 환율 정보")
    currency_data = fetch_currency_rates()

    if currency_data:
        for rate in currency_data:
            st.metric(
                f"{rate['currency']} 환율",
                f"{rate['exchange_rate']:,.2f} KRW",
                delta=f"업데이트: {rate['updated_at'][:10]}",
            )

    # 시스템 정보
    st.subheader("ℹ️ 시스템 정보")
    st.info(f"마지막 업데이트: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    col1, col2 = st.columns(2)

    with col1:
        st.write("**API 서버 상태**")
        try:
            response = requests.get(API_BASE_URL.replace("/api/v1", ""))
            if response.status_code == 200:
                st.success("✅ API 서버 연결됨")
            else:
                st.error("❌ API 서버 연결 실패")
        except:
            st.error("❌ API 서버에 연결할 수 없습니다")

    with col2:
        st.write("**데이터 새로고침**")
        if st.button("🔄 전체 캐시 초기화"):
            st.cache_data.clear()
            st.success("캐시가 초기화되었습니다!")

# 푸터
st.markdown("---")
st.markdown("💼 **AssetNest** - 효율적인 자산관리를 위한 대쉬보드 v1.0")
