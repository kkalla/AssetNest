import os
import sys
import time
from contextlib import asynccontextmanager
from datetime import datetime
from typing import List, Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware

from .database import DatabaseManager
from .models import (
    AssetAllocationResponse,
    HoldingResponse,
    PerformanceData,
    PortfolioOverview,
    StockInfo,
    UnmatchedProductsResponse,
)

# 프로젝트 루트를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from logger import get_api_logger

api_logger = get_api_logger("API")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 시작 시 실행
    api_logger.info("🚀 AssetNest API 서버가 시작되었습니다")
    api_logger.info("📊 API 문서: http://localhost:8000/docs")
    yield
    # 종료 시 실행
    api_logger.info("🛑 AssetNest API 서버가 종료됩니다")


app = FastAPI(
    title="AssetNest API",
    description="효율적인 자산관리를 위한 포트폴리오 API",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 로깅 미들웨어
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """API 요청/응답 로깅 미들웨어"""
    start_time = time.time()

    # 요청 로깅
    api_logger.info(
        f"📨 {request.method} {request.url.path} - "
        f"클라이언트: {request.client.host if request.client else 'unknown'}"
    )

    # 쿼리 파라미터 로깅 (있는 경우)
    if request.query_params:
        api_logger.debug(f"📊 쿼리 파라미터: {dict(request.query_params)}")

    try:
        response = await call_next(request)
        process_time = time.time() - start_time

        # 응답 로깅
        status_emoji = "✅" if response.status_code < 400 else "❌"
        api_logger.info(
            f"{status_emoji} {request.method} {request.url.path} - "
            f"상태: {response.status_code} - 처리시간: {process_time:.3f}초"
        )

        return response

    except Exception as e:
        process_time = time.time() - start_time
        api_logger.error(
            f"💥 {request.method} {request.url.path} - "
            f"오류: {str(e)} - 처리시간: {process_time:.3f}초"
        )
        raise


db = DatabaseManager()


@app.get("/")
async def root():
    return {"message": "AssetNest API에 오신 것을 환영합니다!", "version": "1.0.0"}


@app.get("/api/v1/portfolio/overview", response_model=PortfolioOverview)
async def get_portfolio_overview(account: Optional[str] = None):
    """포트폴리오 전체 현황을 반환합니다."""
    try:
        api_logger.info(f"📊 포트폴리오 개요 조회 요청 - 계정: {account or '전체'}")
        data = await db.get_portfolio_overview(account)
        api_logger.info(
            f"✅ 포트폴리오 개요 조회 완료 - 총 자산: ₩{data.total_value_krw:,.0f}"
        )
        return data
    except Exception as e:
        api_logger.error(f"❌ 포트폴리오 개요 조회 실패: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"데이터 조회 중 오류가 발생했습니다: {str(e)}"
        )


@app.get("/api/v1/holdings/", response_model=List[HoldingResponse])
async def get_all_holdings(account: Optional[str] = None, market: Optional[str] = None):
    """모든 보유 종목 정보를 반환합니다."""
    try:
        holdings = await db.get_holdings(account, market)
        return holdings
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"보유 종목 조회 중 오류가 발생했습니다: {str(e)}"
        )


@app.get("/api/v1/holdings/{account}", response_model=List[HoldingResponse])
async def get_holdings_by_account(account: str):
    """특정 계좌의 보유 종목을 반환합니다."""
    try:
        holdings = await db.get_holdings(account=account)
        if not holdings:
            raise HTTPException(
                status_code=404,
                detail=f"계좌 '{account}'의 보유 종목을 찾을 수 없습니다",
            )
        return holdings
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"계좌별 보유 종목 조회 중 오류가 발생했습니다: {str(e)}",
        )


@app.get("/api/v1/stocks/", response_model=List[StockInfo])
async def get_all_stocks():
    """모든 주식 정보를 반환합니다."""
    try:
        stocks = await db.get_all_stocks()
        return stocks
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"주식 정보 조회 중 오류가 발생했습니다: {str(e)}"
        )


@app.post("/api/v1/stocks/refresh-prices")
async def refresh_stock_prices():
    """symbol_table의 주식 가격을 새로고침합니다."""
    try:
        api_logger.info("🔄 symbol_table 가격 업데이트 요청")
        result = await db.update_symbol_table_prices()
        api_logger.info(
            f"✅ 가격 업데이트 완료 - 성공: {result['success_count']}, "
            f"실패: {result['fail_count']}, 스킵: {result['skip_count']}, 전체: {result['total_count']}"
        )
        return {
            "message": "주식 가격이 성공적으로 업데이트되었습니다",
            "success_count": result["success_count"],
            "fail_count": result["fail_count"],
            "skip_count": result["skip_count"],
            "total_count": result["total_count"],
            "timestamp": datetime.now(),
        }
    except Exception as e:
        api_logger.error(f"❌ 가격 업데이트 실패: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"가격 업데이트 중 오류가 발생했습니다: {str(e)}"
        )


@app.post("/api/v1/stocks/update")
async def update_stocks():
    """symbol_table의 가격 정보와 sector/industry 정보를 한꺼번에 업데이트합니다."""
    try:
        api_logger.info("🔄 symbol_table 전체 업데이트 요청 (가격 + sector/industry)")

        # 1. 가격 정보 업데이트
        api_logger.info("📊 1단계: 가격 정보 업데이트 시작")
        price_result = await db.update_symbol_table_prices()
        api_logger.info(
            f"✅ 가격 업데이트 완료 - 성공: {price_result['success_count']}, "
            f"실패: {price_result['fail_count']}, 스킵: {price_result['skip_count']}"
        )

        # 2. Sector/Industry 정보 업데이트
        api_logger.info("🏢 2단계: sector/industry 정보 업데이트 시작")
        sector_result = await db.update_symbol_sector_info()
        api_logger.info(
            f"✅ sector/industry 업데이트 완료 - 성공: {sector_result['success_count']}, "
            f"실패: {sector_result['fail_count']}"
        )

        return {
            "message": "주식 정보가 성공적으로 업데이트되었습니다",
            "price_update": {
                "success_count": price_result["success_count"],
                "fail_count": price_result["fail_count"],
                "skip_count": price_result["skip_count"],
                "total_count": price_result["total_count"],
                "failed_stocks": price_result.get("failed_stocks", []),
            },
            "sector_update": {
                "success_count": sector_result["success_count"],
                "fail_count": sector_result["fail_count"],
                "total_count": sector_result["total_count"],
                "failed_stocks": sector_result.get("failed_stocks", []),
            },
            "timestamp": datetime.now(),
        }
    except Exception as e:
        api_logger.error(f"❌ 주식 정보 업데이트 실패: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"주식 정보 업데이트 중 오류가 발생했습니다: {str(e)}",
        )


@app.get("/api/v1/analytics/performance/{account}", response_model=PerformanceData)
async def get_performance_analytics(account: str):
    """계좌별 성과 분석 데이터를 반환합니다."""
    try:
        performance = await db.get_performance_data(account)
        if not performance:
            raise HTTPException(
                status_code=404,
                detail=f"계좌 '{account}'의 성과 데이터를 찾을 수 없습니다",
            )
        return performance
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"성과 분석 데이터 조회 중 오류가 발생했습니다: {str(e)}",
        )


@app.get("/api/v1/currency/rates")
async def get_currency_rates(auto_update: bool = True):
    """환율 정보를 반환합니다."""
    try:
        api_logger.info(f"💱 환율 정보 조회 요청 - 자동 업데이트: {auto_update}")
        rates = await db.get_currency_rates(auto_update=auto_update)
        api_logger.info(f"✅ 환율 정보 조회 완료 - {len(rates)}개 통화")
        return rates
    except Exception as e:
        api_logger.error(f"❌ 환율 정보 조회 실패: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"환율 정보 조회 중 오류가 발생했습니다: {str(e)}"
        )


@app.post("/api/v1/currency/refresh")
async def refresh_currency_rates(currencies: Optional[List[str]] = None):
    """환율 정보를 수동으로 새로고침합니다."""
    try:
        api_logger.info(f"🔄 환율 수동 새로고침 요청 - 통화: {currencies or '전체'}")

        if currencies:
            # 특정 통화만 업데이트
            updated_rates = await db.update_currency_rates(currencies)
        else:
            # 모든 환율 새로고침 (기존 환율 조회 후 업데이트)
            current_rates = await db.get_currency_rates(auto_update=False)
            all_currencies = [rate.currency for rate in current_rates]
            updated_rates = await db.update_currency_rates(all_currencies)

        api_logger.info(f"✅ 환율 새로고침 완료 - {len(updated_rates)}개 업데이트")
        return {
            "message": f"환율 정보가 성공적으로 업데이트되었습니다",
            "updated_count": len(updated_rates),
            "updated_currencies": [rate.currency for rate in updated_rates],
            "timestamp": datetime.now(),
        }
    except Exception as e:
        api_logger.error(f"❌ 환율 새로고침 실패: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"환율 새로고침 중 오류가 발생했습니다: {str(e)}"
        )


@app.get("/api/v1/portfolio/allocation", response_model=AssetAllocationResponse)
async def get_asset_allocation(
    account: Optional[str] = None, auto_add_unmatched: bool = True
):
    """자산 분배 현황을 반환합니다.

    Args:
        account: 특정 계좌만 조회 (None이면 전체)
        auto_add_unmatched: symbol_table에 없는 상품을 자동으로 추가할지 여부 (기본값: True)
    """
    try:
        allocation = await db.get_asset_allocation(account, auto_add_unmatched)
        return allocation
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"자산 분배 조회 중 오류가 발생했습니다: {str(e)}"
        )


@app.get(
    "/api/v1/validation/unmatched-products", response_model=UnmatchedProductsResponse
)
async def get_unmatched_products(account: Optional[str] = None):
    """by_accounts 테이블에는 있지만 symbol_table에는 없는 상품들을 반환합니다."""
    try:
        unmatched = await db.get_unmatched_products(account)
        return unmatched
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"매칭되지 않는 상품 조회 중 오류가 발생했습니다: {str(e)}",
        )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
