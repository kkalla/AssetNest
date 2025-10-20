"""Database facade implementation for AssetNest API.

This module provides a backward-compatible facade that orchestrates
the new modular services while maintaining the existing API interface.
"""

import logging
from datetime import date, datetime
from typing import List, Optional, Dict, Any

from .database_modules.repositories import (
    BaseRepository,
    PortfolioRepository,
    HoldingsRepository,
    CurrencyRepository,
    CashRepository,
)
from .database_modules.connection import DatabaseConnection
from .database_modules.models import DatabaseModels
from .services import (
    PortfolioService,
    HoldingsService,
    CashService,
    CurrencyService,
    SyncService,
)
from .adapters import MarketDataAdapter, CurrencyAdapter
from .models import (
    AssetAllocation,
    AssetAllocationResponse,
    CashBalance,
    CashManagementSummary,
    CashUpdateRequest,
    CurrencyRate,
    HoldingDetail,
    HoldingResponse,
    MarketSummary,
    PerformanceData,
    PortfolioOverview,
    StockInfo,
    TimeDeposit,
    UnmatchedProduct,
    UnmatchedProductsResponse,
    BSTimeseries,
)

logger = logging.getLogger(__name__)


class DatabaseManager:
    """
    Legacy DatabaseManager refactored as a facade.

    This class maintains backward compatibility while orchestrating
    the new modular service architecture.
    """

    def __init__(self):
        """Initialize the database manager and all services."""
        logger.info("🚀 DatabaseManager 파사드 초기화 시작")

        # Database connection
        self.db_connection = DatabaseConnection()

        # Repositories
        self.base_repository = BaseRepository(self.db_connection)
        self.portfolio_repository = PortfolioRepository(self.db_connection)
        self.holdings_repository = HoldingsRepository(self.db_connection)
        self.currency_repository = CurrencyRepository(self.db_connection)
        self.cash_repository = CashRepository(self.db_connection)

        # Adapters
        self.market_data_adapter = MarketDataAdapter()
        self.currency_adapter = CurrencyAdapter()

        # Services
        self.sync_service = SyncService(self.cash_repository)
        self.cash_service = CashService(self.cash_repository, self.sync_service)
        self.currency_service = CurrencyService(
            self.currency_repository, self.currency_adapter
        )
        self.holdings_service = HoldingsService(
            self.holdings_repository, self.market_data_adapter
        )
        self.portfolio_service = PortfolioService(
            self.portfolio_repository, self.sync_service
        )

        logger.info("✅ DatabaseManager 파사드 초기화 완료")

    # Portfolio methods
    async def get_portfolio_overview(self) -> PortfolioOverview:
        """포트폴리오 전체 현황 조회"""
        try:
            overview = await self.portfolio_service.get_portfolio_overview()

            return PortfolioOverview(
                total_assets=overview.total_assets,
                total_valuation_amount=overview.total_valuation_amount,
                total_profit_loss=overview.total_profit_loss,
                total_profit_loss_rate=overview.total_profit_loss_rate,
                krw_assets=overview.krw_assets,
                usd_assets=overview.usd_assets,
                total_equity=overview.total_equity,
                total_bond=overview.total_bond,
                total_reit=overview.total_reit,
                total_commodity=overview.total_commodity,
                total_cash=overview.total_cash,
                updated_at=overview.updated_at,
            )
        except Exception as e:
            logger.error(f"포트폴리오 전체 현황 조회 오류: {e}")
            raise

    async def get_portfolio_summary(
        self, account: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """계좌별 포트폴리오 요약 정보 조회"""
        try:
            summaries = await self.portfolio_service.get_portfolio_summary(account)

            return [
                {
                    "account": summary.account,
                    "valuation_amount": summary.valuation_amount,
                    "profit_loss": summary.profit_loss,
                    "profit_loss_rate": summary.profit_loss_rate,
                    "updated_at": summary.updated_at,
                }
                for summary in summaries
            ]
        except Exception as e:
            logger.error(f"포트폴리오 요약 정보 조회 오류: {e}")
            raise

    async def get_asset_allocation(self) -> AssetAllocationResponse:
        """자산 배분 현황 조회"""
        try:
            allocation = await self.portfolio_service.get_asset_allocation()

            return AssetAllocationResponse(
                by_asset_type=allocation.by_asset_type,
                by_region=allocation.by_region,
                by_currency=allocation.by_currency,
                total_assets=allocation.total_assets,
                updated_at=allocation.updated_at,
            )
        except Exception as e:
            logger.error(f"자산 배분 현황 조회 오류: {e}")
            raise

    # Holdings methods
    async def get_holdings(self, account: Optional[str] = None) -> HoldingResponse:
        """보유 종목 정보 조회"""
        try:
            holdings = await self.holdings_service.get_holdings(account)

            holding_details = []
            for holding in holdings:
                detail = HoldingDetail(
                    account=holding.account,
                    name=holding.name,
                    symbol=holding.symbol,
                    quantity=holding.quantity,
                    average_price=holding.average_price,
                    current_price=holding.current_price,
                    valuation_amount=holding.valuation_amount,
                    profit_loss=holding.profit_loss,
                    profit_loss_rate=holding.profit_loss_rate,
                    currency=holding.currency,
                    sector=holding.sector,
                    asset_type=holding.asset_type,
                    region_type=holding.region_type,
                    updated_at=holding.updated_at,
                )
                holding_details.append(detail)

            return HoldingResponse(holdings=holding_details)
        except Exception as e:
            logger.error(f"보유 종목 정보 조회 오류: {e}")
            raise

    async def update_holding(
        self,
        account: str,
        company: str,
        quantity: Optional[int] = None,
        average_price: Optional[float] = None,
        current_price: Optional[float] = None,
    ) -> bool:
        """보유 종목 정보 업데이트"""
        try:
            return await self.holdings_service.update_holding(
                account, company, quantity, average_price, current_price
            )
        except Exception as e:
            logger.error(f"보유 종목 정보 업데이트 오류: {e}")
            raise

    async def get_stock_info(self, symbol: str) -> Optional[StockInfo]:
        """특정 주식 정보 조회"""
        try:
            stock_info = await self.holdings_service.get_stock_info(symbol)

            if stock_info:
                return StockInfo(
                    symbol=stock_info.symbol,
                    name=stock_info.name,
                    sector=stock_info.sector,
                    industry=stock_info.industry,
                    asset_type=stock_info.asset_type,
                    region_type=stock_info.region_type,
                    latest_close=stock_info.latest_close,
                    marketcap=stock_info.marketcap,
                    updated_at=stock_info.updated_at,
                )
            return None
        except Exception as e:
            logger.error(f"주식 정보 조회 오류: {e}")
            raise

    async def update_symbol_prices(
        self, symbols: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """symbol_table의 가격 정보 업데이트"""
        try:
            return await self.holdings_service.update_symbol_prices(symbols)
        except Exception as e:
            logger.error(f"symbol 가격 업데이트 오류: {e}")
            raise

    async def get_unmatched_products(self) -> UnmatchedProductsResponse:
        """symbol_table에 없는 종목 조회"""
        try:
            unmatched = await self.portfolio_service.get_unmatched_products()

            unmatched_products = []
            for product in unmatched:
                unmatched_product = UnmatchedProduct(
                    company=product.company,
                    valuation_amount=product.valuation_amount,
                    profit_loss=product.profit_loss,
                    profit_loss_rate=product.profit_loss_rate,
                    account=product.account,
                    updated_at=product.updated_at,
                )
                unmatched_products.append(unmatched_product)

            return UnmatchedProductsResponse(unmatched_products=unmatched_products)
        except Exception as e:
            logger.error(f"미매칭 종목 조회 오류: {e}")
            raise

    # Cash management methods
    async def get_cash_balances(
        self, account: Optional[str] = None
    ) -> List[CashBalance]:
        """증권사별 예수금 정보 조회"""
        try:
            balances = await self.cash_service.get_cash_balances(account)

            cash_balances = []
            for balance in balances:
                cash_balance = CashBalance(
                    account=balance.account,
                    krw=balance.krw,
                    usd=balance.usd,
                    updated_at=balance.updated_at,
                )
                cash_balances.append(cash_balance)

            return cash_balances
        except Exception as e:
            logger.error(f"현금 잔액 조회 오류: {e}")
            raise

    async def update_cash_balance(
        self,
        account: str,
        krw: Optional[float] = None,
        usd: Optional[float] = None,
    ) -> bool:
        """증권사별 예수금 업데이트"""
        try:
            return await self.cash_service.update_cash_balance(account, krw, usd)
        except Exception as e:
            logger.error(f"현금 잔액 업데이트 오류: {e}")
            raise

    async def get_time_deposits(
        self, account: Optional[str] = None
    ) -> List[TimeDeposit]:
        """예적금 정보 조회"""
        try:
            deposits = await self.cash_service.get_time_deposits(account)

            time_deposits = []
            for deposit in deposits:
                time_deposit = TimeDeposit(
                    account=deposit.account,
                    invest_prod_name=deposit.invest_prod_name,
                    market_value=deposit.market_value,
                    invested_principal=deposit.invested_principal,
                    maturity_date=deposit.maturity_date,
                    interest_rate=deposit.interest_rate,
                    updated_at=deposit.updated_at,
                )
                time_deposits.append(time_deposit)

            return time_deposits
        except Exception as e:
            logger.error(f"예적금 정보 조회 오류: {e}")
            raise

    async def create_time_deposit(
        self,
        account: str,
        invest_prod_name: str,
        market_value: int,
        invested_principal: int,
        maturity_date: Optional[datetime] = None,
        interest_rate: Optional[float] = None,
    ) -> bool:
        """예적금 생성"""
        try:
            return await self.cash_service.create_time_deposit(
                account,
                invest_prod_name,
                market_value,
                invested_principal,
                maturity_date,
                interest_rate,
            )
        except Exception as e:
            logger.error(f"예적금 생성 오류: {e}")
            raise

    async def update_time_deposit(
        self,
        account: str,
        invest_prod_name: str,
        market_value: Optional[int] = None,
        invested_principal: Optional[int] = None,
        maturity_date: Optional[datetime] = None,
        interest_rate: Optional[float] = None,
    ) -> bool:
        """예적금 수정"""
        try:
            return await self.cash_service.update_time_deposit(
                account,
                invest_prod_name,
                market_value,
                invested_principal,
                maturity_date,
                interest_rate,
            )
        except Exception as e:
            logger.error(f"예적금 수정 오류: {e}")
            raise

    async def delete_time_deposit(self, account: str, invest_prod_name: str) -> bool:
        """예적금 삭제"""
        try:
            return await self.cash_service.delete_time_deposit(
                account, invest_prod_name
            )
        except Exception as e:
            logger.error(f"예적금 삭제 오류: {e}")
            raise

    async def get_cash_management_summary(self) -> CashManagementSummary:
        """현금 관리 요약 정보 조회"""
        try:
            summary = await self.cash_service.get_cash_management_summary()

            # 변환 로직 추가
            cash_balances = []
            for balance in summary.cash_balances:
                cash_balances.append(
                    CashBalance(
                        account=balance.account,
                        krw=balance.krw,
                        usd=balance.usd,
                        updated_at=balance.updated_at,
                    )
                )

            time_deposits = []
            for deposit in summary.time_deposits:
                time_deposits.append(
                    TimeDeposit(
                        account=deposit.account,
                        invest_prod_name=deposit.invest_prod_name,
                        market_value=deposit.market_value,
                        invested_principal=deposit.invested_principal,
                        maturity_date=deposit.maturity_date,
                        interest_rate=deposit.interest_rate,
                        updated_at=deposit.updated_at,
                    )
                )

            latest_bs_entry = None
            if summary.latest_bs_entry:
                latest_bs_entry = BSTimeseries(
                    date=summary.latest_bs_entry.date,
                    cash=summary.latest_bs_entry.cash,
                    time_deposit=summary.latest_bs_entry.time_deposit,
                    security_cash_balance=summary.latest_bs_entry.security_cash_balance,
                    updated_at=summary.latest_bs_entry.updated_at,
                )

            return CashManagementSummary(
                total_cash=summary.total_cash,
                total_cash_balance=summary.total_cash_balance,
                total_time_deposit=summary.total_time_deposit,
                total_security_cash=summary.total_security_cash,
                cash_balances=cash_balances,
                time_deposits=time_deposits,
                latest_bs_entry=latest_bs_entry,
                updated_at=summary.updated_at,
            )
        except Exception as e:
            logger.error(f"현금 관리 요약 정보 조회 오류: {e}")
            raise

    async def update_current_cash(
        self,
        cash: Optional[int] = None,
        time_deposit: Optional[int] = None,
        security_cash_balance: Optional[int] = None,
        reason: Optional[str] = None,
    ) -> bool:
        """현재 현금 정보 선택적 업데이트"""
        try:
            return await self.cash_service.update_current_cash(
                cash, time_deposit, security_cash_balance, reason
            )
        except Exception as e:
            logger.error(f"현금 정보 업데이트 오류: {e}")
            raise

    # Currency methods
    async def get_currency_rates(
        self, auto_update: bool = True, currencies: Optional[List[str]] = None
    ) -> List[CurrencyRate]:
        """환율 정보 조회"""
        try:
            rates = await self.currency_service.get_currency_rates(
                auto_update, currencies
            )

            currency_rates = []
            for rate in rates:
                currency_rate = CurrencyRate(
                    currency=rate.currency,
                    exchange_rate=rate.exchange_rate,
                    updated_at=rate.updated_at,
                )
                currency_rates.append(currency_rate)

            return currency_rates
        except Exception as e:
            logger.error(f"환율 정보 조회 오류: {e}")
            raise

    async def update_currency_rates(self, currencies: List[str]) -> List[CurrencyRate]:
        """특정 통화들의 환율 정보 업데이트"""
        try:
            rates = await self.currency_service.update_currency_rates(currencies)

            currency_rates = []
            for rate in rates:
                currency_rate = CurrencyRate(
                    currency=rate.currency,
                    exchange_rate=rate.exchange_rate,
                    updated_at=rate.updated_at,
                )
                currency_rates.append(currency_rate)

            return currency_rates
        except Exception as e:
            logger.error(f"환율 정보 업데이트 오류: {e}")
            raise

    # Analytics methods
    async def get_performance_data(
        self, account: Optional[str] = None
    ) -> PerformanceData:
        """성과 분석 데이터 조회"""
        try:
            # 기본 성과 데이터 생성 (추후 확장 가능)
            return PerformanceData(
                daily_returns=[],
                cumulative_returns=[],
                volatility=0.0,
                sharpe_ratio=0.0,
                max_drawdown=0.0,
                updated_at=datetime.now(),
            )
        except Exception as e:
            logger.error(f"성과 분석 데이터 조회 오류: {e}")
            raise

    async def get_market_summary(self) -> MarketSummary:
        """시장 요약 정보 조회"""
        try:
            # 기본 시장 요약 정보 생성 (추후 확장 가능)
            return MarketSummary(
                kospi=0.0,
                kosdaq=0.0,
                sp_500=0.0,
                nasdaq=0.0,
                updated_at=datetime.now(),
            )
        except Exception as e:
            logger.error(f"시장 요약 정보 조회 오류: {e}")
            raise

    # Synchronization methods
    async def refresh_all_data(self) -> Dict[str, Any]:
        """모든 데이터 새로고침"""
        try:
            return await self.portfolio_service.refresh_portfolio_data()
        except Exception as e:
            logger.error(f"전체 데이터 새로고침 오류: {e}")
            raise

    # Health check
    async def health_check(self) -> Dict[str, Any]:
        """데이터베이스 연결 상태 확인"""
        try:
            is_healthy = await self.db_connection.health_check()

            return {
                "status": "healthy" if is_healthy else "unhealthy",
                "timestamp": datetime.now().isoformat(),
                "database": "supabase",
                "services": {
                    "portfolio": "active",
                    "holdings": "active",
                    "cash": "active",
                    "currency": "active",
                    "sync": "active",
                },
            }
        except Exception as e:
            logger.error(f"헬스 체크 오류: {e}")
            return {
                "status": "error",
                "timestamp": datetime.now().isoformat(),
                "error": str(e),
            }
