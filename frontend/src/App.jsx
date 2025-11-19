import React, { useState, useEffect } from 'react'; // React를 명시적으로 임포트합니다.
import axios from 'axios';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

// 1. FastAPI 서버 주소
const API_URL = 'http://127.0.0.1:8000/dashboard/stats';

const App = () => {
    // 2. 데이터를 담을 상태(State)
    const [stats, setStats] = useState([]);
    const [kpis, setKpis] = useState({ totalSubscribers: 0, totalViews: 0, totalVideos: 0, overallAvgEngagement: 0 });
    const [videos, setVideos] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    // 3. 컴포넌트가 로드될 때 API 데이터를 가져오는 함수 (useEffect)
    useEffect(() => {
        const fetchData = async () => {
            try {
                // 브랜드 통계와 전체 비디오 목록을 병렬로 요청합니다.
                const videosUrl = 'http://127.0.0.1:8000/videos?skip=0&limit=10000';
                const [statsRes, videosRes] = await Promise.all([
                    axios.get(API_URL),
                    axios.get(videosUrl),
                ]);

                const statsData = statsRes.data || [];
                const videosData = videosRes.data || [];

                setStats(statsData);
                setVideos(videosData);

                // KPI 계산
                const totalViews = statsData.reduce((sum, b) => sum + (Number(b.total_views) || 0), 0);
                const totalVideos = statsData.reduce((sum, b) => sum + (Number(b.video_count) || 0), 0);
                const weightedEngagement = statsData.reduce((sum, b) => sum + (Number(b.avg_engagement) || 0) * (Number(b.video_count) || 0), 0);
                const overallAvgEngagement = totalVideos ? (weightedEngagement / totalVideos) : 0;

                // 채널별 중복 제거 후 구독자 합계 계산 (channel_id 기준, 최신/최댓값 사용)
                let totalSubscribers = 0;
                if (videosData.length > 0 && videosData[0].channel_subscribers !== undefined) {
                    const channelMap = {};
                    for (const v of videosData) {
                        if (!v || !v.channel_id) continue;
                        // 문자열로 되어있을 수도 있으니 숫자로 변환
                        const subs = Number(String(v.channel_subscribers).replace(/[^0-9.-]+/g, '')) || 0;
                        if (!channelMap[v.channel_id]) channelMap[v.channel_id] = subs;
                        else channelMap[v.channel_id] = Math.max(channelMap[v.channel_id], subs);
                    }
                    totalSubscribers = Object.values(channelMap).reduce((s, n) => s + n, 0);
                } else {
                    // /videos 응답에 구독자 정보가 없으면 0으로 둡니다. (백엔드에서 필드 포함 필요)
                    totalSubscribers = 0;
                }

                setKpis({ totalSubscribers, totalViews, totalVideos, overallAvgEngagement });

            } catch (err) {
                setError('API 데이터를 불러오는 데 실패했습니다.');
                console.error('API Fetch Error:', err);
            } finally {
                setLoading(false);
            }
        };

        fetchData();
    }, []); // 배열이 비어있으므로 컴포넌트 마운트 시 1회만 실행

    if (loading) return <div className="text-2xl p-8">데이터 로드 중...</div>;
    if (error) return <div className="text-red-500 p-8">오류: {error}</div>;

    // helper 포맷터
    const fmt = (n) => (typeof n === 'number' ? n.toLocaleString() : n);
    const fmtPct = (v) => {
        const num = Number(v);
        if (Number.isNaN(num)) return '-';
        // 값이 큰 경우(>10)에는 이미 퍼센트(예: 1.7 => 1.7%)일 수 있음
        if (Math.abs(num) > 10) return `${num.toFixed(2)}%`;
        // 그렇지 않으면 소수(예: 0.02)로 들어온 상태로 간주하여 100 곱함
        if (Math.abs(num) <= 10 && Math.abs(num) > 0) return `${(num * 100).toFixed(2)}%`;
        return `${(num * 100).toFixed(2)}%`;
    };

    // 4. 데이터 시각화 (브랜드별 평균 참여율 차트) + KPI 카드
    return (
        <div className="p-8 bg-gray-50 min-h-screen">
            <h1 className="text-3xl font-bold text-gray-800 mb-6">뷰티 브랜드별 성과 요약 (Dashboard)</h1>

            {/* KPI 카드 */}
            <div style={{ display: 'flex', gap: '1rem', marginBottom: '1rem', flexWrap: 'wrap' }}>
                <div className="bg-white p-4 rounded-lg shadow-md" style={{ flex: 1, minWidth: 200 }}>
                    <div className="text-sm text-gray-500">총 구독자 수</div>
                    <div className="text-2xl font-bold">{fmt(kpis.totalSubscribers)}</div>
                </div>

                <div className="bg-white p-4 rounded-lg shadow-md" style={{ flex: 1, minWidth: 200 }}>
                    <div className="text-sm text-gray-500">총 영상 수</div>
                    <div className="text-2xl font-bold">{fmt(kpis.totalVideos)}</div>
                </div>

                <div className="bg-white p-4 rounded-lg shadow-md" style={{ flex: 1, minWidth: 200 }}>
                    <div className="text-sm text-gray-500">총 조회수</div>
                    <div className="text-2xl font-bold">{fmt(kpis.totalViews)}</div>
                </div>

                <div className="bg-white p-4 rounded-lg shadow-md" style={{ flex: 1, minWidth: 200 }}>
                    <div className="text-sm text-gray-500">전체 평균 참여율</div>
                    <div className="text-2xl font-bold">{fmtPct(kpis.overallAvgEngagement)}</div>
                </div>
            </div>

            <div className="bg-white p-6 rounded-lg shadow-md" style={{ marginBottom: '1rem' }}>
                <h2 className="text-xl font-semibold mb-4 text-gray-700">브랜드별 평균 참여율 (Average Engagement Rate)</h2>
                <ResponsiveContainer width="100%" height={350}>
                    <BarChart data={stats} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                        <XAxis dataKey="brand" stroke="#333" />
                        <YAxis yAxisId="left" orientation="left" stroke="#8884d8" label={{ value: '평균 참여율 (%)', angle: -90, position: 'insideLeft' }} />
                        <Tooltip />
                        <Legend wrapperStyle={{ paddingTop: '10px' }} />
                        <Bar yAxisId="left" dataKey="avg_engagement" fill="#FF83A0" name="평균 참여율 (%)" barSize={50} />
                    </BarChart>
                </ResponsiveContainer>
            </div>

            {/* 브랜드별 총 영상 수 비교 차트 */}
            <div className="bg-white p-6 rounded-lg shadow-md" style={{ marginBottom: '1rem' }}>
                <h2 className="text-xl font-semibold mb-4 text-gray-700">브랜드별 총 영상 수</h2>
                <ResponsiveContainer width="100%" height={300}>
                    <BarChart data={stats} margin={{ top: 10, right: 20, left: 20, bottom: 5 }}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                        <XAxis dataKey="brand" />
                        <YAxis />
                        <Tooltip />
                        <Bar dataKey="video_count" fill="#4F46E5" name="영상수" />
                    </BarChart>
                </ResponsiveContainer>
            </div>

            {/* Top 5 영상 (조회수 기준) */}
            <div className="bg-white p-6 rounded-lg shadow-md" style={{ marginBottom: '1rem' }}>
                <h2 className="text-xl font-semibold mb-4 text-gray-700">Top 5 영상 (조회수 기준)</h2>
                <div style={{ overflowX: 'auto' }}>
                    <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                        <thead>
                            <tr style={{ textAlign: 'left', borderBottom: '1px solid #e5e7eb' }}>
                                <th style={{ padding: '8px' }}>순위</th>
                                <th style={{ padding: '8px' }}>브랜드</th>
                                <th style={{ padding: '8px' }}>채널</th>
                                <th style={{ padding: '8px' }}>영상 제목</th>
                                <th style={{ padding: '8px' }}>조회수</th>
                            </tr>
                        </thead>
                        <tbody>
                            {videos
                                .slice()
                                .sort((a, b) => (Number(b.view_count) || 0) - (Number(a.view_count) || 0))
                                .slice(0, 5)
                                .map((v, i) => (
                                    <tr key={v.video_id} style={{ borderBottom: '1px solid #f3f4f6' }}>
                                        <td style={{ padding: '8px' }}>{i + 1}</td>
                                        <td style={{ padding: '8px' }}>{v.brand}</td>
                                        <td style={{ padding: '8px' }}>{v.channel_name || v.channel_id || '-'}</td>
                                        <td style={{ padding: '8px' }}>{v.video_title}</td>
                                        <td style={{ padding: '8px' }}>{fmt(Number(v.view_count) || 0)}</td>
                                    </tr>
                                ))}
                        </tbody>
                    </table>
                </div>
            </div>

            {/* (원본 데이터 테이블 제거됨) */}

        </div>
    );
};

export default App;
