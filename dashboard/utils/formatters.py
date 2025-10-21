"""
데이터 포맷팅 유틸리티
"""
from typing import Union
from dashboard.config import settings


def format_currency(amount: Union[int, float], currency: str = "KRW") -> str:
    """
    통화 포맷팅

    Args:
        amount (Union[int, float]): 금액
        currency (str): 통화 코드 (KRW, USD)

    Returns:
        str: 포맷된 통화 문자열
    """
    return settings.format_currency(amount, currency)


def format_percentage(value: Union[int, float], precision: int = 2) -> str:
    """
    퍼센트 포맷팅

    Args:
        value (Union[int, float]): 퍼센트 값
        precision (int): 소수점 자릿수

    Returns:
        str: 포맷된 퍼센트 문자열
    """
    return f"{value:.{precision}f}%"


def format_number(value: Union[int, float], precision: int = 0) -> str:
    """
    숫자 포맷팅 (천 단위 구분 기호)

    Args:
        value (Union[int, float]): 숫자
        precision (int): 소수점 자릿수

    Returns:
        str: 포맷된 숫자 문자열
    """
    return f"{value:,.{precision}f}"


def format_large_number(value: Union[int, float]) -> str:
    """
    큰 숫자를 읽기 쉽게 포맷팅 (만, 억, 조 단위)

    Args:
        value (Union[int, float]): 큰 숫자

    Returns:
        str: 포맷된 숫자 문자열
    """
    if value >= 1_0000_0000_0000:  # 조
        return f"{value/1_0000_0000_0000:.1f}조"
    elif value >= 1_0000_0000:  # 억
        return f"{value/1_0000_0000:.1f}억"
    elif value >= 1_0000:  # 만
        return f"{value/1_0000:.1f}만"
    else:
        return f"{value:,.0f}"


def format_date(date_obj, format_type: str = "iso") -> str:
    """
    날짜 포맷팅

    Args:
        date_obj: 날짜 객체
        format_type (str): 포맷 타입 (iso, korean, short)

    Returns:
        str: 포맷된 날짜 문자열
    """
    if format_type == "iso":
        return date_obj.strftime("%Y-%m-%d")
    elif format_type == "korean":
        return date_obj.strftime("%Y년 %m월 %d일")
    elif format_type == "short":
        return date_obj.strftime("%m/%d")
    else:
        return str(date_obj)


def format_time_duration(minutes: int) -> str:
    """
    시간 간격 포맷팅

    Args:
        minutes (int): 분 단위 시간

    Returns:
        str: 포맷된 시간 간격 문자열
    """
    if minutes < 60:
        return f"{minutes}분"
    elif minutes < 1440:  # 24시간
        hours = minutes // 60
        remaining_minutes = minutes % 60
        return f"{hours}시간 {remaining_minutes}분"
    else:
        days = minutes // 1440
        remaining_hours = (minutes % 1440) // 60
        return f"{days}일 {remaining_hours}시간"


def format_file_size(size_bytes: int) -> str:
    """
    파일 크기 포맷팅

    Args:
        size_bytes (int): 바이트 단위 파일 크기

    Returns:
        str: 포맷된 파일 크기 문자열
    """
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes/1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes/(1024*1024):.1f} MB"
    else:
        return f"{size_bytes/(1024*1024*1024):.1f} GB"