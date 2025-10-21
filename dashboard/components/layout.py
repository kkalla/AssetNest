"""
레이아웃 컴포넌트
"""
import streamlit as st
import pandas as pd
from typing import List, Dict, Any, Optional, Callable

from dashboard.config import settings
from dashboard.utils import StateManager, format_currency


class LayoutComponents:
    """레이아웃 컴포넌트 클래스"""

    @staticmethod
    def create_sidebar() -> str:
        """
        사이드바 생성

        Returns:
            str: 선택된 페이지
        """
        # 사이드바 타이틀
        st.sidebar.title("💼 AssetNest")
        st.sidebar.markdown("효율적인 자산관리 대쉬보드")

        # 페이지 선택
        st.sidebar.subheader("📑 페이지 선택")

        # 페이지 버튼들 생성
        pages = [
            ("📈 포트폴리오 개요", "portfolio_overview"),
            ("🥧 자산 분배", "asset_allocation"),
            ("💰 현금 관리", "cash_management"),
            ("💼 보유 종목", "holdings"),
            ("📊 성과 분석", "performance"),
            ("⚙️ 설정", "settings")
        ]

        for page_name, page_key in pages:
            if st.sidebar.button(page_name, use_container_width=True, key=page_key):
                StateManager.set_selected_page(page_name)
                st.rerun()

        # 현재 선택된 페이지 표시
        selected_page = StateManager.get_selected_page()
        st.sidebar.markdown(f"**현재 페이지:** {selected_page}")

        # 데이터 관리 섹션
        st.sidebar.subheader("⚙️ 데이터 관리")
        LayoutComponents._create_data_management_section()

        return selected_page

    @staticmethod
    def _create_data_management_section():
        """데이터 관리 섹션 생성"""
        col1, col2 = st.sidebar.columns(2)

        with col1:
            if st.button("💰 가격 업데이트", type="primary", key="update_prices"):
                with st.spinner("업데이트 중..."):
                    from dashboard.api import holdings_api
                    success = holdings_api.refresh_prices()
                    if success:
                        st.success("주식 가격이 업데이트되었습니다!")
                        StateManager.clear_all_cache()
                        st.rerun()

        with col2:
            if st.button("🔄 새로고침", key="refresh_cache"):
                StateManager.clear_all_cache()
                st.success("캐시가 초기화되었습니다!")
                st.rerun()

    @staticmethod
    def create_header(title: str, subtitle: Optional[str] = None):
        """
        페이지 헤더 생성

        Args:
            title (str): 페이지 제목
            subtitle (Optional[str]): 부제목
        """
        st.header(title)
        if subtitle:
            st.markdown(subtitle)

    @staticmethod
    def create_data_table(
        data: pd.DataFrame,
        column_config: Optional[Dict[str, str]] = None,
        width: str = "stretch",
        hide_index: bool = True,
        height: Optional[int] = None
    ):
        """
        데이터 테이블 생성

        Args:
            data (pd.DataFrame): 데이터프레임
            column_config (Optional[Dict[str, str]]): 컬럼 설정
            width (str): 너비 설정
            hide_index (bool): 인덱스 숨김 여부
            height (Optional[int]): 높이 설정
        """
        if data.empty:
            st.info("데이터가 없습니다.")
            return

        st.dataframe(
            data,
            column_config=column_config,
            width=width,
            hide_index=hide_index,
            height=height
        )

    @staticmethod
    def create_info_box(title: str, content: str, icon: str = "ℹ️"):
        """
        정보 박스 생성

        Args:
            title (str): 제목
            content (str): 내용
            icon (str): 아이콘
        """
        st.markdown(f"#### {icon} {title}")
        st.info(content)

    @staticmethod
    def create_warning_box(title: str, content: str, icon: str = "⚠️"):
        """
        경고 박스 생성

        Args:
            title (str): 제목
            content (str): 내용
            icon (str): 아이콘
        """
        st.markdown(f"#### {icon} {title}")
        st.warning(content)

    @staticmethod
    def create_success_box(title: str, content: str, icon: str = "✅"):
        """
        성공 박스 생성

        Args:
            title (str): 제목
            content (str): 내용
            icon (str): 아이콘
        """
        st.markdown(f"#### {icon} {title}")
        st.success(content)

    @staticmethod
    def create_error_box(title: str, content: str, icon: str = "❌"):
        """
        에러 박스 생성

        Args:
            title (str): 제목
            content (str): 내용
            icon (str): 아이콘
        """
        st.markdown(f"#### {icon} {title}")
        st.error(content)

    @staticmethod
    def create_tab_interface(tab_names: List[str], tab_contents: List[Callable]):
        """
        탭 인터페이스 생성

        Args:
            tab_names (List[str]): 탭 이름 리스트
            tab_contents (List[Callable]): 탭 컨텐츠 함수 리스트
        """
        if len(tab_names) != len(tab_contents):
            st.error("탭 이름과 컨텐츠 함수의 수가 일치하지 않습니다.")
            return

        tabs = st.tabs(tab_names)

        for i, (tab, content_func) in enumerate(zip(tabs, tab_contents)):
            with tab:
                content_func()

    @staticmethod
    def create_expandable_section(title: str, content_func: Callable, expanded: bool = False):
        """
        확장 가능한 섹션 생성

        Args:
            title (str): 섹션 제목
            content_func (Callable): 컨텐츠 함수
            expanded (bool): 초기 확장 여부
        """
        with st.expander(title, expanded=expanded):
            content_func()

    @staticmethod
    def create_loading_section(message: str = "로딩 중..."):
        """
        로딩 섹션 생성

        Args:
            message (str): 로딩 메시지
        """
        with st.spinner(message):
            st.empty()  # 로딩 공간 확보

    @staticmethod
    def create_empty_state(message: str, icon: str = "📭"):
        """
        빈 상태 표시

        Args:
            message (str): 메시지
            icon (str): 아이콘
        """
        st.markdown(f"""
        <div style="text-align: center; padding: 2rem;">
            <div style="font-size: 3rem;">{icon}</div>
            <h3>{message}</h3>
        </div>
        """, unsafe_allow_html=True)

    @staticmethod
    def create_footer():
        """푸터 생성"""
        st.markdown("---")
        st.markdown("💼 **AssetNest** - 효율적인 자산관리를 위한 대쉬보드 v1.0")

    @staticmethod
    def create_page_layout(
        title: str,
        content_func: Callable,
        sidebar_func: Optional[Callable] = None,
        show_footer: bool = True
    ):
        """
        전체 페이지 레이아웃 생성

        Args:
            title (str): 페이지 제목
            content_func (Callable): 메인 컨텐츠 함수
            sidebar_func (Optional[Callable]): 사이드바 함수
            show_footer (bool): 푸터 표시 여부
        """
        # 페이지 설정
        st.set_page_config(
            page_title=settings.PAGE_TITLE,
            page_icon=settings.PAGE_ICON,
            layout=settings.PAGE_LAYOUT,
            initial_sidebar_state="expanded",
        )

        # 사이드바
        if sidebar_func:
            sidebar_func()
        else:
            LayoutComponents.create_sidebar()

        # 메인 컨텐츠
        st.title(settings.PAGE_TITLE)

        # 대시보드 초기화 확인
        if StateManager.initialize_dashboard():
            from logger import dashboard_logger
            dashboard_logger.info("🚀 AssetNest 대시보드 세션 시작")

        # 페이지 헤더
        LayoutComponents.create_header(title)

        # 메인 컨텐츠
        content_func()

        # 푸터
        if show_footer:
            LayoutComponents.create_footer()

    @staticmethod
    def create_metric_grid(metrics: List[Dict[str, Any]], columns: int = 4):
        """
        메트릭 그리드 생성

        Args:
            metrics (List[Dict[str, Any]]): 메트릭 리스트
            columns (int): 컬럼 수
        """
        cols = st.columns(columns)

        for i, metric in enumerate(metrics):
            with cols[i % columns]:
                st.metric(
                    label=metric.get("label", ""),
                    value=metric.get("value", ""),
                    delta=metric.get("delta"),
                    delta_color=metric.get("delta_color", "normal"),
                    help=metric.get("help")
                )

    @staticmethod
    def create_two_column_layout(
        left_content: Callable,
        right_content: Callable,
        ratio: List[float] = [1, 1]
    ):
        """
        2단 컬럼 레이아웃 생성

        Args:
            left_content (Callable): 왼쪽 컨텐츠 함수
            right_content (Callable): 오른쪽 컨텐츠 함수
            ratio (List[float]): 컬럼 비율
        """
        col1, col2 = st.columns(ratio)

        with col1:
            left_content()

        with col2:
            right_content()

    @staticmethod
    def create_three_column_layout(
        left_content: Callable,
        middle_content: Callable,
        right_content: Callable,
        ratio: List[float] = [1, 1, 1]
    ):
        """
        3단 컬럼 레이아웃 생성

        Args:
            left_content (Callable): 왼쪽 컨텐츠 함수
            middle_content (Callable): 중앙 컨텐츠 함수
            right_content (Callable): 오른쪽 컨텐츠 함수
            ratio (List[float]): 컬럼 비율
        """
        col1, col2, col3 = st.columns(ratio)

        with col1:
            left_content()

        with col2:
            middle_content()

        with col3:
            right_content()