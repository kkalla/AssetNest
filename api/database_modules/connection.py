"""Database connection management for AssetNest API."""

import os
from datetime import datetime, date
from decimal import Decimal
from typing import Any, Dict

from dotenv import load_dotenv
from supabase import Client, create_client

load_dotenv()


class SerializableClient(Client):
    """JSON 직렬화 문제를 해결한 Supabase 클라이언트 래퍼."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def _serialize_data(self, data: Any) -> Any:
        """데이터를 JSON 직렬화 가능한 형태로 변환"""
        if isinstance(data, dict):
            return {k: self._serialize_data(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._serialize_data(item) for item in data]
        elif isinstance(data, (datetime, date)):
            return data.isoformat()
        else:
            return data

    def table(self, table_name: str): # type: ignore
        """테이블 작업을 직렬화와 함께 처리"""
        original_table = super().table(table_name)

        class SerializableTable:
            def __init__(self, table, serializer):
                self._table = table
                self._serialize = serializer

            def insert(self, data, *args, **kwargs):
                serialized_data = self._serialize(data)
                return self._table.insert(serialized_data, *args, **kwargs)

            def update(self, data, *args, **kwargs):
                serialized_data = self._serialize(data)
                return self._table.update(serialized_data, *args, **kwargs)

            def select(self, *args, **kwargs):
                return self._table.select(*args, **kwargs)

            def delete(self, *args, **kwargs):
                return self._table.delete(*args, **kwargs)

            def __getattr__(self, name):
                return getattr(self._table, name)

        return SerializableTable(original_table, self._serialize_data)


class DatabaseConnection:
    """데이터베이스 연결 관리 클래스."""

    def __init__(self):
        self.supabase_url = os.environ.get("SUPABASE_URL")
        self.supabase_key = os.environ.get("SUPABASE_KEY")

        if not self.supabase_url or not self.supabase_key:
            raise ValueError("SUPABASE_URL과 SUPABASE_KEY 환경변수가 필요합니다")

        # JSON 직렬화 문제를 해결하기 위해 커스텀 클라이언트 사용
        self.supabase: SerializableClient = SerializableClient(
            self.supabase_url, self.supabase_key
        )

    def get_client(self) -> SerializableClient:
        """Supabase 클라이언트 인스턴스 반환"""
        return self.supabase

    def health_check(self) -> Dict[str, Any]:
        """데이터베이스 연결 상태 확인"""
        try:
            # 간단한 쿼리로 연결 상태 확인
            response = (
                self.supabase.table("currency").select("count").limit(1).execute()
            )
            return {
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "connection": "supabase",
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "timestamp": datetime.now().isoformat(),
                "error": str(e),
                "connection": "supabase",
            }
