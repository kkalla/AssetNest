"""
AssetNest Dashboard 설정 관리 모듈
"""
import os
from typing import Dict, Any


class Settings:
    """애플리케이션 설정 클래스"""

    # API 설정
    API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000/api/v1")
    API_TIMEOUT = int(os.getenv("API_TIMEOUT", "10"))

    # 캐시 설정 (초 단위)
    CACHE_TTL = int(os.getenv("CACHE_TTL", "300"))  # 5분
    CACHE_TTL_LONG = int(os.getenv("CACHE_TTL_LONG", "1800"))  # 30분

    # 페이지 설정
    PAGE_TITLE = "AssetNest 포트폴리오 대쉬보드"
    PAGE_ICON = "💼"
    PAGE_LAYOUT = "wide"

    # 테마 설정
    THEME_COLORS = {
        "primary": "#3B82F6",
        "success": "#10B981",
        "warning": "#F59E0B",
        "error": "#EF4444",
        "background": "#0F172A",
        "surface": "#1E293B",
        "text": "#F8FAFC"
    }

    # 차트 설정
    CHART_HEIGHT = 400
    CHART_TEMPLATE = "plotly_dark"

    # 메트릭 설정
    METRIC_PRECISION = {
        "percentage": 2,
        "currency": 0,
        "ratio": 1
    }

    # 포맷팅 설정
    CURRENCY_SYMBOLS = {
        "KRW": "₩",
        "USD": "$"
    }

    # 에셋 기본 비율 (시뮬레이터용)
    DEFAULT_ASSET_ALLOCATION = {
        "TDF": 5,
        "기타": 5,
        "해외채권": 20,
        "국내채권": 14,
        "해외주식": 15,
        "국내주식": 15,
        "해외리츠": 5,
        "국내리츠": 5,
        "원자재": 8,
        "금": 8
    }

    # 자산 순서
    ASSET_ORDER = [
        "TDF",
        "해외채권",
        "국내채권",
        "해외주식",
        "국내주식",
        "해외리츠",
        "국내리츠",
        "원자재",
        "금",
        "기타"
    ]

    # 기본 현금 비율
    DEFAULT_CASH_RATIO = 10.0

    @classmethod
    def get_api_url(cls, endpoint: str) -> str:
        """API 엔드포인트 URL 생성"""
        return f"{cls.API_BASE_URL}{endpoint}"

    @classmethod
    def format_currency(cls, amount: float, currency: str = "KRW") -> str:
        """통화 포맷팅"""
        symbol = cls.CURRENCY_SYMBOLS.get(currency, "")
        if currency == "KRW":
            return f"{symbol}{amount:,.0f}"
        else:
            return f"{symbol}{amount:,.2f}"

    @classmethod
    def format_percentage(cls, value: float) -> str:
        """퍼센트 포맷팅"""
        return f"{value:.{cls.METRIC_PRECISION['percentage']}f}%"


# 전역 설정 인스턴스
settings = Settings()