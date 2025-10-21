"""
상태 관리 유틸리티
"""
import streamlit as st
from typing import Any, Optional, Dict
from enum import Enum


class PageType(Enum):
    """페이지 타입 열거형"""
    PORTFOLIO_OVERVIEW = "📈 포트폴리오 개요"
    ASSET_ALLOCATION = "🥧 자산 분배"
    HOLDINGS = "💼 보유 종목"
    CASH_MANAGEMENT = "💰 현금 관리"
    PERFORMANCE = "📊 성과 분석"
    SETTINGS = "⚙️ 설정"


class StateManager:
    """Streamlit 세션 상태 관리자"""

    # 상태 키 상수
    KEY_DASHBOARD_INITIALIZED = "dashboard_initialized"
    KEY_SELECTED_PAGE = "selected_page"
    KEY_FILTERS = "filters"
    KEY_USER_PREFERENCES = "user_preferences"

    @classmethod
    def initialize_dashboard(cls) -> bool:
        """대시보드 초기화"""
        if cls.KEY_DASHBOARD_INITIALIZED not in st.session_state:
            st.session_state[cls.KEY_DASHBOARD_INITIALIZED] = True

            # 기본값 설정
            cls.set_selected_page(PageType.PORTFOLIO_OVERVIEW.value)
            cls.initialize_filters()
            cls.initialize_user_preferences()

            return True
        return False

    @classmethod
    def get_selected_page(cls) -> str:
        """선택된 페이지 가져오기"""
        return st.session_state.get(cls.KEY_SELECTED_PAGE, PageType.PORTFOLIO_OVERVIEW.value)

    @classmethod
    def set_selected_page(cls, page: str):
        """선택된 페이지 설정"""
        st.session_state[cls.KEY_SELECTED_PAGE] = page

    @classmethod
    def initialize_filters(cls):
        """필터 초기화"""
        if cls.KEY_FILTERS not in st.session_state:
            st.session_state[cls.KEY_FILTERS] = {
                "holdings": {
                    "min_value": 0,
                    "min_return": -100.0,
                    "max_return": 1000.0,
                    "selected_account": None,
                    "selected_market": None
                },
                "allocation": {
                    "selected_account": None,
                    "simulation_type": "cash_vs_investment"
                },
                "cash": {
                    "selected_account": None,
                    "operation_type": "create"
                }
            }

    @classmethod
    def get_filters(cls, category: str) -> Dict[str, Any]:
        """특정 카테고리의 필터 가져오기"""
        filters = st.session_state.get(cls.KEY_FILTERS, {})
        return filters.get(category, {})

    @classmethod
    def update_filter(cls, category: str, key: str, value: Any):
        """필터 값 업데이트"""
        if cls.KEY_FILTERS not in st.session_state:
            cls.initialize_filters()

        st.session_state[cls.KEY_FILTERS][category][key] = value

    @classmethod
    def initialize_user_preferences(cls):
        """사용자偏好 초기화"""
        if cls.KEY_USER_PREFERENCES not in st.session_state:
            st.session_state[cls.KEY_USER_PREFERENCES] = {
                "theme": "dark",
                "currency_format": "KRW",
                "auto_refresh": False,
                "refresh_interval": 300,  # 5분
                "chart_height": 400,
                "show_animation": True
            }

    @classmethod
    def get_user_preference(cls, key: str, default: Any = None) -> Any:
        """사용자偏好 가져오기"""
        preferences = st.session_state.get(cls.KEY_USER_PREFERENCES, {})
        return preferences.get(key, default)

    @classmethod
    def set_user_preference(cls, key: str, value: Any):
        """사용자偏好 설정"""
        if cls.KEY_USER_PREFERENCES not in st.session_state:
            cls.initialize_user_preferences()

        st.session_state[cls.KEY_USER_PREFERENCES][key] = value

    @classmethod
    def create_page_button(cls, page_name: str, page_key: str):
        """페이지 버튼 생성 및 상태 관리"""
        if st.sidebar.button(page_name, use_container_width=True, key=page_key):
            cls.set_selected_page(page_name)
            st.rerun()

    @classmethod
    def reset_filters(cls, category: Optional[str] = None):
        """필터 리셋"""
        if category:
            # 특정 카테고리 필터만 리셋
            cls.initialize_filters()
        else:
            # 전체 필터 리셋
            if cls.KEY_FILTERS in st.session_state:
                del st.session_state[cls.KEY_FILTERS]
            cls.initialize_filters()

    @classmethod
    def get_cache_key(cls, base_key: str, *args, **kwargs) -> str:
        """캐시 키 생성"""
        parts = [base_key]
        parts.extend(str(arg) for arg in args)
        parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
        return "_".join(parts)

    @classmethod
    def clear_all_cache(cls):
        """모든 캐시 초기화"""
        st.cache_data.clear()

    @classmethod
    def is_page_selected(cls, page: PageType) -> bool:
        """특정 페이지가 선택되었는지 확인"""
        return cls.get_selected_page() == page.value

    @classmethod
    def navigate_to_page(cls, page: PageType):
        """특정 페이지로 이동"""
        cls.set_selected_page(page.value)
        st.rerun()

    @classmethod
    def get_navigation_state(cls) -> Dict[str, Any]:
        """네비게이션 상태 정보 반환"""
        return {
            "current_page": cls.get_selected_page(),
            "available_pages": [page.value for page in PageType],
            "filters": st.session_state.get(cls.KEY_FILTERS, {}),
            "preferences": st.session_state.get(cls.KEY_USER_PREFERENCES, {})
        }