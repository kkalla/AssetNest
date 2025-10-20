"""Currency adapter for external exchange rate APIs."""

import asyncio
import logging
import os
from abc import ABC, abstractmethod
from datetime import date, datetime, timedelta
from typing import List, Dict, Any, Optional
import time

import requests
from ..database_modules.models import DatabaseModels

logger = logging.getLogger(__name__)


class ICurrencyProvider(ABC):
    """환율 제공자 인터페이스."""

    @abstractmethod
    async def get_exchange_rates(self, search_date: date) -> Dict[str, float]:
        """특정 날짜의 환율 정보 조회"""
        pass

    @abstractmethod
    async def update_rates(
        self, currencies: List[str]
    ) -> List[DatabaseModels.CurrencyRate]:
        """특정 통화들의 환율 업데이트"""
        pass


class KoreaEximAdapter(ICurrencyProvider):
    """한국수출입은행 환율 API 어댑터."""

    def __init__(self, max_retries: int = 3, retry_delay: float = 1.0):
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.api_key = os.environ.get("KOREAEXIM_API_KEY")

    async def _retry_async_call(self, func, *args, **kwargs):
        """비동기 함수 재시도 래퍼"""
        for attempt in range(self.max_retries):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                if attempt == self.max_retries - 1:
                    raise
                logger.warning(
                    f"Attempt {attempt + 1} failed: {e}, retrying in {self.retry_delay}s..."
                )
                await asyncio.sleep(self.retry_delay)
                self.retry_delay *= 2  # Exponential backoff

    def _retry_sync_call(self, func, *args, **kwargs):
        """동기 함수 재시도 래퍼"""
        for attempt in range(self.max_retries):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if attempt == self.max_retries - 1:
                    raise
                logger.warning(
                    f"Attempt {attempt + 1} failed: {e}, retrying in {self.retry_delay}s..."
                )
                time.sleep(self.retry_delay)
                self.retry_delay *= 2  # Exponential backoff

    async def get_exchange_rates(self, search_date: date) -> Dict[str, float]:
        """한국수출입은행 API에서 환율 정보 조회"""
        if not self.api_key:
            logger.error("❌ KOREAEXIM_API_KEY 환경변수가 설정되지 않음")
            return {}

        def _fetch_rates():
            search_date_str = search_date.strftime("%Y%m%d")
            url = "https://oapi.koreaexim.go.kr/site/program/financial/exchangeJSON"
            params = {
                "authkey": self.api_key,
                "searchdate": search_date_str,
                "data": "AP01",  # 환율
            }

            try:
                response = requests.get(url, params=params, timeout=10)
                if response.status_code == 200:
                    data = response.json()

                    # 통화코드 매핑 (API 응답 → DB 통화코드)
                    currency_mapping = {}
                    for item in data:
                        cur_unit = item.get("cur_unit", "")
                        # 괄호 앞부분만 추출
                        currency_code = cur_unit.split("(")[0].strip()

                        # deal_bas_r: 매매기준율 (쉼표 제거 후 float 변환)
                        rate_str = item.get("deal_bas_r", "")
                        if rate_str:
                            try:
                                exchange_rate = float(rate_str.replace(",", ""))
                                currency_mapping[currency_code] = exchange_rate
                            except ValueError as e:
                                logger.error(f"❌ {currency_code} 환율 변환 오류: {e}")

                    logger.info(
                        f"✅ 한국수출입은행 환율 조회 성공: {len(currency_mapping)}개 통화"
                    )
                    return currency_mapping
                else:
                    logger.error(
                        f"❌ 한국수출입은행 API 호출 실패: {response.status_code}"
                    )
                    return {}
            except requests.RequestException as e:
                logger.error(f"❌ 한국수출입은행 API 호출 오류: {e}")
                return {}
            except Exception as e:
                logger.error(f"❌ 환율 데이터 처리 오류: {e}")
                return {}

        return await self._retry_async_call(asyncio.to_thread, _fetch_rates)

    async def update_rates(
        self, currencies: List[str]
    ) -> List[DatabaseModels.CurrencyRate]:
        """특정 통화들의 환율 정보 업데이트"""
        if not self.api_key:
            logger.error("❌ KOREAEXIM_API_KEY 환경변수가 설정되지 않음")
            return []

        # 가장 최근 영업일 찾기
        latest_business_date = self._get_latest_business_date()
        search_date_str = latest_business_date.strftime("%Y%m%d")
        logger.info(f"📅 환율 조회 날짜: {search_date_str}")

        def _update_rates():
            url = "https://oapi.koreaexim.go.kr/site/program/financial/exchangeJSON"
            params = {
                "authkey": self.api_key,
                "searchdate": search_date_str,
                "data": "AP01",
            }

            try:
                response = requests.get(url, params=params, timeout=10)
                if response.status_code == 200:
                    data = response.json()

                    # 통화코드 매핑
                    currency_mapping = {}
                    for item in data:
                        cur_unit = item.get("cur_unit", "")
                        currency_code = cur_unit.split("(")[0].strip()
                        currency_mapping[currency_code] = item

                    updated_rates = []

                    # 요청된 통화들 처리
                    for currency in currencies:
                        if currency in currency_mapping:
                            item = currency_mapping[currency]
                            rate_str = item.get("deal_bas_r", "")

                            if rate_str:
                                try:
                                    exchange_rate = float(rate_str.replace(",", ""))

                                    currency_rate = DatabaseModels.CurrencyRate(
                                        currency=currency,
                                        exchange_rate=exchange_rate,
                                        updated_at=datetime.combine(
                                            latest_business_date,
                                            datetime.min.time(),
                                        ),
                                    )
                                    updated_rates.append(currency_rate)
                                    logger.info(
                                        f"✅ {currency} 환율 업데이트 성공: {exchange_rate}"
                                    )
                                except ValueError as e:
                                    logger.error(f"❌ {currency} 환율 변환 오류: {e}")
                            else:
                                logger.error(f"❌ {currency} 환율 데이터 없음")
                        else:
                            logger.warning(f"⚠️ {currency} API 응답에 없음")

                    logger.info(f"🏁 환율 업데이트 완료: {len(updated_rates)}개 성공")
                    return updated_rates
                else:
                    logger.error(
                        f"❌ 한국수출입은행 API 호출 실패: {response.status_code}"
                    )
                    return []
            except requests.RequestException as e:
                logger.error(f"❌ 한국수출입은행 API 호출 오류: {e}")
                return []
            except Exception as e:
                logger.error(f"❌ 환율 데이터 처리 오류: {e}")
                return []

        return await self._retry_async_call(asyncio.to_thread, _update_rates)

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


class CurrencyAdapter:
    """환율 서비스 어댑터."""

    def __init__(self, provider: ICurrencyProvider = None):
        self.provider = provider or KoreaEximAdapter()

    async def get_currency_rates(
        self, auto_update: bool = True, currencies: Optional[List[str]] = None
    ) -> List[DatabaseModels.CurrencyRate]:
        """환율 정보 조회 (자동 업데이트 옵션 포함)"""
        try:
            logger.info(
                f"💱 환율 정보 조회 시작 - 통화: {currencies if currencies else '전체'}"
            )

            # 특정 통화만 조회할 경우 필터링
            existing_rates = await self.provider.get_exchange_rates(
                self.provider._get_latest_business_date()
                if hasattr(self.provider, "_get_latest_business_date")
                else date.today()
            )

            # 가장 최근 영업일 계산
            latest_business_date = (
                self.provider._get_latest_business_date()
                if hasattr(self.provider, "_get_latest_business_date")
                else date.today()
            )
            logger.info(f"📅 최근 영업일: {latest_business_date}")

            rates = []
            outdated_currencies = []

            for currency_code, exchange_rate in existing_rates.items():
                if currencies and currency_code not in currencies:
                    continue

                rate = DatabaseModels.CurrencyRate(
                    currency=currency_code,
                    exchange_rate=exchange_rate,
                    updated_at=datetime.combine(
                        latest_business_date, datetime.min.time()
                    ),
                )
                rates.append(rate)

            # 오래된 환율이 있고 자동 업데이트가 활성화된 경우
            if outdated_currencies and auto_update:
                logger.info(
                    f"🔄 오래된 환율 정보 자동 업데이트 시작: {outdated_currencies}"
                )
                updated_rates = await self.provider.update_rates(outdated_currencies)

                # 업데이트된 환율로 교체
                for updated_rate in updated_rates:
                    for i, rate in enumerate(rates):
                        if rate.currency == updated_rate.currency:
                            rates[i] = updated_rate
                            break

            logger.info(f"✅ 환율 정보 조회 완료 - {len(rates)}개 통화")
            return rates

        except Exception as e:
            logger.error(f"환율 정보 조회 오류: {e}")
            return []

    async def update_currency_rates(
        self, currencies: List[str]
    ) -> List[DatabaseModels.CurrencyRate]:
        """특정 통화들의 환율 정보 업데이트"""
        try:
            logger.info(f"🔄 환율 업데이트 시작: {currencies}")
            updated_rates = await self.provider.update_rates(currencies)
            logger.info(f"🏁 환율 업데이트 완료: {len(updated_rates)}개 성공")
            return updated_rates
        except Exception as e:
            logger.error(f"환율 업데이트 전체 오류: {e}")
            return []
