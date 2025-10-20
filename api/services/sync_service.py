"""Synchronization service for cross-table data consistency."""

import logging
from datetime import date, datetime
from typing import Dict, Any

from .interfaces import ISyncService
from ..database_modules.repositories import CashRepository

logger = logging.getLogger(__name__)


class SyncService(ISyncService):
    """데이터 동기화 서비스."""

    def __init__(self, cash_repository: CashRepository):
        self.cash_repository = cash_repository

    async def sync_bs_timeseries_from_cash_balances(self) -> None:
        """cash_balance 테이블의 데이터를 기반으로 bs_timeseries 테이블의 security_cash_balance 필드 동기화"""
        try:
            # 1. cash_balance 테이블에서 모든 계좌의 krw 잔액 합계 계산
            cash_balances_data = self.cash_repository.get_cash_balances()

            # 모든 증권사 예수금의 총합 계산
            total_security_cash = sum(
                float(item.get("krw", 0) or 0) for item in cash_balances_data
            )

            logger.info(
                f"💰 cash_balance 테이블 기반 총 증권사 예수금 계산: {total_security_cash:,}원"
            )

            # 2. 오늘 날짜의 bs_timeseries 항목 업데이트
            today = date.today()

            # 오늘 날짜의 기존 항목이 있는지 확인
            existing_bs = self.cash_repository.get_bs_timeseries_by_date(today)

            if existing_bs:
                # 기존 항목 업데이트
                update_result = self.cash_repository.update_bs_timeseries(
                    today, {"security_cash_balance": int(total_security_cash)}
                )

                if update_result:
                    logger.info(
                        f"✅ bs_timeseries 테이블의 security_cash_balance 업데이트 성공: {int(total_security_cash):,}원"
                    )
                else:
                    logger.error(f"❌ bs_timeseries 테이블 업데이트 실패")
            else:
                # 새 항목 생성
                new_bs_data = {
                    "date": today.isoformat(),
                    "security_cash_balance": int(total_security_cash),
                    "cash": 0,  # 기본값
                    "time_deposit": 0,  # 기본값
                }

                create_result = self.cash_repository.create_bs_timeseries(new_bs_data)

                if create_result:
                    logger.info(
                        f"✅ bs_timeseries 테이블에 새 항목 생성 성공: {int(total_security_cash):,}원"
                    )
                else:
                    logger.error(f"❌ bs_timeseries 테이블 신규 항목 생성 실패")

        except Exception as e:
            logger.error(f"bs_timeseries 동기화 중 오류 발생: {e}")
            raise

    async def sync_bs_timeseries_from_time_deposits(self) -> None:
        """time_deposit 테이블의 데이터를 기반으로 bs_timeseries 테이블의 time_deposit 필드 동기화"""
        try:
            # 1. time_deposit 테이블에서 모든 예적금의 market_value 합계 계산
            time_deposits_data = self.cash_repository.get_time_deposits()

            # 모든 예적금의 현재 평가액 합계 계산
            total_time_deposit = sum(
                float(item.get("market_value", 0) or 0) for item in time_deposits_data
            )

            logger.info(
                f"💰 time_deposit 테이블 기반 총 예적금 계산: {total_time_deposit:,}원"
            )

            # 2. 오늘 날짜의 bs_timeseries 항목 업데이트
            today = date.today()

            # 오늘 데이터가 있는지 확인
            existing_response = self.cash_repository.get_bs_timeseries_by_date(today)

            update_data = {"time_deposit": int(total_time_deposit)}

            if existing_response:
                # 기존 데이터가 있으면 time_deposit 필드만 업데이트
                result = self.cash_repository.update_bs_timeseries(today, update_data)
                logger.info(
                    f"✅ bs_timeseries 기존 데이터 동기화 완료: time_deposit={total_time_deposit:,}원"
                )
            else:
                # 오늘 데이터가 없으면 가장 최신 데이터에서 다른 필드 값을 가져와서 새로 생성
                latest_response = self.cash_repository.get_latest_bs_entry()

                new_data = {"date": today.isoformat()}

                if latest_response:
                    latest = latest_response
                    # 기존 필드 값 유지
                    new_data["cash"] = latest.get("cash", 0)
                    new_data["time_deposit"] = int(total_time_deposit)  # 새로 계산된 값
                    new_data["security_cash_balance"] = latest.get(
                        "security_cash_balance", 0
                    )
                else:
                    # 이전 데이터가 없는 경우
                    new_data["cash"] = 0
                    new_data["time_deposit"] = int(total_time_deposit)
                    new_data["security_cash_balance"] = 0

                result = self.cash_repository.create_bs_timeseries(new_data)
                logger.info(
                    f"✅ bs_timeseries 새 데이터 생성 완료: time_deposit={total_time_deposit:,}원"
                )

            if result:
                logger.info(
                    f"🎯 bs_timeseries 동기화 성공: time_deposit={total_time_deposit:,}원"
                )
            else:
                logger.error(f"❌ bs_timeseries 동기화 실패")

        except Exception as e:
            logger.error(f"❌ bs_timeseries 동기화 중 오류 발생: {e}")
            # 동기화 실패하더라도 예적금 수정/생성/삭제는 성공한 것으로 처리 (에러를 다시 발생시키지 않음)

    async def orchestrate_sync_operations(self) -> Dict[str, Any]:
        """모든 동기화 작업 오케스트레이션"""
        try:
            logger.info("🔄 전체 동기화 작업 시작")

            results = {
                "security_cash_sync": {"status": "pending", "amount": 0},
                "time_deposit_sync": {"status": "pending", "amount": 0},
                "timestamp": datetime.now().isoformat(),
            }

            # 1. 증권사 예수금 동기화
            try:
                await self.sync_bs_timeseries_from_cash_balances()
                cash_balances = self.cash_repository.get_cash_balances()
                security_total = sum(
                    float(item.get("krw", 0) or 0) for item in cash_balances
                )
                results["security_cash_sync"] = {
                    "status": "success",
                    "amount": int(security_total),
                }
                logger.info("✅ 증권사 예수금 동기화 완료")
            except Exception as e:
                results["security_cash_sync"] = {
                    "status": "failed",
                    "error": str(e),
                    "amount": 0,
                }
                logger.error(f"❌ 증권사 예수금 동기화 실패: {e}")

            # 2. 예적금 동기화
            try:
                await self.sync_bs_timeseries_from_time_deposits()
                time_deposits = self.cash_repository.get_time_deposits()
                deposit_total = sum(
                    float(item.get("market_value", 0) or 0) for item in time_deposits
                )
                results["time_deposit_sync"] = {
                    "status": "success",
                    "amount": int(deposit_total),
                }
                logger.info("✅ 예적금 동기화 완료")
            except Exception as e:
                results["time_deposit_sync"] = {
                    "status": "failed",
                    "error": str(e),
                    "amount": 0,
                }
                logger.error(f"❌ 예적금 동기화 실패: {e}")

            # 3. 결과 요약
            success_count = sum(
                1
                for result in results.values()
                if isinstance(result, dict) and result.get("status") == "success"
            )
            total_count = 2  # 총 동기화 작업 수

            logger.info(f"🏁 전체 동기화 완료 - 성공: {success_count}/{total_count}")

            results["summary"] = {
                "total_operations": total_count,
                "successful_operations": success_count,
                "failed_operations": total_count - success_count,
                "success_rate": f"{(success_count/total_count)*100:.1f}%",
            }

            return results

        except Exception as e:
            logger.error(f"❌ 동기화 오케스트레이션 전체 오류: {e}")
            return {
                "security_cash_sync": {"status": "failed", "error": str(e)},
                "time_deposit_sync": {"status": "failed", "error": str(e)},
                "summary": {
                    "total_operations": 2,
                    "successful_operations": 0,
                    "failed_operations": 2,
                },
                "timestamp": datetime.now().isoformat(),
            }
