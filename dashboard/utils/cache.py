"""
캐시 유틸리티
"""
import streamlit as st
import functools
from typing import Callable, Any
from datetime import datetime, timedelta


def cache_with_ttl(ttl_seconds: int = 300):
    """
    지정된 TTL(Time To Live)을 가진 캐시 데코레이터

    Args:
        ttl_seconds (int): 캐시 유효시간 (초)
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # 캐시 키 생성
            cache_key = f"{func.__name__}_{str(args)}_{str(sorted(kwargs.items()))}"

            # 캐시된 데이터와 타임스탬프 확인
            cached_data = st.session_state.get(cache_key)
            if cached_data:
                data, timestamp = cached_data
                if datetime.now() - timestamp < timedelta(seconds=ttl_seconds):
                    return data

            # 데이터 실행 및 캐싱
            result = func(*args, **kwargs)
            st.session_state[cache_key] = (result, datetime.now())

            return result

        return wrapper
    return decorator


def clear_cache_by_pattern(pattern: str):
    """
    패턴에 맞는 캐시 항목들 삭제

    Args:
        pattern (str): 삭제할 캐시 키 패턴
    """
    keys_to_delete = []
    for key in st.session_state.keys():
        if pattern in key:
            keys_to_delete.append(key)

    for key in keys_to_delete:
        del st.session_state[key]


def get_cache_info() -> dict:
    """
    캐시 정보 조회

    Returns:
        dict: 캐시 통계 정보
    """
    cache_keys = [key for key in st.session_state.keys() if not key.startswith('_')]
    total_cache_items = len(cache_keys)

    return {
        "total_items": total_cache_items,
        "cache_keys": cache_keys,
        "session_state_size": len(st.session_state)
    }


def expire_old_cache(max_age_hours: int = 24):
    """
    지정된 시간보다 오래된 캐시 항목들 삭제

    Args:
        max_age_hours (int): 최대 보관 시간 (시간)
    """
    max_age = timedelta(hours=max_age_hours)
    current_time = datetime.now()

    keys_to_delete = []
    for key, value in st.session_state.items():
        if isinstance(value, tuple) and len(value) == 2:
            data, timestamp = value
            if isinstance(timestamp, datetime):
                if current_time - timestamp > max_age:
                    keys_to_delete.append(key)

    for key in keys_to_delete:
        del st.session_state[key]