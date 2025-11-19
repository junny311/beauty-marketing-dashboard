"""Pydantic schemas for request/response models used by FastAPI.

Defines the shapes returned by the `/videos` and `/dashboard/stats`
endpoints.
"""

from pydantic import BaseModel
from typing import Optional


# 1. 비디오 데이터 기본 구조 (DB Models와 매칭)
class VideoBase(BaseModel):
    """Base schema for video records returned by the API.

    Fields correspond to the `Video` ORM model attributes.
    """
    video_id: str
    brand: str
    video_title: str
    published_at: str
    view_count: int
    like_count: int
    comment_count: int
    engagement_rate: float
    channel_id: Optional[str] = None
    channel_subscribers: Optional[int] = None
    
    class Config:
        from_attributes = True # ORM 모드 활성화


# 2. 대시보드 차트용 요약 데이터 구조
class BrandStats(BaseModel):
    """Schema for brand-level aggregated statistics used in charts."""
    brand: str
    total_views: int
    total_likes: int
    avg_engagement: float
    video_count: int