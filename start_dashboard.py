#!/usr/bin/env python3
"""
AssetNest Streamlit 대쉬보드 실행 스크립트
"""

import os
import subprocess
import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

if __name__ == "__main__":
    dashboard_file = project_root / "dashboard" / "main.py"

    print("📊 AssetNest 대쉬보드를 시작합니다...")
    print("🌐 대쉬보드: http://localhost:8501")
    print("🔧 종료하려면 Ctrl+C를 누르세요")

    # Streamlit 실행
    subprocess.run(
        [
            sys.executable,
            "-m",
            "streamlit",
            "run",
            str(dashboard_file),
            "--server.port",
            "8501",
            "--server.address",
            "localhost",
            "--theme.base",
            "light",
        ]
    )
