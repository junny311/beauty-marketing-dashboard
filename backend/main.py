"""FastAPI entrypoint for the Beauty Marketing Dashboard API.

Provides endpoints used by the frontend dashboard and performs CORS setup.
"""

# FastAPI entrypoint
from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from fastapi.middleware.cors import CORSMiddleware

# Caching
from cachetools import cached, TTLCache

from .database import get_db
from .models import Video
from . import schemas

app = FastAPI(title="Beauty Dashboard API")

# 5-minute TTL cache for 128 items
cache = TTLCache(maxsize=128, ttl=300)

# 1. CORS 설정 (React 프론트엔드에서 접속 허용)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 실제 배포시에는 구체적인 도메인으로 제한 권장
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. 엔드포인트: 전체 비디오 목록 조회 (최신순)
@app.get("/videos", response_model=List[schemas.VideoBase])
def read_videos(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    저장된 비디오 목록을 최신순으로 반환합니다.
    """
    videos = db.query(Video).order_by(Video.published_at.desc()).offset(skip).limit(limit).all()
    return videos

# 3. 엔드포인트: 브랜드별 통계 요약 (대시보드 차트용) ⭐ 핵심 기능
@app.get("/dashboard/stats", response_model=List[schemas.BrandStats])
@cached(cache)
def read_dashboard_stats(db: Session = Depends(get_db)):
    """
    브랜드별 총 조회수, 총 좋아요, 평균 참여율 등을 계산해서 반환합니다.
    (SQL의 GROUP BY와 같은 역할)
    - [Cache Applied] 5분 단위로 캐싱됩니다.
    """
    # SQL: SELECT brand, SUM(view_count), ... FROM videos GROUP BY brand
    stats = db.query(
        Video.brand,
        func.sum(Video.view_count).label("total_views"),
        func.sum(Video.like_count).label("total_likes"),
        func.avg(Video.engagement_rate).label("avg_engagement"),
        func.count(Video.video_id).label("video_count")
    ).group_by(Video.brand).all()
    
    return stats

# 서버 상태 확인용
@app.get("/")
def read_root():
    return {"message": "Beauty Marketing Dashboard API is Ready! 🚀"}
