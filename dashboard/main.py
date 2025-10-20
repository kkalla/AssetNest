import asyncio
import os
import sys
from datetime import datetime, date
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


# 현금 관리 관련 API 함수
@st.cache_data(ttl=300)
def fetch_cash_management_summary():
    """현금 관리 요약 정보 조회"""
    try:
        data_logger.info("💰 현금 관리 요약 정보 조회 시작")
        url = f"{API_BASE_URL}/cash/summary"
        response = requests.get(url)

        if response.status_code == 200:
            data_logger.info("✅ 현금 관리 요약 정보 조회 성공")
            return response.json()
        else:
            data_logger.error(f"❌ 현금 관리 요약 API 오류: {response.status_code}")
            st.error(f"현금 관리 요약 API 오류: {response.status_code}")
            return None
    except Exception as e:
        data_logger.error(f"💥 현금 관리 요약 조회 실패: {str(e)}")
        st.error(f"현금 관리 요약 조회 중 오류가 발생했습니다: {e}")
        return None


@st.cache_data(ttl=300)
def fetch_cash_balances(account=None):
    """증권사별 예수금 정보 조회"""
    try:
        data_logger.info(
            f"💰 증권사별 예수금 정보 조회 시작 - 계정: {account or '전체'}"
        )
        url = f"{API_BASE_URL}/cash/balances/"
        params = {"account": account} if account else {}
        response = requests.get(url, params=params)

        if response.status_code == 200:
            data_logger.info(f"✅ 증권사별 예수금 정보 조회 성공")
            return response.json()
        else:
            data_logger.error(f"❌ 증권사별 예수금 API 오류: {response.status_code}")
            st.error(f"증권사별 예수금 API 오류: {response.status_code}")
            return []
    except Exception as e:
        data_logger.error(f"💥 증권사별 예수금 조회 실패: {str(e)}")
        st.error(f"증권사별 예수금 조회 중 오류가 발생했습니다: {e}")
        return []


@st.cache_data(ttl=300)
def fetch_time_deposits(account=None):
    """예적금 정보 조회"""
    try:
        data_logger.info(f"💰 예적금 정보 조회 시작 - 계정: {account or '전체'}")
        url = f"{API_BASE_URL}/cash/deposits/"
        params = {"account": account} if account else {}
        response = requests.get(url, params=params)

        if response.status_code == 200:
            data_logger.info(f"✅ 예적금 정보 조회 성공")
            return response.json()
        else:
            data_logger.error(f"❌ 예적금 API 오류: {response.status_code}")
            st.error(f"예적금 API 오류: {response.status_code}")
            return []
    except Exception as e:
        data_logger.error(f"💥 예적금 조회 실패: {str(e)}")
        st.error(f"예적금 조회 중 오류가 발생했습니다: {e}")
        return []


def update_cash_balance(account, krw=None, usd=None):
    """증권사별 예수금 업데이트"""
    try:
        data_logger.info(f"💰 {account} 계좌 예수금 업데이트 요청")
        url = f"{API_BASE_URL}/cash/balances/{account}"
        update_data = {}
        if krw is not None:
            update_data["krw"] = krw
        if usd is not None:
            update_data["usd"] = usd

        response = requests.put(url, json=update_data)

        if response.status_code == 200:
            data_logger.info(f"✅ {account} 계좌 예수금 업데이트 성공")
            st.success(f"{account} 계좌의 예수금이 성공적으로 업데이트되었습니다")
            st.cache_data.clear()
            return True
        else:
            data_logger.error(
                f"❌ {account} 계좌 예수금 업데이트 실패: {response.status_code}"
            )
            st.error(f"예수금 업데이트 실패: {response.status_code}")
            return False
    except Exception as e:
        data_logger.error(f"💥 예수금 업데이트 실패: {str(e)}")
        st.error(f"예수금 업데이트 중 오류가 발생했습니다: {e}")
        return False


def create_time_deposit(
    account,
    invest_prod_name,
    market_value,
    invested_principal,
    maturity_date=None,
    interest_rate=None,
):
    """예적금 생성"""
    try:
        data_logger.info(f"💰 예적금 생성 요청: {invest_prod_name}")
        url = f"{API_BASE_URL}/cash/deposits/"
        create_data = {
            "account": account,
            "invest_prod_name": invest_prod_name,
            "market_value": market_value,
            "invested_principal": invested_principal,
        }
        if maturity_date:
            # date 객체를 ISO 형식 문자열로 변환하여 JSON 직렬화 문제 해결
            if isinstance(maturity_date, (datetime, date)):
                create_data["maturity_date"] = maturity_date.isoformat()
            else:
                create_data["maturity_date"] = maturity_date
        if interest_rate:
            create_data["interest_rate"] = interest_rate

        response = requests.post(url, json=create_data)

        if response.status_code == 200:
            data_logger.info(f"✅ 예적금 생성 성공: {invest_prod_name}")
            st.success("예적금이 성공적으로 생성되었습니다")
            st.cache_data.clear()
            return True
        else:
            data_logger.error(f"❌ 예적금 생성 실패: {response.status_code}")
            st.error(f"예적금 생성 실패: {response.status_code}")
            return False
    except Exception as e:
        data_logger.error(f"💥 예적금 생성 실패: {str(e)}")
        st.error(f"예적금 생성 중 오류가 발생했습니다: {e}")
        return False


def update_time_deposit(
    account,
    invest_prod_name,
    market_value=None,
    invested_principal=None,
    maturity_date=None,
    interest_rate=None,
):
    """예적금 수정"""
    try:
        data_logger.info(f"💰 예적금 수정 요청: {invest_prod_name}")
        url = f"{API_BASE_URL}/cash/deposits/{account}"
        update_data = {"invest_prod_name": invest_prod_name}
        if market_value is not None:
            update_data["market_value"] = market_value
        if invested_principal is not None:
            update_data["invested_principal"] = invested_principal
        if maturity_date is not None:
            # date 객체를 ISO 형식 문자열로 변환하여 JSON 직렬화 문제 해결
            if isinstance(maturity_date, (datetime, date)):
                update_data["maturity_date"] = maturity_date.isoformat()
            else:
                update_data["maturity_date"] = maturity_date
        if interest_rate is not None:
            update_data["interest_rate"] = interest_rate

        response = requests.put(url, json=update_data)

        if response.status_code == 200:
            data_logger.info(f"✅ 예적금 수정 성공: {invest_prod_name}")
            st.success("예적금이 성공적으로 수정되었습니다")
            st.cache_data.clear()

            # bs_timeseries 업데이트 - 현재 현금 정보를 다시 계산하여 저장
            update_bs_timeseries_after_deposit_change(account)
            return True
        else:
            data_logger.error(f"❌ 예적금 수정 실패: {response.status_code}")
            st.error(f"예적금 수정 실패: {response.status_code}")
            return False
    except Exception as e:
        data_logger.error(f"💥 예적금 수정 실패: {str(e)}")
        st.error(f"예적금 수정 중 오류가 발생했습니다: {e}")
        return False


def update_bs_timeseries_after_deposit_change(account):
    """예적금 변경 후 bs_timeseries 테이블 업데이트"""
    try:
        # 1. 수정된 예적금 데이터를 다시 조회
        updated_time_deposits = fetch_time_deposits(None)  # 전체 계정 조회

        if updated_time_deposits:
            # 2. 변경된 예적금 총합 계산
            total_time_deposits = sum(
                td["market_value"] for td in updated_time_deposits
            )
            data_logger.info(f"💰 변경된 예적금 총합: {total_time_deposits:,}원")

            # 3. bs_timeseries 업데이트 API 호출 (예적금 총합만 전달)
            url = f"{API_BASE_URL}/cash/current"
            update_data = {
                "time_deposit": total_time_deposits,
                "reason": f"예적금 수정 ({account})",
            }

            response = requests.put(url, json=update_data)

            if response.status_code == 200:
                data_logger.info("✅ bs_timeseries 예적금 컬럼 업데이트 성공")

                # 4. 캐시 초기화하여 업데이트된 데이터가 반영되도록 함
                st.cache_data.clear()
                data_logger.info("🔄 캐시 데이터 초기화 완료")
            else:
                data_logger.warning(
                    f"⚠️ bs_timeseries 업데이트 실패: {response.status_code}"
                )
        else:
            data_logger.warning("⚠️ 예적금 데이터를 조회할 수 없습니다")
    except Exception as e:
        data_logger.error(f"💥 bs_timeseries 업데이트 실패: {str(e)}")


def delete_time_deposit(account, invest_prod_name):
    """예적금 삭제"""
    try:
        data_logger.info(f"💰 예적금 삭제 요청: {invest_prod_name}")
        url = f"{API_BASE_URL}/cash/deposits/{account}/{invest_prod_name}"
        response = requests.delete(url)

        if response.status_code == 200:
            data_logger.info(f"✅ 예적금 삭제 성공: {invest_prod_name}")
            st.success("예적금이 성공적으로 삭제되었습니다")
            st.cache_data.clear()
            return True
        else:
            data_logger.error(f"❌ 예적금 삭제 실패: {response.status_code}")
            st.error(f"예적금 삭제 실패: {response.status_code}")
            return False
    except Exception as e:
        data_logger.error(f"💥 예적금 삭제 실패: {str(e)}")
        st.error(f"예적금 삭제 중 오류가 발생했습니다: {e}")
        return False


def update_current_cash(cash, reason=None):
    """현재 현금 업데이트"""
    try:
        data_logger.info(f"💰 현재 현금 업데이트 요청: {cash:,}원")
        url = f"{API_BASE_URL}/cash/current"
        update_data = {"cash": cash}
        if reason:
            update_data["reason"] = reason

        response = requests.put(url, json=update_data)

        if response.status_code == 200:
            data_logger.info(f"✅ 현재 현금 업데이트 성공: {cash:,}원")
            st.success("현재 현금이 성공적으로 업데이트되었습니다")
            st.cache_data.clear()
            return True
        else:
            data_logger.error(f"❌ 현재 현금 업데이트 실패: {response.status_code}")
            st.error(f"현금 업데이트 실패: {response.status_code}")
            return False
    except Exception as e:
        data_logger.error(f"💥 현재 현금 업데이트 실패: {str(e)}")
        st.error(f"현금 업데이트 중 오류가 발생했습니다: {e}")
        return False


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


# 페이지 선택 (사이드바 패널)
st.sidebar.subheader("📑 페이지 선택")


# 페이지 버튼들 - session_state 사용하여 페이지 상태 유지
def create_page_button(page_name: str, page_key: str):
    """페이지 버튼 생성 함수"""
    if st.sidebar.button(page_name, use_container_width=True, key=page_key):
        st.session_state.selected_page = page_name
        st.rerun()


# 페이지 선택 로직
if "selected_page" not in st.session_state:
    st.session_state.selected_page = "📈 포트폴리오 개요"

# 페이지 버튼들 생성
create_page_button("📈 포트폴리오 개요", "portfolio_overview")
create_page_button("🥧 자산 분배", "asset_allocation")
create_page_button("💰 현금 관리", "cash_management")
create_page_button("💼 보유 종목", "holdings")
create_page_button("📊 성과 분석", "performance")
create_page_button("⚙️ 설정", "settings")

# 선택된 페이지
selected_page = st.session_state.selected_page

# 현재 선택된 페이지 표시
st.sidebar.markdown(f"**현재 페이지:** {selected_page}")

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
        st.rerun()

# 메인 컨텐츠
st.title("💼 AssetNest 포트폴리오 대쉬보드")

# 포트폴리오 데이터 조회 (모든 페이지에서 공통으로 사용)
overview_data = fetch_portfolio_overview()

# 포트폴리오 개요 페이지
if selected_page == "📈 포트폴리오 개요":
    st.header("📈 포트폴리오 개요")

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

    else:
        st.warning(
            "포트폴리오 데이터를 불러올 수 없습니다. API 서버가 실행 중인지 확인해주세요."
        )

# 자산 분배 페이지
elif selected_page == "🥧 자산 분배":
    st.header("🥧 자산 분배")

    # 자산 분배 데이터 조회
    allocation_data = fetch_asset_allocation()

    if allocation_data and allocation_data.get("allocations"):
        # 총 포트폴리오 가치 표시
        st.subheader(
            f"💰 총 포트폴리오 가치: ₩{allocation_data['total_portfolio_value']:,.0f}"
        )

        # 데이터프레임 생성
        allocations_df = pd.DataFrame(allocation_data["allocations"])
        allocations_df["allocation_percentage"] = (
            allocations_df["allocation_percentage"].round(0).astype(int)
        )

        # 자산 구조 파이차트들
        st.subheader("🍩 자산 구조 분석")

        # 파이차트 2개를 위한 열 생성
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("💰 현금 vs 투자자산 비율")
            # 현금 vs 투자자산 파이차트 데이터
            asset_structure_data = {
                "자산유형": ["현금성자산", "투자자산"],
                "금액": [
                    overview_data.get("cash_asset_value", 0),
                    overview_data.get("investment_asset_value", 0),
                ],
                "비율": [
                    overview_data.get("cash_asset_ratio", 0),
                    overview_data.get("investment_asset_ratio", 0),
                ],
            }

            if sum(asset_structure_data["금액"]) > 0:
                fig_asset_structure = px.pie(
                    values=asset_structure_data["금액"],
                    names=asset_structure_data["자산유형"],
                    title="현금 vs 투자자산",
                    color_discrete_sequence=["#10B981", "#3B82F6"],  # 초록, 다크 네이비
                    hole=0.3,  # 도넛 모양
                )
                fig_asset_structure.update_traces(
                    textposition="inside",
                    textinfo="percent+label",
                    hovertemplate="<b>%{label}</b><br>금액: ₩%{value:,.0f}<br>비중: %{percent}<extra></extra>",
                )
                fig_asset_structure.update_layout(
                    height=400,
                    showlegend=False,
                    template="plotly_dark",
                    paper_bgcolor="rgba(15, 23, 42, 0)",
                    plot_bgcolor="rgba(15, 23, 42, 0)",
                    font_color="#F8FAFC",
                )
                st.plotly_chart(fig_asset_structure, width="stretch")

                # 요약 정보 표시
                st.info(
                    f"💰 현금: ₩{asset_structure_data['금액'][0]:,.0f} ({asset_structure_data['비율'][0]:.1f}%) | 📈 투자: ₩{asset_structure_data['금액'][1]:,.0f} ({asset_structure_data['비율'][1]:.1f}%)"
                )
            else:
                st.warning("자산 데이터가 없습니다.")

        with col2:
            st.subheader("📊 투자자산 분배 비율")
            # 투자자산 분배 파이차트 데이터
            investment_allocations = overview_data.get("investment_allocations", [])

            if investment_allocations:
                # 데이터프레임 생성
                alloc_df = pd.DataFrame(investment_allocations)
                alloc_df["allocation_percentage"] = (
                    alloc_df["allocation_percentage"].round(0).astype(int)
                )

                fig_investment_alloc = px.pie(
                    values=alloc_df["total_market_value"],
                    names=alloc_df["asset_category"],
                    title="투자자산 분배",
                    color_discrete_sequence=[
                        "#3B82F6",
                        "#10B981",
                        "#F59E0B",
                        "#EF4444",
                        "#8B5CF6",
                        "#EC4899",
                        "#06B6D4",
                        "#84CC16",
                    ],
                    hole=0.3,  # 도넛 모양
                )
                fig_investment_alloc.update_traces(
                    textposition="inside",
                    textinfo="percent+label",
                    hovertemplate="<b>%{label}</b><br>평가금액: ₩%{value:,.0f}<br>비중: %{percent}<extra></extra>",
                )
                fig_investment_alloc.update_layout(
                    height=400,
                    showlegend=False,
                    template="plotly_dark",
                    paper_bgcolor="rgba(15, 23, 42, 0)",
                    plot_bgcolor="rgba(15, 23, 42, 0)",
                    font_color="#F8FAFC",
                )
                st.plotly_chart(fig_investment_alloc, width="stretch")

                # 상위 3개 투자자산 요약
                top_3_alloc = alloc_df.nlargest(3, "total_market_value")
                summary_text = " | ".join(
                    [
                        f"{row['asset_category']}: {row['allocation_percentage']:.0f}%"
                        for _, row in top_3_alloc.iterrows()
                    ]
                )
                st.info(f"🏆 상위 분배: {summary_text}")
            else:
                st.warning("투자자산 분배 데이터가 없습니다.")

        if len(allocations_df) > 0:
            # 바 차트
            st.subheader("📈 자산유형별 평가금액")
            fig_bar = px.bar(
                allocations_df.sort_values("total_market_value", ascending=True),
                x="total_market_value",
                y="asset_category",
                orientation="h",
                title="자산유형별 평가금액",
                color="asset_category",
                color_discrete_sequence=[
                    "#3B82F6",
                    "#10B981",
                    "#F59E0B",
                    "#EF4444",
                    "#8B5CF6",
                    "#EC4899",
                    "#06B6D4",
                    "#84CC16",
                ],
                text="allocation_percentage",
            )
            fig_bar.update_traces(texttemplate="%{text:.0f}%", textposition="inside")
            fig_bar.update_layout(
                showlegend=False,
                height=500,
                template="plotly_dark",
                paper_bgcolor="rgba(15, 23, 42, 0)",
                plot_bgcolor="rgba(15, 23, 42, 0)",
                font_color="#F8FAFC",
            )
            fig_bar.update_xaxes(
                title_text="평가금액 (KRW)",
                gridcolor="rgba(30, 41, 59, 0.5)",
                tickcolor="#F8FAFC",
            )
            fig_bar.update_yaxes(
                title_text="자산유형",
                gridcolor="rgba(30, 41, 59, 0.5)",
                tickcolor="#F8FAFC",
            )
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
                    lambda x: f"{x:.0f}%"
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
                width="stretch",
                hide_index=True,
            )

            # 자산분배 시뮬레이터
            st.subheader("🎯 자산분배 시뮬레이터")

            # overview_data가 있는지 확인
            if overview_data:
                # 탭으로 두 시뮬레이터 구분
                sim_tab1, sim_tab2 = st.tabs(
                    ["💰 현금 vs 투자자산", "📊 투자자산 상세 분배"]
                )

                # 탭1: 현금 vs 투자자산 비율 조정
                with sim_tab1:
                    st.markdown(
                        "원하는 현금/투자자산 비율을 설정하면 목표 달성을 위한 매매 금액을 계산합니다."
                    )

                    # 현재 자산 정보 가져오기
                    current_cash = overview_data.get("cash_asset_value", 0)
                    current_investment = overview_data.get("investment_asset_value", 0)
                    total_assets = current_cash + current_investment

                    if total_assets > 0:
                        current_cash_ratio = round(
                            (current_cash / total_assets) * 100, 1
                        )
                        current_investment_ratio = round(
                            (current_investment / total_assets) * 100, 1
                        )

                        # 현재 비율 표시
                        col1, col2 = st.columns(2)
                        with col1:
                            st.info(
                                f"**현재 비율**\n\n💰 현금: {current_cash_ratio:.1f}% (₩{current_cash:,.0f})\n\n📈 투자: {current_investment_ratio:.1f}% (₩{current_investment:,.0f})"
                            )

                        with col2:
                            st.info(f"**총 자산**: ₩{total_assets:,.0f}")

                        # 목표 비율 입력 (TDF 기본값 적용)
                        st.markdown("##### 목표 비율 설정")
                        # 기본 비율: 현금 10%
                        default_cash_ratio = 10.0
                        target_cash_ratio = st.slider(
                            "목표 현금 비율 (%)",
                            min_value=0.0,
                            max_value=100.0,
                            value=default_cash_ratio,
                            step=0.5,
                            help="원하는 현금 자산의 비율을 설정하세요. 투자자산은 자동으로 계산됩니다.",
                        )

                        target_investment_ratio = 100.0 - target_cash_ratio

                        # 목표 금액 계산
                        target_cash = total_assets * (target_cash_ratio / 100)
                        target_investment = total_assets * (
                            target_investment_ratio / 100
                        )

                        # 필요한 조정 금액 계산
                        cash_adjustment = target_cash - current_cash
                        investment_adjustment = target_investment - current_investment

                        # 결과 표시
                        st.markdown("##### 📊 시뮬레이션 결과")

                        col1, col2, col3 = st.columns(3)

                        with col1:
                            st.markdown("**목표 비율**")
                            st.metric(
                                "현금",
                                f"{target_cash_ratio:.1f}%",
                                delta=f"{target_cash_ratio - current_cash_ratio:+.1f}%p",
                            )
                            st.metric(
                                "투자",
                                f"{target_investment_ratio:.1f}%",
                                delta=f"{target_investment_ratio - current_investment_ratio:+.1f}%p",
                            )

                        with col2:
                            st.markdown("**목표 금액**")
                            st.metric("현금", f"₩{target_cash:,.0f}")
                            st.metric("투자", f"₩{target_investment:,.0f}")

                        with col3:
                            st.markdown("**필요한 조정**")
                            if abs(cash_adjustment) < 1000:
                                st.success("✅ 조정 불필요")
                            else:
                                if cash_adjustment > 0:
                                    st.metric(
                                        "현금 증가 필요",
                                        f"₩{abs(cash_adjustment):,.0f}",
                                        delta="매도 필요",
                                        delta_color="inverse",
                                    )
                                else:
                                    st.metric(
                                        "투자 증가 필요",
                                        f"₩{abs(investment_adjustment):,.0f}",
                                        delta="매수 필요",
                                        delta_color="normal",
                                    )

                        # 실행 계획 표시
                        if abs(cash_adjustment) >= 1000:
                            st.markdown("##### 💡 실행 계획")

                            if cash_adjustment > 0:
                                # 현금을 늘려야 함 = 투자자산 매도
                                st.warning(
                                    f"📉 **투자자산 매도**: ₩{abs(cash_adjustment):,.0f} 상당의 주식/펀드를 매도하여 현금 비중을 높이세요."
                                )
                            else:
                                # 투자자산을 늘려야 함 = 현금으로 매수
                                st.success(
                                    f"📈 **투자자산 매수**: ₩{abs(investment_adjustment):,.0f} 상당의 주식/펀드를 매수하여 투자 비중을 높이세요."
                                )

                            # 조정 후 예상 비율
                            st.markdown("**조정 후 예상 포트폴리오**")
                            adjustment_data = pd.DataFrame(
                                {
                                    "구분": ["현금", "투자"],
                                    "현재 금액": [current_cash, current_investment],
                                    "목표 금액": [target_cash, target_investment],
                                    "조정 금액": [
                                        cash_adjustment,
                                        investment_adjustment,
                                    ],
                                }
                            )

                            st.dataframe(
                                adjustment_data.style.format(
                                    {
                                        "현재 금액": "₩{:,.0f}",
                                        "목표 금액": "₩{:,.0f}",
                                        "조정 금액": "₩{:+,.0f}",
                                    }
                                ),
                                width="stretch",
                                hide_index=True,
                            )
                        else:
                            st.success(
                                "✅ 현재 비율이 목표 비율과 유사합니다. 조정이 필요하지 않습니다."
                            )

                    else:
                        st.warning(
                            "자산 데이터가 없어 시뮬레이션을 실행할 수 없습니다."
                        )

                # 탭2: 투자자산 내 분배비율 조정
                with sim_tab2:
                    st.markdown(
                        "투자자산별 목표 비율을 설정하면 매수/매도해야 할 금액을 계산합니다."
                    )

                    # 투자자산 분배 데이터 가져오기
                    investment_allocations = overview_data.get(
                        "investment_allocations", []
                    )

                    if investment_allocations and len(investment_allocations) > 0:
                        # 현재 투자자산 총액
                        current_investment = overview_data.get(
                            "investment_asset_value", 0
                        )

                        # 데이터프레임 생성
                        inv_alloc_df = pd.DataFrame(investment_allocations)
                        # 원래 소수점 비율 저장
                        inv_alloc_df["allocation_percentage_original"] = inv_alloc_df[
                            "allocation_percentage"
                        ]
                        inv_alloc_df["allocation_percentage"] = (
                            inv_alloc_df["allocation_percentage"].round(0).astype(int)
                        )

                        # 현재 비율 표시
                        st.info(
                            f"**총 투자자산**: ₩{current_investment:,.0f}\n\n아래에서 각 자산의 목표 비율을 입력하세요. 합계가 100%가 되어야 합니다."
                        )

                        # 목표 비율 입력을 위한 컨테이너
                        st.markdown("##### 목표 비율 설정")

                        # 기본 비율 설정
                        default_ratios = {
                            "TDF": 5,
                            "기타": 5,
                            "해외채권": 20,
                            "국내채권": 14,
                            "해외주식": 15,
                            "국내주식": 15,
                            "해외리츠": 5,
                            "국내리츠": 5,
                            "원자재": 8,
                            "금": 8,
                        }

                        # 자산유형 정렬 순서 정의
                        asset_order = [
                            "TDF",
                            "해외채권",
                            "국내채권",
                            "해외주식",
                            "국내주식",
                            "해외리츠",
                            "국내리츠",
                            "원자재",
                            "금",
                            "기타",
                        ]

                        # 데이터프레임을 정렬된 순서로 재정렬
                        inv_alloc_df_sorted = inv_alloc_df.copy()
                        inv_alloc_df_sorted["sort_key"] = inv_alloc_df_sorted[
                            "asset_category"
                        ].apply(
                            lambda x: (
                                asset_order.index(x)
                                if x in asset_order
                                else len(asset_order)
                            )
                        )
                        inv_alloc_df_sorted = inv_alloc_df_sorted.sort_values(
                            "sort_key"
                        ).reset_index(drop=True)

                        target_ratios = {}
                        cols = st.columns(min(3, len(inv_alloc_df_sorted)))

                        for idx, row in inv_alloc_df_sorted.iterrows():
                            col_idx = int(idx) % min(3, len(inv_alloc_df_sorted))
                            with cols[col_idx]:
                                # TDF 기본값 사용, 없으면 현재 비율 사용
                                default_value = default_ratios.get(
                                    row["asset_category"],
                                    int(round(row["allocation_percentage_original"])),
                                )
                                target_ratios[row["asset_category"]] = st.number_input(
                                    f"{row['asset_category']} (%)",
                                    min_value=0,
                                    max_value=100,
                                    value=default_value,
                                    step=1,
                                    key=f"inv_ratio_{row['asset_category']}",
                                )

                        # 합계 검증
                        total_ratio = sum(target_ratios.values())
                        ratio_diff = abs(total_ratio - 100)

                        # 합계 표시
                        if ratio_diff == 0:
                            st.success(f"✅ 비율 합계: {total_ratio:.0f}% (정상)")
                            is_valid = True
                        else:
                            st.warning(
                                f"⚠️ 비율 합계: {total_ratio:.0f}% (100%가 되어야 합니다. 차이: {total_ratio - 100:.0f}%)"
                            )
                            is_valid = False

                        # 시뮬레이션 결과 (합계가 100%일 때만 표시)
                        if is_valid:
                            st.markdown("##### 📊 시뮬레이션 결과")

                            # 조정 필요 금액 계산
                            adjustments = []
                            for _, row in inv_alloc_df.iterrows():
                                asset_category = row["asset_category"]
                                current_value = row["total_market_value"]
                                current_ratio_rounded = int(
                                    round(row["allocation_percentage_original"])
                                )
                                target_ratio = target_ratios[asset_category]

                                # 현재 비율과 목표 비율이 같으면 현재 금액을 그대로 사용
                                if current_ratio_rounded == target_ratio:
                                    target_value = current_value
                                else:
                                    target_value = current_investment * (
                                        target_ratio / 100
                                    )

                                adjustment = target_value - current_value

                                adjustments.append(
                                    {
                                        "자산유형": asset_category,
                                        "현재 비율": row[
                                            "allocation_percentage_original"
                                        ],
                                        "목표 비율": target_ratio,
                                        "현재 금액": current_value,
                                        "목표 금액": target_value,
                                        "조정 금액": adjustment,
                                    }
                                )

                            adjustment_df = pd.DataFrame(adjustments)

                            # asset_order에 맞춰서 정렬
                            adjustment_df["sort_key"] = adjustment_df["자산유형"].apply(
                                lambda x: (
                                    asset_order.index(x)
                                    if x in asset_order
                                    else len(asset_order)
                                )
                            )
                            adjustment_df = adjustment_df.sort_values(
                                "sort_key"
                            ).reset_index(drop=True)

                            # 상세 조정 내역
                            st.markdown("##### 💡 자산별 조정 계획")

                            # 조정 후 예상 포트폴리오 테이블
                            st.dataframe(
                                adjustment_df.style.format(
                                    {
                                        "현재 비율": "{:.0f}%",
                                        "목표 비율": "{:.0f}%",
                                        "현재 금액": "₩{:,.0f}",
                                        "목표 금액": "₩{:,.0f}",
                                        "조정 금액": "₩{:+,.0f}",
                                    }
                                ),
                                width="stretch",
                                hide_index=True,
                            )

                    else:
                        st.warning("투자자산 분배 데이터가 없습니다.")

            else:
                st.warning(
                    "포트폴리오 데이터를 불러올 수 없어 시뮬레이터를 실행할 수 없습니다."
                )

        else:
            st.info("자산 분배 데이터가 없습니다.")

    else:
        st.warning(
            "자산 분배 데이터를 불러올 수 없습니다. API 서버가 실행 중인지 확인해주세요."
        )

# 보유 종목 페이지
elif selected_page == "💼 보유 종목":
    st.header("💼 보유 종목")

    # 보유 종목 데이터 조회
    holdings_data = fetch_holdings()

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
                width="stretch",
            )

        else:
            st.info("선택한 조건에 해당하는 보유 종목이 없습니다.")

    else:
        st.warning("보유 종목 데이터를 불러올 수 없습니다.")

# 현금 관리 페이지
elif selected_page == "💰 현금 관리":
    st.header("💰 현금 관리")

    # 현금 관리 요약 정보 조회
    cash_summary = fetch_cash_management_summary()

    if cash_summary:
        # 전체 현금 상태 요약
        st.subheader("📊 전체 현금 현황")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                label="총 현금성자산",
                value=f"₩{cash_summary['total_cash']:,.0f}",
            )

        with col2:
            st.metric(
                label="총 현금",
                value=f"₩{cash_summary['total_cash_balance']:,.0f}",
            )

        with col3:
            st.metric(
                label="총 예적금", value=f"₩{cash_summary['total_time_deposit']:,.0f}"
            )

        with col4:
            st.metric(
                label="총 증권사 예수금",
                value=f"₩{cash_summary['total_security_cash']:,.0f}",
            )

        # 탭으로 기능 분리
        tab1, tab2, tab3 = st.tabs(
            ["💳 증권사 예수금", "💎 예적금 관리", "📈 현재 현금 관리"]
        )

        # 탭1: 현재 현금 관리
        with tab1:
            st.subheader("📈 현재 현금 관리")

            # 최신 현금 정보 조회
            latest_bs = cash_summary.get("latest_bs_entry")

            if latest_bs:
                # 현재 현금 정보 표시
                st.info(f"최신 업데이트: {latest_bs['date']}")

                col1, col2, col3 = st.columns(3)

                with col1:
                    st.metric("현재 현금", f"₩{latest_bs['cash']:,.0f}")

                with col2:
                    st.metric("예적금", f"₩{latest_bs['time_deposit']:,.0f}")

                with col3:
                    st.metric(
                        "증권사 예수금", f"₩{latest_bs['security_cash_balance']:,.0f}"
                    )

                # 현금 업데이트 섹션
                st.subheader("💸 현재 현금 업데이트")

                col1, col2 = st.columns(2)

                with col1:
                    new_cash = int(
                        st.number_input(
                            "새 현금 금액",
                            min_value=0,
                            value=int(latest_bs["cash"]),
                            step=10000,
                            format="%d",
                        )
                    )

                with col2:
                    reason = st.text_input(
                        "변경 사유 (선택사)", placeholder="예: 월급 입금"
                    )

                # 업데이트 버튼
                if st.button(
                    "💰 현재 현금 업데이트", type="primary", use_container_width=True
                ):
                    if update_current_cash(new_cash, reason):
                        st.rerun()

                # 현금 흐름 정보
                st.subheader("📊 현금 흐름 분석")

                # 최근 7일간 추이 (데이터가 있다면)
                st.info("📈 최근 현금 변동 추이 (구현 예정)")

                # 차트 영역 (placeholder)
                chart_placeholder = pd.DataFrame(
                    {
                        "날짜": [
                            "2024-10-11",
                            "2024-10-12",
                            "2024-10-13",
                            "2024-10-14",
                            "2024-10-15",
                            "2024-10-16",
                            "2024-10-17",
                        ],
                        "현금": [
                            28000000,
                            28500000,
                            29264236,
                            28500000,
                            29000000,
                            29200000,
                            29264236,
                        ],
                        "예적금": [
                            17610000,
                            17610000,
                            17610000,
                            17610000,
                            17610000,
                            17610000,
                            17610000,
                        ],
                    }
                )

                # 꺾은 선 차트
                fig = go.Figure()

                fig.add_trace(
                    go.Scatter(
                        x=chart_placeholder["날짜"],
                        y=chart_placeholder["현금"],
                        name="현금",
                        line=dict(color="#10B981", width=3),
                        mode="lines+markers",
                    )
                )

                fig.add_trace(
                    go.Scatter(
                        x=chart_placeholder["날짜"],
                        y=chart_placeholder["예적금"],
                        name="예적금",
                        line=dict(color="#3B82F6", width=3),
                        mode="lines+markers",
                    )
                )

                fig.update_layout(
                    title="최근 현금 현황 추이",
                    xaxis_title="날짜",
                    yaxis_title="금액 (KRW)",
                    template="plotly_dark",
                    height=400,
                    showlegend=True,
                    paper_bgcolor="rgba(15, 23, 42, 0)",
                    plot_bgcolor="rgba(15, 23, 42, 0)",
                    font_color="#F8FAFC",
                )

                st.plotly_chart(fig, use_container_width=True)

                # 합계 계산
                total_cash = latest_bs["cash"] + latest_bs["time_deposit"]
                st.metric("총 현금성자산", f"₩{total_cash:,.0f}")
            else:
                st.warning(
                    "bs_timeseries 데이터가 없습니다. 먼저 현금을 업데이트해주세요."
                )
        # 탭2: 증권사 예수금 관리
        with tab2:
            st.subheader("💳 증권사별 예수금 관리")

            # 예수금 데이터 조회
            cash_balances = fetch_cash_balances()

            if cash_balances:
                st.info(f"📋 현재 {len(cash_balances)}개 증권사 계좌의 예수금 정보")

                # 데이터프레임 생성
                balances_df = pd.DataFrame(cash_balances)
                balances_df["krw_formatted"] = balances_df["krw"].apply(
                    lambda x: f"₩{x:,.0f}"
                )
                balances_df["usd_formatted"] = balances_df["usd"].apply(
                    lambda x: f"${x:,.2f}"
                )
                balances_df["total_krw"] = balances_df["krw"] + (
                    balances_df["usd"] * 1400
                )  # USD 환산

                # 데이터 테이블
                st.dataframe(
                    balances_df[
                        ["account", "krw_formatted", "usd_formatted", "total_krw"]
                    ],
                    column_config={
                        "account": "증권사",
                        "krw_formatted": "KRW 예수금",
                        "usd_formatted": "USD 예수금",
                        "total_krw": "총액 (KRW)",
                    },
                    width="stretch",
                    hide_index=True,
                )

                # 예수금 업데이트 섹션
                st.subheader("✏️ 예수금 업데이트")

                # 계좌 선택
                if cash_balances:
                    selected_balance_account = st.selectbox(
                        "업데이트할 계좌 선택",
                        options=[cb["account"] for cb in cash_balances],
                        index=0,
                    )

                    # 선택된 계좌의 현재 정보
                    current_balance = next(
                        (
                            cb
                            for cb in cash_balances
                            if cb["account"] == selected_balance_account
                        ),
                        None,
                    )

                    if current_balance:
                        col1, col2 = st.columns(2)

                        with col1:
                            st.info(f"현재 {selected_balance_account} 계좌")
                            st.metric("KRW", f"₩{current_balance['krw']:,.0f}")
                            st.metric("USD", f"${current_balance['usd']:,.2f}")

                        with col2:
                            st.write("새로운 금액 입력")
                            new_krw = st.number_input(
                                "새 KRW 예수금",
                                value=float(current_balance["krw"]),
                                min_value=0.0,
                                format="%.0f",
                                step=1000.0,
                            )
                            new_usd = st.number_input(
                                "새 USD 예수금",
                                value=float(current_balance["usd"]),
                                min_value=0.0,
                                format="%.2f",
                                step=0.01,
                            )

                        # 업데이트 버튼
                        if st.button("💾 예수금 업데이트", use_container_width=True):
                            if update_cash_balance(
                                selected_balance_account, new_krw, new_usd
                            ):
                                st.rerun()

            else:
                st.warning("예수금 정보가 없습니다.")

        # 탭3: 예적금 관리
        with tab3:
            st.subheader("💎 예적금 관리")

            # 예적금 데이터 조회
            time_deposits = fetch_time_deposits()

            if time_deposits:
                st.info(f"📋 현재 {len(time_deposits)}개 예적금 정보")

                # 데이터프레임 생성
                deposits_df = pd.DataFrame(time_deposits)
                deposits_df["market_value_formatted"] = deposits_df[
                    "market_value"
                ].apply(lambda x: f"₩{x:,.0f}")
                deposits_df["invested_principal_formatted"] = deposits_df[
                    "invested_principal"
                ].apply(lambda x: f"₩{x:0,}")
                deposits_df["maturity_date_formatted"] = deposits_df[
                    "maturity_date"
                ].apply(lambda x: x if pd.notna(x) else "-")
                deposits_df["interest_rate_formatted"] = deposits_df[
                    "interest_rate"
                ].apply(lambda x: f"{x:.2f}%" if pd.notna(x) else "-")

                # 데이터 테이블
                st.dataframe(
                    deposits_df[
                        [
                            "account",
                            "invest_prod_name",
                            "market_value_formatted",
                            "invested_principal_formatted",
                            "maturity_date_formatted",
                            "interest_rate_formatted",
                        ]
                    ],
                    column_config={
                        "account": "계좌",
                        "invest_prod_name": "상품명",
                        "market_value_formatted": "현재 평가액",
                        "invested_principal_formatted": "예치원금",
                        "maturity_date_formatted": "만기일",
                        "interest_rate_formatted": "이율",
                    },
                    width="stretch",
                    hide_index=True,
                )

                # 예적금 관리 섹션
                st.subheader("⚙️ 예적금 관리")

                operation = st.selectbox(
                    "작업 선택", ["예적금 추가", "예적금 수정", "예적금 삭제"]
                )

                if operation == "예적금 추가":
                    st.subheader("➕ 새 예적금 추가")

                    with st.form("add_deposit_form"):
                        account = st.text_input("계정명", value="")
                        prod_name = st.text_input("상품명")
                        market_value = st.number_input(
                            "현재 평가액", min_value=0, value=1000000, step=10000
                        )
                        invested_principal = st.number_input(
                            "예치원금", min_value=0, value=1000000, step=10000
                        )
                        maturity_date = st.date_input("만기일 (선택사)")
                        interest_rate = st.number_input(
                            "이율 (%)",
                            min_value=0.0,
                            max_value=20.0,
                            value=0.0,
                            step=0.1,
                        )

                        submitted = st.form_submit_button(
                            "💾 예적금 생성", use_container_width=True
                        )

                        if submitted:
                            if (
                                account
                                and prod_name
                                and market_value > 0
                                and invested_principal > 0
                            ):
                                create_time_deposit(
                                    account,
                                    prod_name,
                                    market_value,
                                    invested_principal,
                                    maturity_date,
                                    interest_rate,
                                )
                                st.rerun()

                elif operation == "예적금 수정":
                    st.subheader("✏️ 예적금 수정")

                    if time_deposits:
                        # 수정할 예적금 선택
                        deposit_to_edit = st.selectbox(
                            "수정할 예적금 선택",
                            options=[
                                f"{td['account']} - {td['invest_prod_name']}"
                                for td in time_deposits
                            ],
                        )

                        if deposit_to_edit:
                            # 선택된 예적금 정보 파싱
                            selected_deposit = next(
                                (
                                    td
                                    for td in time_deposits
                                    if f"{td['account']} - {td['invest_prod_name']}"
                                    == deposit_to_edit
                                ),
                                None,
                            )

                            with st.form("edit_deposit_form"):
                                account = st.text_input(
                                    "계정명",
                                    value=selected_deposit["account"],
                                    disabled=True,
                                )
                                prod_name = st.text_input(
                                    "상품명",
                                    value=selected_deposit["invest_prod_name"],
                                    disabled=True,
                                )
                                market_value = st.number_input(
                                    "현재 평가액",
                                    min_value=0,
                                    value=int(selected_deposit["market_value"]),
                                    step=10000,
                                )
                                invested_principal = st.number_input(
                                    "예치원금",
                                    min_value=0,
                                    value=int(selected_deposit["invested_principal"]),
                                    step=10000,
                                )
                                maturity_date = st.date_input(
                                    "만기일 (선택사)",
                                    value=(
                                        pd.to_datetime(
                                            selected_deposit["maturity_date"]
                                        )
                                        if selected_deposit["maturity_date"]
                                        else datetime.now()
                                    ),
                                )
                                interest_rate = st.number_input(
                                    "이율 (%)",
                                    min_value=0.0,
                                    max_value=20.0,
                                    value=float(
                                        selected_deposit["interest_rate"] or 0.0
                                    ),
                                    step=0.1,
                                )

                                submitted = st.form_submit_button(
                                    "💾 예적금 수정", use_container_width=True
                                )

                                if submitted:
                                    if update_time_deposit(
                                        account,
                                        prod_name,
                                        market_value,
                                        invested_principal,
                                        maturity_date,
                                        interest_rate,
                                    ):
                                        # 예적금 데이터만 다시 조회
                                        time_deposits = fetch_time_deposits()

                elif operation == "예적금 삭제":
                    st.subheader("🗑️ 예적금 삭제")

                    if time_deposits:
                        deposit_to_delete = st.selectbox(
                            "삭제할 예적금 선택",
                            options=[
                                f"{td['account']} - {td['invest_prod_name']}"
                                for td in time_deposits
                            ],
                        )

                        if deposit_to_delete:
                            # 선택된 예적금 정보 파싱
                            parts = deposit_to_delete.split(" - ", 1)
                            account, prod_name = parts[0], parts[1]

                            st.warning(
                                f"⚠️ 정말로 삭제하시겠습니까? **{deposit_to_delete}**"
                            )

                            if st.button("🗑️ 예적금 삭제", type="secondary"):
                                if delete_time_deposit(account, prod_name):
                                    st.rerun()
            else:
                st.warning("예적금 정보가 없습니다.")

        

    else:
        st.warning(
            "현금 관리 데이터를 불러올 수 없습니다. API 서버가 실행 중인지 확인해주세요."
        )

# 성과 분석 페이지
elif selected_page == "📊 성과 분석":
    st.header("📊 성과 분석")
    st.info("성과 분석 기능은 다음 단계에서 구현될 예정입니다.")

# 설정 페이지
elif selected_page == "⚙️ 설정":
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
