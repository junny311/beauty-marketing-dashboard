"""SQLAlchemy ORM models for the application.

Currently defines the `Video` model which maps to the `videos` table.
"""

from sqlalchemy import Column, Integer, String, Float, BigInteger, DateTime
from sqlalchemy.sql import func
from .database import Base


class Video(Base):
    """ORM model representing a YouTube video record.

    Attributes match the CSV input and are used for analysis and
    aggregation in the dashboard.
    """
    __tablename__ = "videos"

    # 1. 핵심 식별자 (Primary Key)
    video_id = Column(String, primary_key=True, index=True)

    # 2. 브랜드 및 채널 정보
    brand = Column(String, index=True)          # 브랜드명 (검색용 인덱스 추가)
    channel_id = Column(String)                 # 채널 고유 ID
    channel_name = Column(String)               # 채널명
    channel_subscribers = Column(BigInteger)    # 구독자 수 (숫자가 크므로 BigInteger)

    # 3. 영상 기본 정보
    video_title = Column(String)
    duration = Column(String)                   # 영상 길이 (예: PT5M30S)
    tags = Column(String)                       # 태그 목록 (문자열로 저장)
    
    # 4. 통계 및 성과 지표
    view_count = Column(BigInteger)             # 조회수 (21억 넘을 수 있으므로 BigInteger)
    like_count = Column(BigInteger)             # 좋아요 수
    comment_count = Column(Integer)             # 댓글 수
    engagement_rate = Column(Float)             # 엔게이지먼트율 (%)

    # 5. 시간 정보
    published_at = Column(String)               # 원본 게시 일시 (ISO 포맷)
    published_date = Column(String)             # 게시 날짜 (YYYY-MM-DD)
    published_time = Column(String)             # 게시 시간 (HH:MM:SS)
    
    # 6. 데이터베이스 타임스탬프 (자동 관리)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

