"""
AssetNest 공통 로깅 시스템
API와 Dashboard에서 공통으로 사용하는 로깅 설정
"""

import logging
import os
import sys
from datetime import datetime
from pathlib import Path


def setup_logger(
    name: str = "AssetNest", level: str = "INFO", log_type: str = "app"
) -> logging.Logger:
    """
    로거 설정

    Args:
        name: 로거 이름
        level: 로깅 레벨 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_type: 로그 타입 ("api", "dashboard", "app")

    Returns:
        설정된 로거 객체
    """

    # 로그 레벨 설정
    log_level = getattr(logging, level.upper(), logging.INFO)

    # 로거 생성
    logger = logging.getLogger(name)
    logger.setLevel(log_level)

    # 이미 핸들러가 있으면 제거 (중복 방지)
    if logger.handlers:
        logger.handlers.clear()

    # 포매터 설정
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # 콘솔 핸들러 설정
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)

    # 파일 핸들러 설정 (logs 디렉토리에 저장)
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)

    # 타입별 로그 파일
    log_file = logs_dir / f"{log_type}_{datetime.now().strftime('%Y%m%d')}.log"
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)

    # 에러 전용 로그 파일
    error_log_file = logs_dir / f"error_{datetime.now().strftime('%Y%m%d')}.log"
    error_handler = logging.FileHandler(error_log_file, encoding="utf-8")
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)

    # 핸들러 추가
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    logger.addHandler(error_handler)

    # 상위 로거로 전파하지 않음
    logger.propagate = False

    return logger


def get_logger(name: str = "AssetNest", log_type: str = "app") -> logging.Logger:
    """
    이미 설정된 로거를 반환하거나 새로 생성

    Args:
        name: 로거 이름
        log_type: 로그 타입 ("api", "dashboard", "app")

    Returns:
        로거 객체
    """
    logger = logging.getLogger(name)

    # 핸들러가 없으면 새로 설정
    if not logger.handlers:
        # 환경변수에서 로그 레벨 가져오기 (기본값: INFO)
        log_level = os.getenv("LOG_LEVEL", "INFO")
        logger = setup_logger(name, log_level, log_type)

    return logger


def get_api_logger(component: str = "API") -> logging.Logger:
    """API용 로거 반환"""
    return get_logger(f"AssetNest.{component}", "api")


def get_dashboard_logger(component: str = "Dashboard") -> logging.Logger:
    """Dashboard용 로거 반환"""
    return get_logger(f"AssetNest.{component}", "dashboard")


# 기본 로거 인스턴스들
api_logger = get_api_logger("API")
db_logger = get_api_logger("Database")
dashboard_logger = get_dashboard_logger("Dashboard")
ui_logger = get_dashboard_logger("UI")
data_logger = get_dashboard_logger("Data")
