"""Cash management service for handling cash balances and time deposits."""

import logging
from datetime import date, datetime
from typing import List, Optional, Dict, Any

from .interfaces import ICashService, ISyncService
from ..database_modules.repositories import CashRepository
from ..database_modules.models import DatabaseModels

logger = logging.getLogger(__name__)


class CashService(ICashService):
    """현금 관리 서비스."""

    def __init__(self, cash_repository: CashRepository, sync_service: ISyncService):
        self.cash_repository = cash_repository
        self.sync_service = sync_service

    async def get_cash_balances(
        self, account: Optional[str] = None
    ) -> List[DatabaseModels.CashBalance]:
        """증권사별 예수금 정보 조회"""
        try:
            cash_balances_data = self.cash_repository.get_cash_balances(account)

            cash_balances = []
            for item in cash_balances_data:
                cash_balance = DatabaseModels.CashBalance(
                    account=item.get("account"),
                    krw=float(item.get("krw", 0)),
                    usd=float(item.get("usd", 0)),
                    updated_at=datetime.now(),
                )
                cash_balances.append(cash_balance)

            return cash_balances

        except Exception as e:
            logger.error(f"현금 잔액 조회 오류: {e}")
            raise

    async def update_cash_balance(
        self, account: str, krw: Optional[float] = None, usd: Optional[float] = None
    ) -> bool:
        """증권사별 예수금 업데이트"""
        try:
            update_data = {}
            if krw is not None:
                update_data["krw"] = int(krw) if isinstance(krw, (int, float)) else krw
            if usd is not None:
                update_data["usd"] = (
                    float(usd) if isinstance(usd, (int, float)) else usd
                )

            if not update_data:
                logger.warning(f"⚠️ {account}: 업데이트할 데이터가 없음")
                return False

            logger.info(f"🔄 {account} 현금 잔액 업데이트 시도: {update_data}")

            # 먼저 해당 계좌가 존재하는지 확인
            existing = self.cash_repository.get_cash_balances(account)
            if not existing:
                logger.error(f"❌ {account} 계좌를 찾을 수 없음")
                return False

            result = self.cash_repository.update_cash_balance(account, update_data)

            if result:
                logger.info(f"✅ {account} 현금 잔액 업데이트 성공: {update_data}")

                # bs_timeseries 테이블에 security_cash_balance 동기화
                await self.sync_service.sync_bs_timeseries_from_cash_balances()

                return True
            else:
                logger.error(f"❌ {account} 현금 잔액 업데이트 실패 - 데이터 없음")
                return False

        except Exception as e:
            logger.error(f"현금 잔액 업데이트 오류: {e}")
            import traceback

            logger.error(f"상세 에러: {traceback.format_exc()}")
            raise

    async def get_time_deposits(
        self, account: Optional[str] = None
    ) -> List[DatabaseModels.TimeDeposit]:
        """예적금 정보 조회"""
        try:
            time_deposits_data = self.cash_repository.get_time_deposits(account)

            time_deposits = []
            for item in time_deposits_data:
                time_deposit = DatabaseModels.TimeDeposit(
                    account=item.get("account"),
                    invest_prod_name=item.get("invest_prod_name"),
                    market_value=item.get("market_value", 0),
                    invested_principal=item.get("invested_principal", 0),
                    maturity_date=item.get("maturity_date"),
                    interest_rate=item.get("interest_rate"),
                    updated_at=datetime.now(),
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
            insert_data = {
                "account": account,
                "invest_prod_name": invest_prod_name,
                "market_value": market_value,
                "invested_principal": invested_principal,
                "updated_at": datetime.now(),
            }

            if maturity_date:
                insert_data["maturity_date"] = maturity_date
            if interest_rate:
                insert_data["interest_rate"] = interest_rate

            logger.debug(f"Insert data: {insert_data}")
            result = self.cash_repository.create_time_deposit(insert_data)

            if result:
                logger.info(f"✅ 예적금 생성 성공: {invest_prod_name}")

                # bs_timeseries 테이블 동기화
                await self.sync_service.sync_bs_timeseries_from_time_deposits()

                return True
            else:
                logger.error(f"❌ 예적금 생성 실패: {invest_prod_name}")
                return False

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
            update_data = {}
            if market_value is not None:
                update_data["market_value"] = market_value
            if invested_principal is not None:
                update_data["invested_principal"] = invested_principal
            if maturity_date is not None:
                update_data["maturity_date"] = maturity_date
            if interest_rate is not None:
                update_data["interest_rate"] = interest_rate

            if not update_data:
                return False

            logger.debug(f"Update data: {update_data}")
            result = self.cash_repository.update_time_deposit(
                account, invest_prod_name, update_data
            )

            if result:
                logger.info(f"✅ 예적금 수정 성공: {invest_prod_name}")

                # bs_timeseries 테이블 동기화
                await self.sync_service.sync_bs_timeseries_from_time_deposits()

                return True
            else:
                logger.error(f"❌ 예적금 수정 실패: {invest_prod_name}")
                return False

        except Exception as e:
            logger.error(f"예적금 수정 오류: {e}")
            raise

    async def delete_time_deposit(self, account: str, invest_prod_name: str) -> bool:
        """예적금 삭제"""
        try:
            result = self.cash_repository.delete_time_deposit(account, invest_prod_name)

            if result:
                logger.info(f"✅ 예적금 삭제 성공: {invest_prod_name}")

                # bs_timeseries 테이블 동기화
                await self.sync_service.sync_bs_timeseries_from_time_deposits()

                return True
            else:
                logger.error(f"❌ 예적금 삭제 실패: {invest_prod_name}")
                return False

        except Exception as e:
            logger.error(f"예적금 삭제 오류: {e}")
            raise

    async def get_cash_management_summary(self) -> DatabaseModels.CashManagementSummary:
        """현금 관리 요약 정보 조회"""
        try:
            # 1. 현금 잔액 조회
            cash_balances = await self.get_cash_balances()

            # 2. 예적금 조회
            time_deposits = await self.get_time_deposits()

            # 3. 최신 bs_timeseries 조회
            latest_bs = await self.get_latest_bs_entry()

            if latest_bs:
                # date 필드를 datetime으로 변환하여 JSON 직렬화 문제 해결
                bs_data = latest_bs.copy()
                if "date" in bs_data:
                    date_value = bs_data["date"]
                    if isinstance(date_value, str):
                        bs_data["date"] = datetime.fromisoformat(
                            date_value.replace("Z", "+00:00")
                        )
                    elif isinstance(date_value, date):
                        bs_data["date"] = datetime.combine(
                            date_value, datetime.min.time()
                        )
                    else:
                        bs_data["date"] = date_value

                return DatabaseModels.CashManagementSummary(
                    total_cash=latest_bs["cash"]
                    + latest_bs["time_deposit"]
                    + latest_bs["security_cash_balance"],
                    total_cash_balance=latest_bs["cash"],
                    total_time_deposit=latest_bs["time_deposit"],
                    total_security_cash=latest_bs["security_cash_balance"],
                    cash_balances=cash_balances,
                    time_deposits=time_deposits,
                    latest_bs_entry=DatabaseModels.BSTimeseries(**bs_data),
                    updated_at=datetime.now(),
                )
            else:
                return DatabaseModels.CashManagementSummary(
                    total_cash=0,
                    total_cash_balance=0,
                    total_time_deposit=0,
                    total_security_cash=0,
                    cash_balances=[],
                    time_deposits=[],
                    latest_bs_entry=None,
                    updated_at=datetime.now(),
                )

        except Exception as e:
            logger.error(f"현금 관리 요약 조회 오류: {e}")
            raise

    async def get_latest_bs_entry(self) -> Optional[Dict[str, Any]]:
        """가장 최신 bs_timeseries 항목 조회"""
        try:
            return self.cash_repository.get_latest_bs_entry()
        except Exception as e:
            logger.error(f"최신 bs_timeseries 조회 오류: {e}")
            raise

    async def update_current_cash(
        self,
        cash: Optional[int] = None,
        time_deposit: Optional[int] = None,
        security_cash_balance: Optional[int] = None,
        reason: Optional[str] = None,
    ) -> bool:
        """현재 현금 정보 선택적 업데이트 (bs_timeseries)"""
        try:
            today = date.today()

            # 업데이트할 컬럼 결정
            update_fields = {}
            if cash is not None:
                update_fields["cash"] = int(cash)
            if time_deposit is not None:
                update_fields["time_deposit"] = int(time_deposit)
            if security_cash_balance is not None:
                update_fields["security_cash_balance"] = int(security_cash_balance)

            if not update_fields:
                logger.warning("❌ 업데이트할 필드가 없습니다")
                return False

            # 오늘 데이터가 있는지 확인
            existing_bs = self.cash_repository.get_bs_timeseries_by_date(today)

            if existing_bs:
                # 기존 데이터가 있으면 선택적 컬럼만 업데이트
                result = self.cash_repository.update_bs_timeseries(today, update_fields)
                logger.info(f"✅ 기존 데이터 업데이트: {list(update_fields.keys())}")
            else:
                # 새 데이터인 경우, 가장 최신 데이터에서 기존 값 가져오기
                latest_bs = self.cash_repository.get_latest_bs_entry()

                # 기본값 설정
                new_data = {"date": today.isoformat()}

                if latest_bs:
                    latest = latest_bs
                    # 업데이트하지 않을 필드는 최신 데이터에서 가져오기
                    new_data["cash"] = (
                        int(cash) if cash is not None else latest.get("cash", 0)
                    )
                    new_data["time_deposit"] = (
                        int(time_deposit)
                        if time_deposit is not None
                        else latest.get("time_deposit", 0)
                    )
                    new_data["security_cash_balance"] = (
                        int(security_cash_balance)
                        if security_cash_balance is not None
                        else latest.get("security_cash_balance", 0)
                    )
                else:
                    # 이전 데이터가 없는 경우 기본값 사용
                    new_data["cash"] = int(cash) if cash is not None else 0
                    new_data["time_deposit"] = (
                        int(time_deposit) if time_deposit is not None else 0
                    )
                    new_data["security_cash_balance"] = (
                        int(security_cash_balance)
                        if security_cash_balance is not None
                        else 0
                    )

                result = self.cash_repository.create_bs_timeseries(new_data)
                logger.info(
                    f"✅ 새 데이터 생성: cash={new_data['cash']:,}, "
                    f"time_deposit={new_data['time_deposit']:,}, "
                    f"security={new_data['security_cash_balance']:,}"
                )

            if result:
                # 업데이트된 정보 요약
                updated_fields = ", ".join(
                    [f"{k}: {v:,}원" for k, v in update_fields.items()]
                )
                logger.info(
                    f"✅ 현금 정보 업데이트 성공 - {updated_fields} "
                    f"(사유: {reason or '수동 업데이트'})"
                )
                return True
            else:
                logger.error(f"❌ 현금 정보 업데이트 실패")
                return False

        except Exception as e:
            logger.error(f"현금 정보 업데이트 오류: {e}")
            raise
