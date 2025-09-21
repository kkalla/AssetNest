from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
import os
from datetime import datetime

from .database import DatabaseManager
from .models import PortfolioOverview, HoldingResponse, StockInfo, PerformanceData

app = FastAPI(
    title="AssetNest API",
    description="효율적인 자산관리를 위한 포트폴리오 API",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

db = DatabaseManager()


@app.get("/")
async def root():
    return {"message": "AssetNest API에 오신 것을 환영합니다!", "version": "1.0.0"}


@app.get("/api/v1/portfolio/overview", response_model=PortfolioOverview)
async def get_portfolio_overview(account: Optional[str] = None):
    """포트폴리오 전체 현황을 반환합니다."""
    try:
        data = await db.get_portfolio_overview(account)
        return data
    except Exception as e:
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
    """주식 가격을 새로고침합니다."""
    try:
        # update_stock_info.py의 main() 함수 호출
        from ..update_stock_info import main as update_prices

        await update_prices()
        return {
            "message": "주식 가격이 성공적으로 업데이트되었습니다",
            "timestamp": datetime.now(),
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"가격 업데이트 중 오류가 발생했습니다: {str(e)}"
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
async def get_currency_rates():
    """환율 정보를 반환합니다."""
    try:
        rates = await db.get_currency_rates()
        return rates
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"환율 정보 조회 중 오류가 발생했습니다: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
