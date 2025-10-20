import asyncio
import pytest
import sys
import os
from pathlib import Path

# 프로젝트 루트 경로 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "api"))


@pytest.fixture(scope="session")
def event_loop():
    """비동기 테스트를 위한 이벤트 루프 생성"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def test_client():
    """FastAPI 테스트 클라이언트 생성"""
    from fastapi.testclient import TestClient
    from api.main import app

    return TestClient(app)


@pytest.fixture
def mock_db_manager():
    """Database Manager 모킹"""
    from unittest.mock import AsyncMock, MagicMock
    from api.database import DatabaseManager

    # 실제 DB 연결을 피하기 위해 모킹
    mock_db = AsyncMock(spec=DatabaseManager)
    return mock_db


@pytest.fixture
def sample_portfolio_overview():
    """샘플 포트폴리오 개요 데이터"""
    from datetime import datetime

    return {
        "total_value_krw": 100000000,
        "total_value_usd": 75000,
        "total_pnl_krw": 5000000,
        "total_pnl_usd": 3750,
        "total_return_rate": 0.0526,
        "accounts": ["증권사A", "증권사B"],
        "cash_asset_value": 20000000,
        "investment_asset_value": 80000000,
        "cash_asset_ratio": 20.0,
        "investment_asset_ratio": 80.0,
        "investment_allocations": [],
        "last_updated": datetime(2025, 1, 20, 10, 0, 0),
    }


@pytest.fixture
def sample_holdings():
    """샘플 보유 종목 데이터"""
    return [
        {
            "account": "증권사A",
            "company": "삼성전자",
            "market": "KOSPI",
            "amount": 100,
            "avg_price_krw": 70000,
            "current_price_krw": 75000,
            "principal": 7000000,
            "market_value": 7500000,
            "unrealized_pnl": 500000,
            "return_rate": 0.0714,
            "currency": "KRW",
            "sector": "전자",
            "asset_type": "equity",
            "region_type": "domestic",
        },
        {
            "account": "증권사B",
            "company": "Apple Inc.",
            "market": "NASDAQ",
            "amount": 50,
            "avg_price_krw": 150000,
            "current_price_krw": 160000,
            "principal": 7500000,
            "market_value": 8000000,
            "unrealized_pnl": 500000,
            "return_rate": 0.0667,
            "currency": "USD",
            "sector": "IT",
            "asset_type": "equity",
            "region_type": "global",
        },
    ]


@pytest.fixture
def sample_stock_info():
    """샘플 주식 정보 데이터"""
    return [
        {
            "name": "삼성전자",
            "symbol": "005930",
            "exchange": "KOSPI",
            "sector": "전자",
            "industry": "반도체",
            "asset_type": "equity",
            "region_type": "domestic",
            "latest_close": 75000,
            "marketcap": 4500000,
            "updated_at": "2025-01-20T10:00:00",
        },
        {
            "name": "Apple Inc.",
            "symbol": "AAPL",
            "exchange": "NASDAQ",
            "sector": "IT",
            "industry": "컴퓨터",
            "asset_type": "equity",
            "region_type": "global",
            "latest_close": 175.50,
            "marketcap": 2700000,
            "updated_at": "2025-01-20T10:00:00",
        },
    ]


@pytest.fixture
def sample_currency_rates():
    """샘플 환율 데이터"""
    return [
        {"currency": "USD", "rate": 1385.0, "timestamp": "2025-01-20T10:00:00"},
        {"currency": "EUR", "rate": 1500.0, "timestamp": "2025-01-20T10:00:00"},
    ]


@pytest.fixture
def sample_performance_data():
    """샘플 성과 분석 데이터"""
    return {
        "account": "증권사A",
        "total_investment": 7000000,
        "total_value": 7500000,
        "total_return": 500000,
        "return_rate": 0.0714,
        "sector_allocation": {"전자": 0.6, "금융": 0.3, "제조": 0.1},
        "region_allocation": {"domestic": 0.7, "global": 0.3},
        "daily_returns": [0.01, -0.005, 0.02, 0.015, -0.01],
        "cumulative_returns": [1.01, 1.005, 1.025, 1.04, 1.03],
        "volatility": 0.15,
        "sharpe_ratio": 1.2,
        "max_drawdown": -0.08,
        "updated_at": "2025-01-20T10:00:00",
    }


@pytest.fixture
def sample_asset_allocation():
    """샘플 자산 분배 데이터"""
    return {
        "total_portfolio_value": 100000000,
        "allocations": [
            {
                "asset_category": "주식",
                "holdings_count": 20,
                "total_market_value": 70000000,
                "allocation_percentage": 0.7,
            },
            {
                "asset_category": "채권",
                "holdings_count": 5,
                "total_market_value": 20000000,
                "allocation_percentage": 0.2,
            },
            {
                "asset_category": "현금",
                "holdings_count": 3,
                "total_market_value": 10000000,
                "allocation_percentage": 0.1,
            },
        ],
        "by_asset_type": {"equity": 0.7, "bond": 0.2, "cash": 0.1},
        "by_region": {"domestic": 0.6, "global": 0.4},
        "by_currency": {"krw": 0.7, "usd": 0.3},
        "total_assets": 100000000,
        "updated_at": "2025-01-20T10:00:00",
    }
