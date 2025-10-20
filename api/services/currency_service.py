"""Currency service for handling exchange rate operations."""

import logging
from datetime import date, datetime, timedelta
from typing import List, Optional

from .interfaces import ICurrencyService
from ..database_modules.repositories import CurrencyRepository
from ..adapters.currency_adapter import CurrencyAdapter
from ..database_modules.models import DatabaseModels

logger = logging.getLogger(__name__)


class CurrencyService(ICurrencyService):
    """환율 서비스."""

    def __init__(
        self, currency_repository: CurrencyRepository, currency_adapter: CurrencyAdapter
    ):
        self.currency_repository = currency_repository
        self.currency_adapter = currency_adapter

    async def get_currency_rates(
        self, auto_update: bool = True, currencies: Optional[List[str]] = None
    ) -> List[DatabaseModels.CurrencyRate]:
        """환율 정보 조회 (자동 업데이트 옵션 포함)"""
        try:
            logger.info(
                f"💱 환율 정보 조회 시작 - 통화: {currencies if currencies else '전체'}"
            )

            # 특정 통화만 조회할 경우 필터링
            existing_rates_data = self.currency_repository.get_currency_rates(
                currencies
            )
            logger.debug(f"기존 환율 데이터: {len(existing_rates_data)}개")

            # 가장 최근 영업일 계산
            latest_business_date = self._get_latest_business_date()
            logger.info(f"📅 최근 영업일: {latest_business_date}")

            rates = []
            outdated_currencies = []

            for item in existing_rates_data:
                # updated_at이 문자열인 경우 datetime으로 변환
                updated_at = item.get("updated_at")
                if isinstance(updated_at, str):
                    try:
                        updated_at = datetime.fromisoformat(
                            updated_at.replace("Z", "+00:00")
                        )
                    except:
                        updated_at = datetime.now()
                elif updated_at is None:
                    updated_at = datetime.now()

                # 날짜 비교 (최근 영업일과 다르면 오래된 것으로 간주)
                update_date = (
                    updated_at.date()
                    if hasattr(updated_at, "date")
                    else latest_business_date
                )
                is_outdated = update_date != latest_business_date

                if is_outdated:
                    outdated_currencies.append(item.get("currency"))
                    logger.warning(
                        f"⚠️ {item.get('currency')} 환율 정보가 오래됨 - "
                        f"마지막 업데이트: {update_date}, 최근 영업일: {latest_business_date}"
                    )

                rate = DatabaseModels.CurrencyRate(
                    currency=item.get("currency"),
                    exchange_rate=float(item.get("exchange_rate", 0)),
                    updated_at=updated_at,
                )
                rates.append(rate)

            # 오래된 환율이 있고 자동 업데이트가 활성화된 경우
            if outdated_currencies and auto_update:
                logger.info(
                    f"🔄 오래된 환율 정보 자동 업데이트 시작: {outdated_currencies}"
                )
                updated_rates = await self.currency_adapter.update_currency_rates(
                    outdated_currencies
                )

                # 업데이트된 환율로 교체
                for updated_rate in updated_rates:
                    for i, rate in enumerate(rates):
                        if rate.currency == updated_rate.currency:
                            rates[i] = updated_rate
                            break

            logger.info(f"✅ 환율 정보 조회 완료 - {len(rates)}개 통화")
            if outdated_currencies:
                logger.info(
                    f"📝 오래된 환율: {len(outdated_currencies)}개, 업데이트 완료"
                )

            return rates

        except Exception as e:
            logger.error(f"환율 정보 조회 오류: {e}")
            raise

    async def update_currency_rates(
        self, currencies: List[str]
    ) -> List[DatabaseModels.CurrencyRate]:
        """특정 통화들의 환율 정보 업데이트"""
        try:
            logger.info(f"🔄 환율 업데이트 시작: {currencies}")
            updated_rates = await self.currency_adapter.update_currency_rates(
                currencies
            )

            # 데이터베이스에 업데이트된 환율 저장
            saved_rates = []
            for rate in updated_rates:
                success = self.currency_repository.update_currency_rate(
                    rate.currency,
                    rate.exchange_rate,
                    rate.updated_at.date() if rate.updated_at else date.today(),
                )
                if success:
                    saved_rates.append(rate)
                    logger.info(f"✅ {rate.currency} 환율 DB 저장 성공")
                else:
                    logger.error(f"❌ {rate.currency} 환율 DB 저장 실패")

            logger.info(f"🏁 환율 업데이트 완료: {len(saved_rates)}개 성공")
            return saved_rates

        except Exception as e:
            logger.error(f"환율 업데이트 전체 오류: {e}")
            return []

    def _get_latest_business_date(self) -> date:
        """가장 최근 영업일을 계산하여 반환

        Returns:
            date: 최근 영업일 (평일 20시 이전이면 전날, 주말이면 금요일)
        """
        now = datetime.now()
        latest_business_day = now

        # 평일 20시 이전이면 전날로
        if now.hour < 20:
            latest_business_day = now - timedelta(days=1)

        # 주말이면 가장 최근 금요일로
        while latest_business_day.weekday() >= 5:  # 5=토요일, 6=일요일
            latest_business_day = latest_business_day - timedelta(days=1)

        return latest_business_day.date()
