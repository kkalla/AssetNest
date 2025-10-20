"""
Supabase 데이터베이스의 모든 테이블 스키마를 조회하여 파일로 저장하는 스크립트
"""

import json
import os
from datetime import datetime

from dotenv import load_dotenv
from supabase import Client, create_client

# .env 파일 로드
load_dotenv()


def get_table_schemas():
    """Supabase 데이터베이스의 모든 테이블 스키마 조회"""

    # Supabase 클라이언트 생성
    supabase_url = os.environ.get("SUPABASE_URL")
    supabase_key = os.environ.get("SUPABASE_KEY")

    if not supabase_url or not supabase_key:
        raise ValueError("SUPABASE_URL과 SUPABASE_KEY 환경변수가 필요합니다")

    supabase: Client = create_client(supabase_url, supabase_key)

    # 모든 테이블 조회 (information_schema 사용)
    try:
        # PostgreSQL information_schema에서 모든 테이블 목록 조회
        tables_response = supabase.rpc("get_all_tables", {}).execute()

        if tables_response.data:
            all_tables = [row["table_name"] for row in tables_response.data]
            print(f"📋 데이터베이스에서 {len(all_tables)}개 테이블 발견")
        else:
            # RPC 함수가 없는 경우, 알려진 테이블 목록으로 대체
            print("⚠️ RPC 함수 사용 불가, 알려진 테이블 목록으로 대체")
            all_tables = [
                "by_accounts",
                "cash_balance",
                "profit_timeseries",
                "currency",
                "symbol_table",
                "funds",
                "time_deposit",
                "bs_timeseries",
            ]
    except Exception as e:
        print(f"⚠️ 테이블 목록 조회 실패: {e}")
        print("ℹ️ 알려진 테이블 목록으로 대체합니다")
        all_tables = [
            "by_accounts",
            "cash_balance",
            "profit_timeseries",
            "currency",
            "symbol_table",
            "funds",
            "time_deposit",
            "bs_timeseries",
        ]

    schema_data = {
        "export_timestamp": datetime.now().isoformat(),
        "database": "supabase",
        "tables": {},
    }

    print("🔍 테이블 스키마 조회 시작...\n")

    # 각 테이블의 스키마 정보 조회
    for table_name in all_tables:
        try:
            print(f"📋 {table_name} 테이블 조회 중...")

            # RPC 함수로 컬럼 타입 정보 조회
            try:
                column_info_response = supabase.rpc(
                    "get_table_schema", {"table_name_param": table_name}
                ).execute()
                column_types = {
                    row["column_name"]: row["data_type"]
                    for row in column_info_response.data
                }
            except Exception as rpc_error:
                print(f"  ⚠️ RPC 함수 사용 불가: {rpc_error}")
                print(f"  ℹ️ 샘플 데이터 기반으로 타입 추론")
                column_types = {}

            # 샘플 데이터 조회
            response = supabase.table(table_name).select("*").limit(10).execute()

            if response.data and len(response.data) > 0:
                # 여러 행에서 NULL이 아닌 값 찾기
                all_columns = {}

                # 모든 컬럼명 수집
                for row in response.data:
                    for col_name in row.keys():
                        if col_name not in all_columns:
                            all_columns[col_name] = {
                                "db_type": column_types.get(col_name, "unknown"),
                                "sample_value": None,
                            }

                # NULL이 아닌 샘플 값 찾기
                for row in response.data:
                    for col_name, value in row.items():
                        if (
                            value is not None
                            and all_columns[col_name]["sample_value"] is None
                        ):
                            all_columns[col_name]["sample_value"] = str(value)[:100]

                schema_data["tables"][table_name] = {
                    "columns": all_columns,
                    "row_count": f"샘플 {len(response.data)}개 행 조회",
                }
                print(f"  ✅ {len(all_columns)}개 컬럼 발견")
            else:
                # 데이터가 없는 경우에도 RPC로 스키마 정보는 가져올 수 있음
                if column_types:
                    columns = {
                        col_name: {
                            "db_type": db_type,
                            "sample_value": None,
                        }
                        for col_name, db_type in column_types.items()
                    }
                    schema_data["tables"][table_name] = {
                        "columns": columns,
                        "row_count": 0,
                    }
                    print(f"  ✅ {len(columns)}개 컬럼 발견 (데이터 없음)")
                else:
                    print(f"  ⚠️ 데이터 및 스키마 정보 없음")
                    schema_data["tables"][table_name] = {
                        "columns": {},
                        "row_count": 0,
                        "note": "데이터가 없어 컬럼 정보를 파악할 수 없음",
                    }

        except Exception as e:
            print(f"  ❌ 오류: {e}")
            schema_data["tables"][table_name] = {"error": str(e)}

    return schema_data


def save_schema_to_file(schema_data, output_format="json"):
    """스키마 데이터를 파일로 저장

    Args:
        schema_data: 스키마 정보 딕셔너리
        output_format: 'json' 또는 'markdown'
    """
    timestamp = datetime.now().strftime("%Y%m%d")

    if output_format == "json":
        # JSON 파일로 저장
        filename = f"database_schema_{timestamp}.json"
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(schema_data, f, ensure_ascii=False, indent=2)
        print(f"\n✅ JSON 파일로 저장: {filename}")

    elif output_format == "markdown":
        # Markdown 파일로 저장
        filename = f"database_schema_{timestamp}.md"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(f"# Database Schema\n\n")
            f.write(f"생성일시: {schema_data['export_timestamp']}\n\n")

            # 테이블 스키마
            f.write(f"## Tables\n\n")
            for table_name, table_info in schema_data["tables"].items():
                f.write(f"### {table_name}\n\n")

                if "error" in table_info:
                    f.write(f"❌ 오류: {table_info['error']}\n\n")
                    continue

                if "note" in table_info:
                    f.write(f"ℹ️ {table_info['note']}\n\n")

                if table_info.get("columns"):
                    f.write("| Column | DB Type | Sample Value |\n")
                    f.write("|--------|---------|-------------|\n")

                    for col_name, col_info in table_info["columns"].items():
                        db_type = col_info.get("db_type", "unknown")
                        sample = col_info.get("sample_value", "N/A")
                        f.write(f"| {col_name} | {db_type} | {sample} |\n")

                    f.write("\n")

        print(f"✅ Markdown 파일로 저장: {filename}")

    return filename


def main():
    """메인 함수"""
    print("=" * 60)
    print("📊 Supabase 데이터베이스 스키마 추출 도구")
    print("=" * 60)
    print()

    try:
        # 스키마 조회
        schema_data = get_table_schemas()

        # JSON과 Markdown 두 가지 형식으로 저장
        json_file = save_schema_to_file(schema_data, "json")
        md_file = save_schema_to_file(schema_data, "markdown")

        print("\n" + "=" * 60)
        print("🎉 스키마 추출 완료!")
        print("=" * 60)

        # 요약 정보 출력
        print(f"\n📋 요약:")
        print(f"  - 테이블: {len(schema_data['tables'])}개")
        print(f"  - 저장 파일: {json_file}, {md_file}")

    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
