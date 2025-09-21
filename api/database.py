import os
from supabase import create_client, Client
from typing import List, Optional, Dict, Any
from datetime import datetime
from .models import (
    PortfolioOverview,
    HoldingResponse,
    StockInfo,
    PerformanceData,
    CurrencyRate,
    MarketSummary,
)


class DatabaseManager:
    def __init__(self):
        self.supabase_url = os.environ.get("SUPABASE_URL")
        self.supabase_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

        if not self.supabase_url or not self.supabase_key:
            raise ValueError(
                "SUPABASE_URL과 SUPABASE_SERVICE_ROLE_KEY 환경변수가 필요합니다"
            )

        self.supabase: Client = create_client(self.supabase_url, self.supabase_key)

    async def get_portfolio_overview(
        self, account: Optional[str] = None
    ) -> PortfolioOverview:
        """포트폴리오 전체 현황 조회"""
        try:
            # overall_info 뷰에서 데이터 조회
            query = self.supabase.table("overall_info").select("*")

            if account:
                query = query.eq("account", account)

            response = query.execute()
            data = response.data

            if not data:
                # 기본값 반환
                return PortfolioOverview(
                    total_value_krw=0.0,
                    total_value_usd=0.0,
                    total_pnl_krw=0.0,
                    total_pnl_usd=0.0,
                    total_return_rate=0.0,
                    accounts=[],
                    last_updated=datetime.now(),
                )

            # 계산
            total_value_krw = sum(float(item.get("market_value", 0)) for item in data)
            total_value_usd = sum(
                float(item.get("market_value_usd", 0)) for item in data
            )
            total_pnl_krw = sum(float(item.get("unrealized_G/L", 0)) for item in data)
            total_pnl_usd = sum(
                float(item.get("unrealized_G/L_usd", 0)) for item in data
            )

            # 수익률 계산
            total_principal_krw = sum(float(item.get("principal", 0)) for item in data)
            total_return_rate = (
                (total_pnl_krw / total_principal_krw * 100)
                if total_principal_krw > 0
                else 0.0
            )

            # 계좌 목록
            accounts = list(set(item["account"] for item in data))

            return PortfolioOverview(
                total_value_krw=total_value_krw,
                total_value_usd=total_value_usd,
                total_pnl_krw=total_pnl_krw,
                total_pnl_usd=total_pnl_usd,
                total_return_rate=total_return_rate,
                accounts=accounts,
                last_updated=datetime.now(),
            )

        except Exception as e:
            print(f"포트폴리오 개요 조회 오류: {e}")
            raise

    async def get_holdings(
        self, account: Optional[str] = None, market: Optional[str] = None
    ) -> List[HoldingResponse]:
        """보유 종목 정보 조회"""
        try:
            query = self.supabase.table("overall_info").select("*")

            if account:
                query = query.eq("account", account)

            if market:
                query = query.eq("market", market)

            response = query.execute()
            data = response.data

            holdings = []
            for item in data:
                holding = HoldingResponse(
                    id=item.get("id"),
                    account=item.get("account"),
                    company=item.get("company"),
                    market=item.get("market"),
                    area=item.get("area"),
                    amount=item.get("amount", 0),
                    avg_price_krw=float(item.get("avg_price_krw", 0)),
                    current_price_krw=float(item.get("latest_close_krw", 0)),
                    principal=float(item.get("principal", 0)),
                    market_value=float(item.get("market_value", 0)),
                    unrealized_pnl=float(item.get("unrealized_G/L", 0)),
                    return_rate=float(item.get("rate_of_return", 0)),
                    avg_price_usd=(
                        float(item.get("avg_price_usd", 0))
                        if item.get("avg_price_usd")
                        else None
                    ),
                    current_price_usd=(
                        float(item.get("latest_close_usd", 0))
                        if item.get("latest_close_usd")
                        else None
                    ),
                    principal_usd=(
                        float(item.get("principal_usd", 0))
                        if item.get("principal_usd")
                        else None
                    ),
                    market_value_usd=(
                        float(item.get("market_value_usd", 0))
                        if item.get("market_value_usd")
                        else None
                    ),
                    unrealized_pnl_usd=(
                        float(item.get("unrealized_G/L_usd", 0))
                        if item.get("unrealized_G/L_usd")
                        else None
                    ),
                    return_rate_usd=(
                        float(item.get("rate_of_return_usd", 0))
                        if item.get("rate_of_return_usd")
                        else None
                    ),
                    first_buy_at=item.get("first_buy_at"),
                    last_buy_at=item.get("last_buy_at"),
                    last_sell_at=item.get("last_sell_at"),
                    total_realized_pnl=(
                        float(item.get("total_realized_G/L", 0))
                        if item.get("total_realized_G/L")
                        else None
                    ),
                )
                holdings.append(holding)

            return holdings

        except Exception as e:
            print(f"보유 종목 조회 오류: {e}")
            raise

    async def get_all_stocks(self) -> List[StockInfo]:
        """모든 주식 정보 조회"""
        try:
            response = self.supabase.table("stock_info").select("*").execute()
            data = response.data

            stocks = []
            for item in data:
                stock = StockInfo(
                    id=item.get("id"),
                    company=item.get("company"),
                    symbol=item.get("symbol"),
                    exchange=item.get("exchange"),
                    sector=item.get("sector"),
                    industry=item.get("industry"),
                    area=item.get("area"),
                    latest_close=(
                        float(item.get("latest_close", 0))
                        if item.get("latest_close")
                        else None
                    ),
                    marketcap=(
                        float(item.get("marketcap", 0))
                        if item.get("marketcap")
                        else None
                    ),
                    updated_at=item.get("updated_at"),
                )
                stocks.append(stock)

            return stocks

        except Exception as e:
            print(f"주식 정보 조회 오류: {e}")
            raise

    async def get_performance_data(self, account: str) -> Optional[PerformanceData]:
        """계좌별 성과 분석 데이터"""
        try:
            response = (
                self.supabase.table("overall_info")
                .select("*")
                .eq("account", account)
                .execute()
            )
            data = response.data

            if not data:
                return None

            total_investment = sum(float(item.get("principal", 0)) for item in data)
            total_value = sum(float(item.get("market_value", 0)) for item in data)
            total_return = total_value - total_investment
            return_rate = (
                (total_return / total_investment * 100) if total_investment > 0 else 0.0
            )

            # 섹터별 분배 (stock_info와 조인 필요)
            sector_allocation = {}
            region_allocation = {"국내": 0, "해외": 0}

            for item in data:
                market = item.get("market", "알수없음")
                value = float(item.get("market_value", 0))

                if market in region_allocation:
                    region_allocation[market] += value

                # 섹터 정보는 별도 조회 필요 (stock_info 테이블)

            return PerformanceData(
                account=account,
                total_investment=total_investment,
                total_value=total_value,
                total_return=total_return,
                return_rate=return_rate,
                sector_allocation=sector_allocation,
                region_allocation=region_allocation,
            )

        except Exception as e:
            print(f"성과 데이터 조회 오류: {e}")
            raise

    async def get_currency_rates(self) -> List[CurrencyRate]:
        """환율 정보 조회"""
        try:
            response = self.supabase.table("currency").select("*").execute()
            data = response.data

            rates = []
            for item in data:
                rate = CurrencyRate(
                    currency=item.get("currency"),
                    exchange_rate=float(item.get("exchange_rate", 0)),
                    updated_at=item.get("updated_at", datetime.now()),
                )
                rates.append(rate)

            return rates

        except Exception as e:
            print(f"환율 정보 조회 오류: {e}")
            raise
