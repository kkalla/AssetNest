"""
AssetNest 대시보드 메인 애플리케이션
"""
import os
import sys
from typing import Dict, Any, Optional

import streamlit as st

# 프로젝트 루트를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 모듈 임포트
from logger import get_dashboard_logger
from config import settings
from components import LayoutComponents
from page_modules import (
    PortfolioOverviewPage,
    HoldingsPage,
    AssetAllocationPage,
    CashManagementPage,
    PerformancePage,
    SettingsPage
)
from utils import StateManager, PageType

# 대시보드 로거
dashboard_logger = get_dashboard_logger("Main")


def create_page_router() -> Dict[str, Any]:
    """페이지 라우터 생성"""
    page_map = {
        PageType.PORTFOLIO_OVERVIEW.value: PortfolioOverviewPage.render,
        PageType.ASSET_ALLOCATION.value: AssetAllocationPage.render,
        PageType.CASH_MANAGEMENT.value: CashManagementPage.render,
        PageType.HOLDINGS.value: HoldingsPage.render,
        PageType.PERFORMANCE.value: PerformancePage.render,
        PageType.SETTINGS.value: SettingsPage.render,
    }

    return page_map


def render_current_page():
    """현재 선택된 페이지 렌더링"""
    selected_page = StateManager.get_selected_page()
    page_router = create_page_router()

    page_renderer = page_router.get(selected_page)
    if page_renderer:
        try:
            dashboard_logger.info(f"🔄 페이지 렌더링: {selected_page}")
            page_renderer()
            dashboard_logger.info(f"✅ 페이지 렌더링 완료: {selected_page}")
        except Exception as e:
            dashboard_logger.error(f"💥 페이지 렌더링 오류 ({selected_page}): {str(e)}")
            st.error(f"페이지 로딩 중 오류가 발생했습니다: {e}")
    else:
        dashboard_logger.warning(f"⚠️ 페이지를 찾을 수 없음: {selected_page}")
        LayoutComponents.create_warning_box(
            "페이지를 찾을 수 없습니다",
            f"'{selected_page}' 페이지를 찾을 수 없습니다. 기본 페이지로 이동합니다.",
            "❌"
        )


def handle_error_boundary():
    """에러 경계 처리"""
    try:
        # 에러 페이지가 아닌 경우 기본 페이지로 이동
        if not StateManager.is_page_selected(PageType.PORTFOLIO_OVERVIEW):
            StateManager.navigate_to_page(PageType.PORTFOLIO_OVERVIEW)
        else:
            # 이미 기본 페이지인 경우 에러 메시지 표시
            LayoutComponents.create_error_box(
                "시스템 오류",
                "대시보드를 로드하는 중 오류가 발생했습니다. 나중에 다시 시도해주세요.",
                "🚨"
            )
    except Exception as e:
        dashboard_logger.error(f"💥 에러 경계 처리 실패: {str(e)}")
        st.error("치명적인 시스템 오류가 발생했습니다. 관리자에게 문의해주세요.")


def main():
    """메인 애플리케이션 실행 함수"""
    try:
        # 페이지 설정
        st.set_page_config(
            page_title=settings.PAGE_TITLE,
            page_icon=settings.PAGE_ICON,
            layout=settings.PAGE_LAYOUT,
            initial_sidebar_state="expanded",
        )

        # 대시보드 초기화
        is_new_session = StateManager.initialize_dashboard()
        if is_new_session:
            dashboard_logger.info("🚀 AssetNest 대시보드 새 세션 시작")

        # 사이드바 생성
        selected_page = LayoutComponents.create_sidebar()

        # 메인 컨텐츠 헤더
        st.title(settings.PAGE_TITLE)

        # 사용자 액션 로깅
        dashboard_logger.info(f"👤 사용자 페이지 접속: {selected_page}")

        # 현재 페이지 렌더링
        render_current_page()

        # 애플리케이션 푸터
        LayoutComponents.create_footer()

        # 세션 상태 로깅 (디버그용)
        if StateManager.get_user_preference("debug_mode", False):
            with st.expander("🔧 디버그 정보", expanded=False):
                navigation_state = StateManager.get_navigation_state()
                st.json(navigation_state)

    except Exception as e:
        dashboard_logger.error(f"💥 메인 애플리케이션 오류: {str(e)}")
        handle_error_boundary()


if __name__ == "__main__":
    main()