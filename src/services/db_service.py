import duckdb
from src.config import Config

# =========================================================
# 2. Service Layer - Database
# 데이터베이스 연결 및 쿼리 실행을 담당합니다.
# =========================================================

class DBService:
    """
    DuckDB와의 연결 및 쿼리 실행을 전담하는 클래스입니다.
    Context Manager를 사용하여 연결 누수를 방지합니다.
    """
    @staticmethod
    def query(sql, params=None):
        """
        SQL 조회 쿼리(SELECT)를 실행하고 결과를 DataFrame으로 반환합니다.
        """
        try:
            with duckdb.connect(Config.DB_NAME) as conn:
                return conn.execute(sql, params).df() if params else conn.execute(sql).df()
        except Exception as e:
            print(f"DB Query Error: {e}")
            raise e

    @staticmethod
    def execute(sql, params=None):
        """
        SQL 조작 쿼리(INSERT, UPDATE, DELETE)를 실행합니다.
        """
        try:
            with duckdb.connect(Config.DB_NAME) as conn:
                if params:
                    conn.execute(sql, params)
                else:
                    conn.execute(sql)
                return None
        except Exception as e:
            print(f"DB Execute Error: {e}")
            raise e
