"""Service interfaces defining contracts for business logic."""

from abc import ABC, abstractmethod
from datetime import date, datetime
from typing import List, Optional, Dict, Any

from ..database_modules.models import DatabaseModels


class IPortfolioService(ABC):
    """포트폴리오 서비스 인터페이스."""

    @abstractmethod
    async def get_portfolio_overview(
        self, account: Optional[str] = None
    ) -> DatabaseModels.PortfolioOverview:
        """포트폴리오 전체 현황 조회"""
        pass

    @abstractmethod
    async def get_asset_allocation(
        self, account: Optional[str] = None, auto_add_unmatched: bool = True
    ) -> DatabaseModels.AssetAllocationResponse:
        """자산 분배 현황 조회"""
        pass

    @abstractmethod
    async def get_unmatched_products(
        self, account: Optional[str] = None
    ) -> DatabaseModels.UnmatchedProductsResponse:
        """매칭되지 않는 상품 조회"""
        pass

    @abstractmethod
    async def add_unmatched_to_symbol_table(
        self, unmatched_response: DatabaseModels.UnmatchedProductsResponse
    ) -> Dict[str, int]:
        """매칭되지 않는 상품들을 symbol_table에 추가"""
        pass


class IHoldingsService(ABC):
    """보유 종목 서비스 인터페이스."""

    @abstractmethod
    async def get_holdings(
        self, account: Optional[str] = None, market: Optional[str] = None
    ) -> List[DatabaseModels.HoldingResponse]:
        """보유 종목 정보 조회"""
        pass

    @abstractmethod
    async def get_all_stocks(self) -> List[DatabaseModels.StockInfo]:
        """모든 주식 정보 조회"""
        pass

    @abstractmethod
    async def get_performance_data(
        self, account: str
    ) -> Optional[DatabaseModels.PerformanceData]:
        """계좌별 성과 분석 데이터"""
        pass

    @abstractmethod
    async def update_symbol_table_prices(self) -> Dict[str, Any]:
        """symbol_table의 모든 종목 최신 가격 업데이트"""
        pass

    @abstractmethod
    async def update_symbol_sector_info(self) -> Dict[str, Any]:
        """symbol_table에서 sector/industry가 None인 항목 업데이트"""
        pass


class ICurrencyService(ABC):
    """환율 서비스 인터페이스."""

    @abstractmethod
    async def get_currency_rates(
        self, auto_update: bool = True, currencies: Optional[List[str]] = None
    ) -> List[DatabaseModels.CurrencyRate]:
        """환율 정보 조회 (자동 업데이트 옵션 포함)"""
        pass

    @abstractmethod
    async def update_currency_rates(
        self, currencies: List[str]
    ) -> List[DatabaseModels.CurrencyRate]:
        """특정 통화들의 환율 정보 업데이트"""
        pass

    @abstractmethod
    def _get_latest_business_date(self) -> date:
        """가장 최근 영업일을 계산하여 반환"""
        pass


class ICashService(ABC):
    """현금 관리 서비스 인터페이스."""

    @abstractmethod
    async def get_cash_balances(
        self, account: Optional[str] = None
    ) -> List[DatabaseModels.CashBalance]:
        """증권사별 예수금 정보 조회"""
        pass

    @abstractmethod
    async def update_cash_balance(
        self, account: str, krw: Optional[float] = None, usd: Optional[float] = None
    ) -> bool:
        """증권사별 예수금 업데이트"""
        pass

    @abstractmethod
    async def get_time_deposits(
        self, account: Optional[str] = None
    ) -> List[DatabaseModels.TimeDeposit]:
        """예적금 정보 조회"""
        pass

    @abstractmethod
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
        pass

    @abstractmethod
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
        pass

    @abstractmethod
    async def delete_time_deposit(self, account: str, invest_prod_name: str) -> bool:
        """예적금 삭제"""
        pass

    @abstractmethod
    async def get_cash_management_summary(self) -> DatabaseModels.CashManagementSummary:
        """현금 관리 요약 정보 조회"""
        pass

    @abstractmethod
    async def get_latest_bs_entry(self) -> Optional[Dict[str, Any]]:
        """가장 최신 bs_timeseries 항목 조회"""
        pass

    @abstractmethod
    async def update_current_cash(
        self,
        cash: Optional[int] = None,
        time_deposit: Optional[int] = None,
        security_cash_balance: Optional[int] = None,
        reason: Optional[str] = None,
    ) -> bool:
        """현재 현금 정보 선택적 업데이트 (bs_timeseries)"""
        pass


class ISyncService(ABC):
    """동기화 서비스 인터페이스."""

    @abstractmethod
    async def sync_bs_timeseries_from_cash_balances(self) -> None:
        """cash_balance 테이블의 데이터를 기반으로 bs_timeseries 테이블 동기화"""
        pass

    @abstractmethod
    async def sync_bs_timeseries_from_time_deposits(self) -> None:
        """time_deposit 테이블의 데이터를 기반으로 bs_timeseries 테이블 동기화"""
        pass

    @abstractmethod
    async def orchestrate_sync_operations(self) -> Dict[str, Any]:
        """모든 동기화 작업 오케스트레이션"""
        pass
