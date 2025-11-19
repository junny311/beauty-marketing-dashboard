# YouTube crawler script

"""
YouTube 뷰티 브랜드 채널 데이터 수집기
- 채널 정보, 최근 영상, 조회수, 좋아요, 댓글 수 등 수집
"""

import os
import json
import pandas as pd
from datetime import datetime, timedelta
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from dotenv import load_dotenv

# 재시도 라이브러리
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

# 환경변수 로드
load_dotenv()

class YouTubeBeautyCrawler:
    def __init__(self, api_key):
        self.api_key = api_key
        self.youtube = build('youtube', 'v3', developerKey=api_key)
        
        # 국내 주요 뷰티 브랜드 채널 (실제 채널 ID로 교체 필요)
        self.target_brands = {
            '3CE': '@3CE_Official',           
            'ETUDE': '@etudeofficial',           
            'CLIO': '@clio_official',
        }
    
    @retry(
        retry=retry_if_exception_type(HttpError),
        wait=wait_exponential(multiplier=1, min=2, max=10), 
        stop=stop_after_attempt(3)
    )
    def search_channel_id(self, channel_username):
        """채널 사용자명으로 채널 ID 검색"""
        print(f"-> channel_id 검색: {channel_username}")
        # @ 제거
        username = channel_username.replace('@', '')
        
        # 채널 검색
        request = self.youtube.search().list(
            part='snippet',
            q=username,
            type='channel',
            maxResults=1
        )
        response = request.execute()
        
        if response['items']:
            channel_id = response['items'][0]['snippet']['channelId']
            print(f"✓ 채널 ID 찾음: {username} -> {channel_id}")
            return channel_id
        else:
            print(f"✗ 채널을 찾을 수 없음: {username}")
            return None
    
    @retry(
        retry=retry_if_exception_type(HttpError),
        wait=wait_exponential(multiplier=1, min=2, max=10), 
        stop=stop_after_attempt(3)
    )
    def get_channel_stats(self, channel_id):
        """채널 통계 정보 수집"""
        print(f"-> channel_stats 수집: {channel_id}")
        request = self.youtube.channels().list(
            part='statistics,snippet',
            id=channel_id
        )
        response = request.execute()
        
        if response['items']:
            item = response['items'][0]
            stats = item['statistics']
            snippet = item['snippet']
            
            return {
                'channel_id': channel_id,
                'channel_name': snippet['title'],
                'subscribers': int(stats.get('subscriberCount', 0)),
                'total_views': int(stats.get('viewCount', 0)),
                'video_count': int(stats.get('videoCount', 0)),
                'description': snippet.get('description', ''),
                'published_at': snippet.get('publishedAt', '')
            }
        return None
    
    @retry(
        retry=retry_if_exception_type(HttpError),
        wait=wait_exponential(multiplier=1, min=2, max=10), 
        stop=stop_after_attempt(3)
    )
    def get_recent_videos(self, channel_id, max_results=50):
        """최근 영상 목록 수집 (최근 1년)"""
        print(f"-> recent_videos 수집: {channel_id}")
        # 1년 전 날짜
        date_1_year_ago = (datetime.now() - timedelta(days=365)).isoformat() + 'Z'
        
        request = self.youtube.search().list(
            part='snippet',
            channelId=channel_id,
            type='video',
            order='date',
            maxResults=max_results,
            publishedAfter=date_1_year_ago
        )
        response = request.execute()
        
        videos = []
        for item in response['items']:
            videos.append({
                'video_id': item['id']['videoId'],
                'title': item['snippet']['title'],
                'published_at': item['snippet']['publishedAt'],
                'description': item['snippet']['description']
            })
        
        return videos
            
    @retry(
        retry=retry_if_exception_type(HttpError),
        wait=wait_exponential(multiplier=1, min=2, max=10), 
        stop=stop_after_attempt(3)
    )
    def get_video_stats(self, video_ids):
        """영상 상세 통계 수집"""
        print(f"-> video_stats 수집 (영상 {len(video_ids)}개)")
        # 최대 50개씩 요청 가능
        video_ids_str = ','.join(video_ids[:50])
        
        request = self.youtube.videos().list(
            part='statistics,snippet,contentDetails',
            id=video_ids_str
        )
        response = request.execute()
        
        videos_stats = []
        for item in response['items']:
            stats = item['statistics']
            snippet = item['snippet']
            
            videos_stats.append({
                'video_id': item['id'],
                'title': snippet['title'],
                'published_at': snippet['publishedAt'],
                'view_count': int(stats.get('viewCount', 0)),
                'like_count': int(stats.get('likeCount', 0)),
                'comment_count': int(stats.get('commentCount', 0)),
                'duration': item['contentDetails']['duration'],
                'tags': snippet.get('tags', []),
                'category_id': snippet.get('categoryId', '')
            })
        
        return videos_stats
            
    def calculate_engagement_rate(self, video_stats):
        """엔게이지먼트율 계산"""
        if video_stats['view_count'] > 0:
            engagement = (video_stats['like_count'] + video_stats['comment_count']) / video_stats['view_count'] * 100
            return round(engagement, 2)
        return 0
    
    def crawl_all_brands(self):
        """모든 브랜드 데이터 수집"""
        all_data = []
        
        print("=" * 60)
        print("🎨 뷰티 브랜드 유튜브 데이터 수집 시작")
        print("=" * 60)
        
        for brand_name, channel_username in self.target_brands.items():
            print(f"\n📺 [{brand_name}] 수집 중...")
            
            try:
                # 1. 채널 ID 찾기
                channel_id = self.search_channel_id(channel_username)
                if not channel_id:
                    print(f"⚠️ {brand_name} 채널 ID를 찾을 수 없습니다. 건너뜁니다.")
                    continue
                
                # 2. 채널 통계
                channel_stats = self.get_channel_stats(channel_id)
                if not channel_stats:
                    continue
                
                print(f"   구독자: {channel_stats['subscribers']:,}명")
                print(f"   총 영상: {channel_stats['video_count']}개")
                
                # 3. 최근 영상 목록
                recent_videos = self.get_recent_videos(channel_id)
                print(f"   최근 1년 영상: {len(recent_videos)}개")
                
                if not recent_videos:
                    continue
                
                # 4. 영상 상세 통계
                video_ids = [v['video_id'] for v in recent_videos]
                videos_stats = self.get_video_stats(video_ids)
                
                # 5. 데이터 결합
                for video in videos_stats:
                    data = {
                        'brand': brand_name,
                        'channel_id': channel_id,
                        'channel_name': channel_stats['channel_name'],
                        'channel_subscribers': channel_stats['subscribers'],
                        'video_id': video['video_id'],
                        'video_title': video['title'],
                        'published_at': video['published_at'],
                        'view_count': video['view_count'],
                        'like_count': video['like_count'],
                        'comment_count': video['comment_count'],
                        'engagement_rate': self.calculate_engagement_rate(video),
                        'duration': video['duration'],
                        'tags': ','.join(video['tags']) if video['tags'] else '',
                    }
                    all_data.append(data)
                
                print(f"   ✓ {len(videos_stats)}개 영상 데이터 수집 완료")

            except HttpError as e:
                print(f"✗ [{brand_name}] 처리 중 API 에러 발생 (최종 재시도 실패): {e}")
                continue
            except Exception as e:
                print(f"✗ [{brand_name}] 처리 중 알 수 없는 에러 발생: {e}")
                continue
        
        return all_data
    
    def save_to_csv(self, data, filename='youtube_beauty_data.csv'):
        """데이터를 CSV로 저장"""
        df = pd.DataFrame(data)
        
        # 날짜 파싱
        df['published_date'] = pd.to_datetime(df['published_at']).dt.date
        df['published_time'] = pd.to_datetime(df['published_at']).dt.time
        
        # 저장
        filepath = f'data/raw/{filename}'
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        df.to_csv(filepath, index=False, encoding='utf-8-sig')
        
        print(f"\n💾 데이터 저장 완료: {filepath}")
        print(f"   총 {len(df)}개 행")
        print(f"   브랜드 수: {df['brand'].nunique()}개")
        
        return df
    
    def print_summary(self, df):
        """수집 결과 요약"""
        print("\n" + "=" * 60)
        print("📊 데이터 수집 요약")
        print("=" * 60)
        
        summary = df.groupby('brand').agg({
            'video_id': 'count',
            'view_count': 'sum',
            'like_count': 'sum',
            'comment_count': 'sum',
            'engagement_rate': 'mean',
            'channel_subscribers': 'first'
        }).round(2)
        
        summary.columns = ['영상수', '총조회수', '총좋아요', '총댓글', '평균엔게이지먼트율(%)', '구독자수']
        
        print(summary.to_string())
        print("\n✅ 수집 완료!")


def main():
    # API 키 확인
    api_key = os.getenv('YOUTUBE_API_KEY')
    
    if not api_key:
        print("❌ 오류: YOUTUBE_API_KEY 환경변수를 찾을 수 없습니다.")
        print("   .env 파일에 YOUTUBE_API_KEY=your_api_key 를 추가하세요.")
        return
    
    # 크롤러 실행
    crawler = YouTubeBeautyCrawler(api_key)
    
    # 데이터 수집
    data = crawler.crawl_all_brands()
    
    if data:
        # CSV 저장
        df = crawler.save_to_csv(data)
        
        # 결과 요약
        crawler.print_summary(df)
    else:
        print("❌ 수집된 데이터가 없습니다.")


if __name__ == "__main__":
    main()