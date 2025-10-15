"""
AssetNest Dashboard 모듈
Streamlit 기반 대시보드 애플리케이션
"""

import os
import sys

# 프로젝트 루트를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from logger import get_dashboard_logger

# 대시보드 모듈 로거
dashboard_module_logger = get_dashboard_logger("Module")
dashboard_module_logger.info("📦 AssetNest Dashboard 모듈 로드됨")

__version__ = "1.0.0"
__author__ = "AssetNest Team"
