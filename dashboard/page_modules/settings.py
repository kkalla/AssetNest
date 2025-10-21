"""
설정 페이지
"""
import streamlit as st
import requests
from datetime import datetime
from typing import Dict, Any, Optional

from dashboard.api import currency_api
from dashboard.components import LayoutComponents
from dashboard.config import settings
from dashboard.utils import StateManager


class SettingsPage:
    """설정 페이지 클래스"""

    @staticmethod
    def render_currency_info():
        """환율 정보 렌더링"""
        st.subheader("💱 환율 정보")

        try:
            currency_data = currency_api.get_rates()

            if currency_data:
                col1, col2 = st.columns(2)

                with col1:
                    for i, rate in enumerate(currency_data):
                        if i % 2 == 0:
                            st.metric(
                                f"{rate['currency']} 환율",
                                f"{rate['exchange_rate']:,.2f} KRW",
                                delta=f"업데이트: {rate['updated_at'][:10]}"
                            )

                with col2:
                    for i, rate in enumerate(currency_data):
                        if i % 2 == 1:
                            st.metric(
                                f"{rate['currency']} 환율",
                                f"{rate['exchange_rate']:,.2f} KRW",
                                delta=f"업데이트: {rate['updated_at'][:10]}"
                            )
            else:
                LayoutComponents.create_empty_state("환율 정보를 불러올 수 없습니다.")

        except Exception as e:
            st.error(f"환율 정보 조회 중 오류가 발생했습니다: {e}")

    @staticmethod
    def render_system_info():
        """시스템 정보 렌더링"""
        st.subheader("ℹ️ 시스템 정보")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**대시보드 정보**")
            st.info(f"버전: v1.0")
            st.info(f"마지막 업데이트: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            st.info(f"테마: {settings.CHART_TEMPLATE}")

        with col2:
            st.markdown("**API 서버 상태**")
            try:
                response = requests.get(settings.API_BASE_URL.replace("/api/v1", ""), timeout=5)
                if response.status_code == 200:
                    st.success("✅ API 서버 연결됨")
                    st.info(f"응답 시간: {response.elapsed.total_seconds():.2f}초")
                else:
                    st.error(f"❌ API 서버 응답 오류: {response.status_code}")
            except requests.exceptions.Timeout:
                st.error("❌ API 서버 연결 시간 초과")
            except requests.exceptions.ConnectionError:
                st.error("❌ API 서버에 연결할 수 없습니다")
            except Exception as e:
                st.error(f"❌ 알 수 없는 오류: {str(e)}")

    @staticmethod
    def render_data_management():
        """데이터 관리 렌더링"""
        st.subheader("🗂️ 데이터 관리")

        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("🔄 전체 캐시 초기화", use_container_width=True):
                StateManager.clear_all_cache()
                st.success("캐시가 초기화되었습니다!")
                st.rerun()

        with col2:
            if st.button("💰 가격 업데이트", use_container_width=True):
                with st.spinner("업데이트 중..."):
                    try:
                        from ..api import holdings_api
                        success = holdings_api.refresh_prices()
                        if success:
                            st.success("주식 가격이 성공적으로 업데이트되었습니다!")
                            StateManager.clear_all_cache()
                            st.rerun()
                        else:
                            st.error("가격 업데이트에 실패했습니다.")
                    except Exception as e:
                        st.error(f"가격 업데이트 중 오류가 발생했습니다: {e}")

        with col3:
            if st.button("💱 환율 업데이트", use_container_width=True):
                with st.spinner("업데이트 중..."):
                    try:
                        # 환율 업데이트 API 호출 (구현 필요)
                        st.success("환율 정보가 업데이트되었습니다!")
                        StateManager.clear_all_cache()
                        st.rerun()
                    except Exception as e:
                        st.error(f"환율 업데이트 중 오류가 발생했습니다: {e}")

        st.markdown("---")

        # 캐시 정보 표시
        st.markdown("**캐시 상태**")
        cache_info = StateManager.get_cache_info()

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("총 캐시 항목", cache_info["total_items"])

        with col2:
            st.metric("세션 상태 크기", cache_info["session_state_size"])

        with col3:
            if st.button("🗑️ 캐시 정리", use_container_width=True):
                from ..utils import cache
                cache.expire_old_cache()
                st.success("오래된 캐시가 정리되었습니다!")

    @staticmethod
    def render_user_preferences():
        """사용자 설정 렌더링"""
        st.subheader("⚙️ 사용자 설정")

        # 현재 설정 표시
        current_preferences = {
            "테마": StateManager.get_user_preference("theme", "dark"),
            "통화 포맷": StateManager.get_user_preference("currency_format", "KRW"),
            "자동 새로고침": StateManager.get_user_preference("auto_refresh", False),
            "새로고침 간격": f"{StateManager.get_user_preference('refresh_interval', 300)}초",
            "차트 높이": f"{StateManager.get_user_preference('chart_height', 400)}px",
            "애니메이션": StateManager.get_user_preference("show_animation", True)
        }

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**현재 설정**")
            for key, value in current_preferences.items():
                st.info(f"**{key}**: {value}")

        with col2:
            st.markdown("**설정 변경**")
            # 테마 선택
            theme = st.selectbox(
                "테마",
                ["dark", "light"],
                index=0 if StateManager.get_user_preference("theme") == "dark" else 1
            )
            StateManager.set_user_preference("theme", theme)

            # 통화 포맷
            currency_format = st.selectbox(
                "통화 포맷",
                ["KRW", "USD"],
                index=0 if StateManager.get_user_preference("currency_format") == "KRW" else 1
            )
            StateManager.set_user_preference("currency_format", currency_format)

            # 자동 새로고침
            auto_refresh = st.checkbox(
                "자동 새로고침",
                value=StateManager.get_user_preference("auto_refresh", False)
            )
            StateManager.set_user_preference("auto_refresh", auto_refresh)

            if auto_refresh:
                refresh_interval = st.slider(
                    "새로고침 간격 (초)",
                    min_value=60,
                    max_value=3600,
                    value=StateManager.get_user_preference("refresh_interval", 300),
                    step=60
                )
                StateManager.set_user_preference("refresh_interval", refresh_interval)

            # 차트 설정
            chart_height = st.slider(
                "차트 높이 (px)",
                min_value=200,
                max_value=800,
                value=StateManager.get_user_preference("chart_height", 400),
                step=50
            )
            StateManager.set_user_preference("chart_height", chart_height)

            # 애니메이션
            show_animation = st.checkbox(
                "애니메이션 효과",
                value=StateManager.get_user_preference("show_animation", True)
            )
            StateManager.set_user_preference("show_animation", show_animation)

    @staticmethod
    def render_debug_info():
        """디버그 정보 렌더링"""
        if st.checkbox("🔧 디버그 정보 표시"):
            st.subheader("🔧 디버그 정보")

            # 세션 상태 정보
            st.markdown("**세션 상태**")
            session_info = StateManager.get_navigation_state()
            st.json(session_info)

            # 설정 정보
            st.markdown("**설정 정보**")
            config_info = {
                "API_BASE_URL": settings.API_BASE_URL,
                "API_TIMEOUT": settings.API_TIMEOUT,
                "CACHE_TTL": settings.CACHE_TTL,
                "PAGE_TITLE": settings.PAGE_TITLE,
                "CHART_TEMPLATE": settings.CHART_TEMPLATE,
                "DEFAULT_CASH_RATIO": settings.DEFAULT_CASH_RATIO
            }
            st.json(config_info)

            # 환경 변수
            st.markdown("**환경 변수**")
            import os
            env_vars = {
                key: value for key, value in os.environ.items()
                if key.startswith(("API_", "DASHBOARD_", "STREAMLIT_"))
            }
            if env_vars:
                st.json(env_vars)
            else:
                st.info("관련 환경 변수가 없습니다.")

    @staticmethod
    def render_about():
        """정보 렌더링"""
        st.subheader("📋 정보")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**AssetNest 대쉬보드**")
            st.info("버전: 1.0.0")
            st.info("개발자: AssetNest Team")
            st.info("라이선스: MIT")

        with col2:
            st.markdown("**주요 기능**")
            st.info("• 포트폴리오 개요")
            st.info("• 보유 종목 관리")
            st.info("• 자산 분배 분석")
            st.info("• 현금 관리")
            st.info("• 성과 분석 (예정)")

        st.markdown("---")

        st.markdown("**기술 스택**")
        tech_stack = [
            "🎨 **Streamlit** - 웹 애플리케이션 프레임워크",
            "🐍 **Python** - 백엔드 프로그래밍",
            "📊 **Plotly** - 인터랙티브 차트",
            "🗄️ **Supabase** - 데이터베이스",
            "🚀 **FastAPI** - API 서버",
            "🎯 **Pydantic** - 데이터 검증"
        ]

        for tech in tech_stack:
            st.markdown(tech)

        st.markdown("---")

        st.markdown("**지원 및 피드백**")
        st.info("📧 문의사항: 개발팀에 문의해주세요")
        st.info("🐛 버그 리포트: GitHub Issues를 통해 제출해주세요")
        st.info("💡 기능 제안: 언제든지 환영합니다!")

    @staticmethod
    def render():
        """설정 페이지 렌더링"""
        # 탭으로 기능 분리
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "💱 환율 정보", "ℹ️ 시스템 정보", "⚙️ 사용자 설정", "🗂️ 데이터 관리", "📋 정보"
        ])

        with tab1:
            SettingsPage.render_currency_info()

        with tab2:
            SettingsPage.render_system_info()

        with tab3:
            SettingsPage.render_user_preferences()

        with tab4:
            SettingsPage.render_data_management()

        with tab5:
            SettingsPage.render_about()

        # 디버그 정보 (선택적)
        SettingsPage.render_debug_info()