"""Repository pattern implementation for data access layer."""

from abc import ABC, abstractmethod
from datetime import date, datetime, timedelta
from typing import List, Optional, Dict, Any
import logging

from .connection import DatabaseConnection
from .models import DatabaseModels

logger = logging.getLogger(__name__)


class BaseRepository(ABC):
    """베이스 리포지토리 추상 클래스."""

    def __init__(self, connection: DatabaseConnection):
        self.connection = connection
        self.supabase = connection.get_client()

    def _get_latest_business_date(self) -> date:
        """가장 최근 영업일을 계산하여 반환"""
        now = datetime.now()
        latest_business_day = now

        # 평일 20시 이전이면 전날로
        if now.hour < 20:
            latest_business_day = now - timedelta(days=1)

        # 주말이면 가장 최근 금요일로
        while latest_business_day.weekday() >= 5:  # 5=토요일, 6=일요일
            latest_business_day = latest_business_day - timedelta(days=1)

        return latest_business_day.date()


class PortfolioRepository(BaseRepository):
    """포트폴리오 관련 데이터 접근 리포지토리."""

    def get_overall_info(self, account: Optional[str] = None) -> List[Dict[str, Any]]:
        """overall_info 테이블 데이터 조회"""
        try:
            query = self.supabase.table("overall_info").select("*")
            if account:
                query = query.eq("account", account)
            response = query.execute()
            return response.data
        except Exception as e:
            logger.error(f"overall_info 조회 오류: {e}")
            raise

    def get_by_accounts(self, account: Optional[str] = None) -> List[Dict[str, Any]]:
        """by_accounts 테이블 데이터 조회"""
        try:
            query = self.supabase.table("by_accounts").select("*")
            if account:
                query = query.eq("account", account)
            response = query.execute()
            return response.data
        except Exception as e:
            logger.error(f"by_accounts 조회 오류: {e}")
            raise

    def get_funds(self, account: Optional[str] = None) -> List[Dict[str, Any]]:
        """funds 테이블 데이터 조회"""
        try:
            query = self.supabase.table("funds").select("*")
            if account:
                query = query.eq("account", account)
            response = query.execute()
            return response.data
        except Exception as e:
            logger.error(f"funds 조회 오류: {e}")
            raise

    def get_symbol_table(self) -> List[Dict[str, Any]]:
        """symbol_table 테이블 전체 조회"""
        try:
            response = self.supabase.table("symbol_table").select("*").execute()
            return response.data
        except Exception as e:
            logger.error(f"symbol_table 조회 오류: {e}")
            raise

    def add_symbol_to_table(self, symbol_data: Dict[str, Any]) -> bool:
        """symbol_table에 새 종목 추가"""
        try:
            response = self.supabase.table("symbol_table").insert(symbol_data).execute()
            return len(response.data) > 0
        except Exception as e:
            logger.error(f"symbol_table 추가 오류: {e}")
            raise

    def update_symbol_price(self, name: str, price_data: Dict[str, Any]) -> bool:
        """symbol_table 가격 정보 업데이트"""
        try:
            response = (
                self.supabase.table("symbol_table")
                .update(price_data)
                .eq("name", name)
                .execute()
            )
            return len(response.data) > 0
        except Exception as e:
            logger.error(f"symbol_table 가격 업데이트 오류: {e}")
            raise

    def update_symbol_sector_info(self, name: str, sector_data: Dict[str, Any]) -> bool:
        """symbol_table 섹터/산업 정보 업데이트"""
        try:
            response = (
                self.supabase.table("symbol_table")
                .update(sector_data)
                .eq("name", name)
                .execute()
            )
            return len(response.data) > 0
        except Exception as e:
            logger.error(f"symbol_table 섹터 정보 업데이트 오류: {e}")
            raise


class HoldingsRepository(BaseRepository):
    """보유 종목 관련 데이터 접근 리포지토리."""

    def get_stock_info(self) -> List[Dict[str, Any]]:
        """stock_info 테이블 데이터 조회"""
        try:
            response = self.supabase.table("stock_info").select("*").execute()
            return response.data
        except Exception as e:
            logger.error(f"stock_info 조회 오류: {e}")
            raise

    def get_holdings_by_account(self, account: str) -> List[Dict[str, Any]]:
        """계좌별 보유 종목 조회"""
        try:
            response = (
                self.supabase.table("overall_info")
                .select("*")
                .eq("account", account)
                .execute()
            )
            return response.data
        except Exception as e:
            logger.error(f"계좌별 보유 종목 조회 오류: {e}")
            raise

    def get_all_holdings(
        self, account: Optional[str] = None, market: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """모든 보유 종목 조회"""
        try:
            query = self.supabase.table("overall_info").select("*")
            if account:
                query = query.eq("account", account)
            if market:
                query = query.eq("market", market)
            response = query.execute()
            return response.data
        except Exception as e:
            logger.error(f"보유 종목 조회 오류: {e}")
            raise


class CurrencyRepository(BaseRepository):
    """환율 관련 데이터 접근 리포지토리."""

    def get_currency_rates(
        self, currencies: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """환율 정보 조회"""
        try:
            query = self.supabase.table("currency").select("*")
            if currencies:
                query = query.in_("currency", currencies)
            response = query.execute()
            return response.data
        except Exception as e:
            logger.error(f"환율 정보 조회 오류: {e}")
            raise

    def update_currency_rate(
        self, currency: str, exchange_rate: float, update_date: date
    ) -> bool:
        """환율 정보 업데이트"""
        try:
            response = (
                self.supabase.table("currency")
                .update(
                    {
                        "exchange_rate": exchange_rate,
                        "updated_at": update_date.isoformat(),
                    }
                )
                .eq("currency", currency)
                .execute()
            )
            return len(response.data) > 0
        except Exception as e:
            logger.error(f"환율 업데이트 오류: {e}")
            raise


class CashRepository(BaseRepository):
    """현금 관련 데이터 접근 리포지토리."""

    def get_cash_balances(self, account: Optional[str] = None) -> List[Dict[str, Any]]:
        """증권사별 예수금 정보 조회"""
        try:
            query = self.supabase.table("cash_balance").select("*")
            if account:
                query = query.eq("account", account)
            response = query.execute()
            return response.data
        except Exception as e:
            logger.error(f"현금 잔액 조회 오류: {e}")
            raise

    def update_cash_balance(self, account: str, update_data: Dict[str, Any]) -> bool:
        """증권사별 예수금 업데이트"""
        try:
            response = (
                self.supabase.table("cash_balance")
                .update(update_data)
                .eq("account", account)
                .execute()
            )
            return len(response.data) > 0
        except Exception as e:
            logger.error(f"현금 잔액 업데이트 오류: {e}")
            raise

    def get_time_deposits(self, account: Optional[str] = None) -> List[Dict[str, Any]]:
        """예적금 정보 조회"""
        try:
            query = self.supabase.table("time_deposit").select("*")
            if account:
                query = query.eq("account", account)
            response = query.execute()
            return response.data
        except Exception as e:
            logger.error(f"예적금 정보 조회 오류: {e}")
            raise

    def create_time_deposit(self, deposit_data: Dict[str, Any]) -> bool:
        """예적금 생성"""
        try:
            response = (
                self.supabase.table("time_deposit").insert(deposit_data).execute()
            )
            return len(response.data) > 0
        except Exception as e:
            logger.error(f"예적금 생성 오류: {e}")
            raise

    def update_time_deposit(
        self, account: str, invest_prod_name: str, update_data: Dict[str, Any]
    ) -> bool:
        """예적금 수정"""
        try:
            response = (
                self.supabase.table("time_deposit")
                .update(update_data)
                .eq("account", account)
                .eq("invest_prod_name", invest_prod_name)
                .execute()
            )
            return len(response.data) > 0
        except Exception as e:
            logger.error(f"예적금 수정 오류: {e}")
            raise

    def delete_time_deposit(self, account: str, invest_prod_name: str) -> bool:
        """예적금 삭제"""
        try:
            response = (
                self.supabase.table("time_deposit")
                .delete()
                .eq("account", account)
                .eq("invest_prod_name", invest_prod_name)
                .execute()
            )
            return len(response.data) > 0
        except Exception as e:
            logger.error(f"예적금 삭제 오류: {e}")
            raise

    def get_latest_bs_entry(self) -> Optional[Dict[str, Any]]:
        """가장 최신 bs_timeseries 항목 조회"""
        try:
            response = (
                self.supabase.table("bs_timeseries")
                .select("*")
                .order("date", desc=True)
                .limit(1)
                .execute()
            )
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"최신 bs_timeseries 조회 오류: {e}")
            raise

    def update_bs_timeseries(self, date: date, update_data: Dict[str, Any]) -> bool:
        """bs_timeseries 업데이트"""
        try:
            response = (
                self.supabase.table("bs_timeseries")
                .update(update_data)
                .eq("date", date.isoformat())
                .execute()
            )
            return len(response.data) > 0
        except Exception as e:
            logger.error(f"bs_timeseries 업데이트 오류: {e}")
            raise

    def create_bs_timeseries(self, bs_data: Dict[str, Any]) -> bool:
        """bs_timeseries 신규 항목 생성"""
        try:
            response = self.supabase.table("bs_timeseries").insert(bs_data).execute()
            return len(response.data) > 0
        except Exception as e:
            logger.error(f"bs_timeseries 생성 오류: {e}")
            raise

    def get_bs_timeseries_by_date(self, date: date) -> Optional[Dict[str, Any]]:
        """특정 날짜의 bs_timeseries 조회"""
        try:
            response = (
                self.supabase.table("bs_timeseries")
                .select("*")
                .eq("date", date.isoformat())
                .execute()
            )
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"bs_timeseries 날짜별 조회 오류: {e}")
            raise
