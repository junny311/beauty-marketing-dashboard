"""Database connection setup.

This module creates a SQLAlchemy engine and session factory using
environment variables (or defaults). The `get_db` generator yields a
session for FastAPI dependency injection.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

# DB 연결 정보 가져오기
DB_USER = os.getenv("DB_USER", "postgres")
# .env에 DB_PASSWORD가 없다면 아래에 직접 비밀번호를 입력하세요!
DB_PASSWORD = os.getenv("DB_PASSWORD", "8289")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "marketing_db")

# URL 생성
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# 1. 엔진 생성
engine = create_engine(DATABASE_URL)

# 2. 세션 생성기
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 3. 모델의 기초 클래스
Base = declarative_base()


def get_db():
    """Yield a database session for FastAPI dependencies.

    Yields:
        sqlalchemy.orm.Session: database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()