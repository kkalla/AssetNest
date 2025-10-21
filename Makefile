# AssetNest - 효율적인 자산관리 대쉬보드 앱
# 로컬 개발 환경을 위한 Makefile

.PHONY: help install api dashboard update-data dev logs clean test lint

# 기본 타겟
help:
	@echo "🚀 AssetNest 개발 환경 명령어"
	@echo ""
	@echo "📦 설치 및 설정:"
	@echo "  make install     - 의존성 패키지 설치"
	@echo "  make env         - 환경변수 파일(.env) 생성 가이드"
	@echo ""
	@echo "🔧 서버 실행:"
	@echo "  make api         - FastAPI 서버 시작 (포트 8000)"
	@echo "  make dashboard   - Streamlit 대쉬보드 시작 (포트 8501)"
	@echo "  make dev         - API와 대쉬보드 동시 실행"
	@echo ""
	@echo "📊 데이터 관리:"
	@echo "  make update      - 주식 가격 정보 업데이트"
	@echo "  make excel       - 포트폴리오 엑셀로 내보내기"
	@echo ""
	@echo "🧪 개발 도구:"
	@echo "  make logs        - 서버 로그 확인"
	@echo "  make clean       - 임시파일 및 캐시 정리"
	@echo "  make lint        - 코드 스타일 검사"
	@echo ""

# 패키지 설치
install:
	@echo "📦 패키지 설치 중..."
	pip install -r requirements.txt
	@echo "✅ 설치 완료!"

# 환경변수 설정 가이드
env:
	@echo "🔐 환경변수 설정이 필요합니다."
	@echo "프로젝트 루트에 .env 파일을 생성하고 다음 내용을 추가하세요:"
	@echo ""
	@echo "SUPABASE_URL=your_supabase_url"
	@echo "SUPABASE_SERVICE_ROLE_KEY=your_service_role_key"
	@echo "ALPHA_VANTAGE_API_KEY=your_alpha_vantage_key"
	@echo ""
	@if [ ! -f .env ]; then \
		echo "# AssetNest 환경변수" > .env; \
		echo "SUPABASE_URL=" >> .env; \
		echo "SUPABASE_SERVICE_ROLE_KEY=" >> .env; \
		echo "ALPHA_VANTAGE_API_KEY=" >> .env; \
		echo "📝 .env 파일 템플릿이 생성되었습니다. 값을 입력해주세요."; \
	else \
		echo "✅ .env 파일이 이미 존재합니다."; \
	fi

# FastAPI 서버 시작
api:
	@echo "🚀 FastAPI 서버를 시작합니다..."
	@echo "📊 API 문서: http://localhost:8000/docs"
	python start_api.py

# Streamlit 대쉬보드 시작
dashboard:
	@echo "📊 Streamlit 대쉬보드를 시작합니다..."
	@echo "🌐 대쉬보드: http://localhost:8501"
	@echo "🏗️  새로운 모듈식 아키텍처로 실행됩니다"
	python start_dashboard.py

# API와 대쉬보드 동시 실행 (백그라운드)
dev:
	@echo "🔧 개발 환경을 시작합니다..."
	@echo "🚀 API 서버: http://localhost:8000/docs"
	@echo "📊 대쉬보드: http://localhost:8501"
	@echo "🛑 종료하려면: make stop 또는 Ctrl+C"
	@echo ""
	python start_api.py & \
	sleep 3 && \
	python start_dashboard.py

# 백그라운드 프로세스 종료
stop:
	@echo "🛑 AssetNest 프로세스를 종료합니다..."
	@pkill -f "start_api.py" || true
	@pkill -f "start_dashboard.py" || true
	@pkill -f "uvicorn" || true
	@pkill -f "streamlit" || true
	@echo "✅ 프로세스가 종료되었습니다."

# 주식 데이터 업데이트
update:
	@echo "📈 주식 가격 정보를 업데이트합니다..."
	python update_stock_info.py
	@echo "✅ 업데이트 완료!"

# 엑셀 내보내기
excel:
	@echo "📋 포트폴리오를 엑셀로 내보냅니다..."
	python write_excel.py
	@echo "✅ 엑셀 파일이 생성되었습니다!"

# 로그 확인
logs:
	@echo "📋 최근 로그를 확인합니다..."
	@if command -v tail >/dev/null 2>&1; then \
		echo "API 서버 로그:"; \
		ps aux | grep "start_api.py" | grep -v grep || echo "API 서버가 실행중이지 않습니다."; \
		echo ""; \
		echo "대쉬보드 로그:"; \
		ps aux | grep "start_dashboard.py" | grep -v grep || echo "대쉬보드가 실행중이지 않습니다."; \
	else \
		echo "로그 확인 도구를 찾을 수 없습니다."; \
	fi

# 정리 작업
clean:
	@echo "🧹 임시 파일과 캐시를 정리합니다..."
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name ".DS_Store" -delete 2>/dev/null || true
	@echo "✅ 정리 완료!"

# 코드 스타일 검사 (선택사항)
lint:
	@echo "🔍 코드 스타일을 검사합니다..."
	@if command -v flake8 >/dev/null 2>&1; then \
		flake8 api/ dashboard/ --max-line-length=88 --ignore=E203,W503; \
	else \
		echo "⚠️  flake8이 설치되어 있지 않습니다. 'pip install flake8'으로 설치하세요."; \
	fi

# 테스트 실행 (선택사항)
test:
	@echo "🧪 테스트를 실행합니다..."
	@if command -v pytest >/dev/null 2>&1; then \
		pytest tests/ -v || echo "테스트 폴더가 없거나 테스트가 없습니다."; \
	else \
		echo "⚠️  pytest가 설치되어 있지 않습니다. 'pip install pytest'로 설치하세요."; \
	fi

# 상태 확인
status:
	@echo "📊 AssetNest 상태를 확인합니다..."
	@echo ""
	@echo "🔧 실행 중인 프로세스:"
	@ps aux | grep -E "(start_api|start_dashboard|uvicorn|streamlit)" | grep -v grep || echo "실행중인 AssetNest 프로세스가 없습니다."
	@echo ""
	@echo "🌐 포트 상태:"
	@lsof -i :8000 2>/dev/null | head -2 || echo "포트 8000: 사용 안함"
	@lsof -i :8501 2>/dev/null | head -2 || echo "포트 8501: 사용 안함"
	@echo ""
	@echo "📁 환경 파일:"
	@if [ -f .env ]; then echo "✅ .env 파일 존재"; else echo "❌ .env 파일 없음 (make env 실행 필요)"; fi