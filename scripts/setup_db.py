"""Database initialization script.

Reads the CSV data and populates the `videos` table. Intended for one-time
or development use when setting up the demo database.
"""

import sys
import os
import pandas as pd
from sqlalchemy import text

# 프로젝트 루트 경로 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.append(project_root)

from backend.database import SessionLocal, engine, Base
from backend.models import Video


def init_db():
    """Reset and populate the database from the CSV file.

    Drops all tables and recreates schema then inserts rows from
    `data/raw/youtube_beauty_data.csv`.
    """
    print("🔄 데이터베이스 적재 시작...")

    # 1. 기존 테이블 삭제 후 재생성 (스키마가 바뀌었으므로 필수!)
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    print("✅ 테이블 리셋 완료 (새 스키마 적용)")

    # 2. CSV 파일 읽기
    csv_path = os.path.join(project_root, 'data', 'raw', 'youtube_beauty_data.csv')
    if not os.path.exists(csv_path):
        print(f"❌ 파일이 없습니다: {csv_path}")
        return

    df = pd.read_csv(csv_path)
    # NaN(빈값)을 None으로 변환 (DB 에러 방지)
    df = df.where(pd.notnull(df), None)
    
    print(f"📂 CSV 로드: {len(df)}개 데이터")

    # 3. DB 적재
    db = SessionLocal()
    try:
        count = 0
        for _, row in df.iterrows():
            video = Video(
                video_id=row['video_id'],
                brand=row['brand'],  # brand_name -> brand로 변경됨
                channel_id=row.get('channel_id'),
                channel_name=row.get('channel_name'),
                channel_subscribers=row.get('channel_subscribers'),
                video_title=row['video_title'], # title -> video_title 변경됨
                published_at=row['published_at'],
                view_count=row['view_count'],
                like_count=row['like_count'],
                comment_count=row['comment_count'],
                engagement_rate=row['engagement_rate'],
                duration=row.get('duration'),
                tags=str(row.get('tags')),
                published_date=row.get('published_date'),
                published_time=row.get('published_time')
            )
            db.add(video)
            count += 1
        
        db.commit()
        print(f"🚀 총 {count}개 데이터 DB 적재 완료!")
        
    except Exception as e:
        print(f"❌ 에러 발생: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    init_db()