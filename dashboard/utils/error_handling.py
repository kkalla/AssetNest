"""
에러 처리 유틸리티
"""
import logging
import traceback
from typing import Any, Dict, Optional, Callable
from functools import wraps
import streamlit as st

from .formatters import format_currency, format_number


class DashboardError(Exception):
    """대시보드 커스텀 예외 클래스"""

    def __init__(self, message: str, error_code: Optional[str] = None, context: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.context = context or {}


class DataLoadError(DashboardError):
    """데이터 로딩 오류"""
    pass


class APIError(DashboardError):
    """API 호출 오류"""
    pass


class ValidationError(DashboardError):
    """데이터 검증 오류"""
    pass


class CacheError(DashboardError):
    """캐시 오류"""
    pass


def error_boundary(error_message: str = "오류가 발생했습니다"):
    """
    에러 경계 데코레이터

    Args:
        error_message (str): 사용자에게 표시할 에러 메시지
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except DashboardError as e:
                logger = logging.getLogger(func.__module__)
                logger.error(f"💥 DashboardError in {func.__name__}: {e.message}")
                logger.debug(f"🔍 Error context: {e.context}")
                st.error(f"{error_message}: {e.message}")
                return None
            except Exception as e:
                logger = logging.getLogger(func.__module__)
                logger.error(f"💥 Unexpected error in {func.__name__}: {str(e)}")
                logger.debug(f"🔍 Traceback: {traceback.format_exc()}")
                st.error(f"{error_message}: 예상치 못은 오류가 발생했습니다.")
                return None
        return wrapper
    return decorator


def handle_api_errors(func: Callable) -> Callable:
    """
    API 호출 에러 핸들링 데코레이터

    Args:
        func (Callable): API 호출 함수
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger = logging.getLogger(func.__module__)
            error_msg = f"API 호출 실패: {str(e)}"
            logger.error(f"💥 {error_msg}")

            # 사용자 친화적인 에러 메시지
            if "timeout" in str(e).lower():
                user_msg = "서버 응답 시간이 초과되었습니다. 잠시 후 다시 시도해주세요."
            elif "connection" in str(e).lower():
                user_msg = "서버에 연결할 수 없습니다. 인터넷 연결을 확인해주세요."
            elif "404" in str(e):
                user_msg = "요청한 데이터를 찾을 수 없습니다."
            elif "500" in str(e):
                user_msg = "서버 내부 오류가 발생했습니다. 잠시 후 다시 시도해주세요."
            else:
                user_msg = f"데이터 조회 중 오류가 발생했습니다: {str(e)}"

            st.error(user_msg)
            return None
    return wrapper


def safe_execute(func: Callable, default_return: Any = None, show_error: bool = True) -> Callable:
    """
    안전한 실행 데코레이터

    Args:
        func (Callable): 실행할 함수
        default_return (Any): 오류 시 반환할 기본값
        show_error (bool): 에러 메시지 표시 여부
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger = logging.getLogger(func.__module__)
            logger.error(f"💥 Safe execution failed in {func.__name__}: {str(e)}")

            if show_error:
                st.error(f"오류가 발생했습니다: {str(e)}")

            return default_return
    return wrapper


class ErrorReporter:
    """에러 리포팅 클래스"""

    def __init__(self):
        self.logger = logging.getLogger("Dashboard.ErrorReporter")
        self.error_counts = {}
        self.error_details = []

    def report_error(
        self,
        error: Exception,
        context: Optional[Dict[str, Any]] = None,
        severity: str = "error"
    ):
        """
        에러 리포트

        Args:
            error (Exception): 발생한 에러
            context (Optional[Dict[str, Any]]): 에러 컨텍스트
            severity (str): 심각도 ("debug", "info", "warning", "error", "critical")
        """
        error_type = type(error).__name__
        error_message = str(error)

        # 에러 카운트 증가
        self.error_counts[error_type] = self.error_counts.get(error_type, 0) + 1

        # 에러 상세 정보 저장
        error_detail = {
            "timestamp": st.session_state.get("current_time") if "current_time" in st.session_state else "Unknown",
            "type": error_type,
            "message": error_message,
            "context": context or {},
            "severity": severity,
            "traceback": traceback.format_exc()
        }
        self.error_details.append(error_detail)

        # 로깅
        log_method = getattr(self.logger, severity)
        log_method(f"📊 Error Report: {error_type} - {error_message}")
        if context:
            log_method(f"🔍 Context: {context}")

    def get_error_summary(self) -> Dict[str, Any]:
        """
        에러 요약 정보 조회

        Returns:
            Dict[str, Any]: 에러 요약
        """
        return {
            "total_errors": len(self.error_details),
            "error_counts": self.error_counts,
            "most_common_error": max(self.error_counts.items(), key=lambda x: x[1])[0] if self.error_counts else None,
            "recent_errors": self.error_details[-5:] if self.error_details else []
        }

    def clear_error_history(self):
        """에러 히스토리 초기화"""
        self.error_counts.clear()
        self.error_details.clear()
        self.logger.info("🗑️ 에러 히스토리가 초기화되었습니다.")


def create_error_display(error_type: str, message: str, details: Optional[str] = None):
    """
    에러 표시 컴포넌트 생성

    Args:
        error_type (str): 에러 타입
        message (str): 에러 메시지
        details (Optional[str]): 상세 정보
    """
    if error_type == "warning":
        st.warning(f"⚠️ {message}")
    elif error_type == "error":
        st.error(f"❌ {message}")
    elif error_type == "info":
        st.info(f"ℹ️ {message}")
    else:
        st.error(f"🚨 {message}")

    if details:
        with st.expander("자세한 정보", expanded=False):
            st.code(details, language="text")


def validate_api_response(response_data: Any, required_fields: list) -> bool:
    """
    API 응답 데이터 검증

    Args:
        response_data (Any): API 응답 데이터
        required_fields (list): 필수 필드 리스트

    Returns:
        bool: 검증 결과
    """
    if not response_data:
        raise ValidationError("API 응답이 비어있습니다.")

    if isinstance(response_data, dict):
        missing_fields = [field for field in required_fields if field not in response_data]
        if missing_fields:
            raise ValidationError(f"필수 필드가 누락되었습니다: {missing_fields}")

    elif isinstance(response_data, list) and required_fields:
        if len(response_data) == 0:
            raise ValidationError("데이터가 비어있습니다.")

        # 리스트의 첫 번째 항목만 검증
        first_item = response_data[0]
        missing_fields = [field for field in required_fields if field not in first_item]
        if missing_fields:
            raise ValidationError(f"데이터 항목에 필수 필드가 누락되었습니다: {missing_fields}")

    return True


def format_user_friendly_error(error: Exception) -> str:
    """
    사용자 친화적 에러 메시지 생성

    Args:
        error (Exception): 발생한 에러

    Returns:
        str: 사용자 친화적 에러 메시지
    """
    error_str = str(error).lower()

    if "connection" in error_str:
        return "서버에 연결할 수 없습니다. 인터넷 연결을 확인하고 다시 시도해주세요."
    elif "timeout" in error_str:
        return "요청 시간이 초과되었습니다. 잠시 후 다시 시도해주세요."
    elif "404" in error_str:
        return "요청한 데이터를 찾을 수 없습니다."
    elif "401" in error_str or "unauthorized" in error_str:
        return "인증이 필요합니다. 다시 로그인해주세요."
    elif "403" in error_str or "forbidden" in error_str:
        return "접근 권한이 없습니다. 관리자에게 문의해주세요."
    elif "500" in error_str:
        return "서버 내부 오류가 발생했습니다. 잠시 후 다시 시도해주세요."
    elif "validation" in error_str:
        return "입력 데이터가 올바르지 않습니다. 다시 확인해주세요."
    elif "network" in error_str:
        return "네트워크 오류가 발생했습니다. 인터넷 연결을 확인해주세요."
    else:
        return f"오류가 발생했습니다: {str(error)}"


# 전역 에러 리포터 인스턴스
error_reporter = ErrorReporter()