#!/usr/bin/env python3
"""
AssetNest FastAPI 서버 실행 스크립트
"""

import os
import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

if __name__ == "__main__":
    import uvicorn

    from api.main import app

    print("🚀 AssetNest API 서버를 시작합니다...")
    print("📊 API 문서: http://localhost:8000/docs")
    print("🔧 종료하려면 Ctrl+C를 누르세요")

    uvicorn.run(
        "api.main:app",  # import string 형태로 전달
        host="0.0.0.0",
        port=8000,
        reload=True,  # 개발 중에만 사용
        log_level="info",
    )
