import { useState } from 'react'
import PageContainer from '../../components/common/PageContainer'

function AnalyticsPage() {
  const [selectedPlatform, setSelectedPlatform] = useState('all')
  const [timeRange, setTimeRange] = useState('7days')

  const platforms = [
    { id: 'all', name: '全部平台', icon: '📊' },
    { id: 'douyin', name: '抖音', icon: '🎵' },
    { id: 'kuaishou', name: '快手', icon: '🎬' },
    { id: 'shipinhao', name: '视频号', icon: '💚' },
    { id: 'bilibili', name: 'B站', icon: '📺' },
    { id: 'xiaohongshu', name: '小红书', icon: '📖' },
  ]

  const timeRanges = [
    { id: '7days', name: '近7天' },
    { id: '30days', name: '近30天' },
    { id: '90days', name: '近90天' },
  ]

  const mockData = {
    overview: {
      totalViews: '1,256,789',
      viewsChange: '+23.5%',
      totalLikes: '89,456',
      likesChange: '+18.2%',
      totalComments: '12,345',
      commentsChange: '+31.7%',
      totalShares: '5,678',
      sharesChange: '+15.4%',
      newFollowers: '3,456',
      followersChange: '+28.9%',
    },
    topVideos: [
      { id: 1, title: '这3个技巧让你效率翻倍', views: '156,789', likes: '12,345', comments: '1,234', platform: 'douyin', date: '2026-03-10' },
      { id: 2, title: '普通人如何做副业', views: '134,567', likes: '9,876', comments: '987', platform: 'kuaishou', date: '2026-03-08' },
      { id: 3, title: '揭秘爆款视频的秘密', views: '98,765', likes: '7,654', comments: '765', platform: 'shipinhao', date: '2026-03-05' },
      { id: 4, title: '我用AI工具提高了10倍效率', views: '87,654', likes: '6,543', comments: '543', platform: 'bilibili', date: '2026-03-03' },
      { id: 5, title: '新手必看的5个避坑指南', views: '76,543', likes: '5,432', comments: '432', platform: 'xiaohongshu', date: '2026-03-01' },
    ],
    platformStats: [
      { id: 'douyin', name: '抖音', icon: '🎵', views: '567,890', followers: '123,456', engagement: '8.2%' },
      { id: 'kuaishou', name: '快手', icon: '🎬', views: '345,678', followers: '87,654', engagement: '7.8%' },
      { id: 'shipinhao', name: '视频号', icon: '💚', views: '234,567', followers: '56,789', engagement: '9.1%' },
      { id: 'bilibili', name: 'B站', icon: '📺', views: '156,789', followers: '34,567', engagement: '10.5%' },
      { id: 'xiaohongshu', name: '小红书', icon: '📖', views: '123,456', followers: '23,456', engagement: '11.2%' },
    ],
    dailyTrend: [
      { date: '03-07', views: 12345, likes: 890 },
      { date: '03-08', views: 15678, likes: 1123 },
      { date: '03-09', views: 14567, likes: 1045 },
      { date: '03-10', views: 18901, likes: 1345 },
      { date: '03-11', views: 21345, likes: 1567 },
      { date: '03-12', views: 19876, likes: 1423 },
      { date: '03-13', views: 23456, likes: 1789 },
    ],
  }

  const getPlatformIcon = (platform) => {
    const p = platforms.find(pl => pl.id === platform)
    return p?.icon || '📱'
  }

  const getPlatformName = (platform) => {
    const p = platforms.find(pl => pl.id === platform)
    return p?.name || platform
  }

  const maxViews = Math.max(...mockData.dailyTrend.map(d => d.views))

  const metrics = [
    { icon: '👁️', label: '总播放', value: mockData.overview.totalViews, change: mockData.overview.viewsChange },
    { icon: '👍', label: '总点赞', value: mockData.overview.totalLikes, change: mockData.overview.likesChange },
    { icon: '💬', label: '总评论', value: mockData.overview.totalComments, change: mockData.overview.commentsChange },
    { icon: '📤', label: '总分享', value: mockData.overview.totalShares, change: mockData.overview.sharesChange },
    { icon: '👥', label: '新增粉丝', value: mockData.overview.newFollowers, change: mockData.overview.followersChange },
  ]

  const getChangeClass = (change) => change.startsWith('+') ? 'positive' : 'negative'

  return (
    <PageContainer title="数据分析" description="多平台数据看板与趋势分析">
      <div className="analytics-toolbar">
        <div className="history-filters">
          {platforms.map(platform => (
            <button
              key={platform.id}
              onClick={() => setSelectedPlatform(platform.id)}
              className={`history-filter-btn ${selectedPlatform === platform.id ? 'active' : ''}`}
            >
              <span className="filter-icon">{platform.icon}</span>
              <span className="filter-text">{platform.name}</span>
            </button>
          ))}
        </div>
        <select
          value={timeRange}
          onChange={(e) => setTimeRange(e.target.value)}
          className="analytics-select"
        >
          {timeRanges.map(r => (
            <option key={r.id} value={r.id}>{r.name}</option>
          ))}
        </select>
      </div>

      <div className="analytics-overview-grid">
        {metrics.map((m, idx) => (
          <div key={idx} className="metric-card">
            <div className="metric-card-icon">{m.icon}</div>
            <div className="metric-info">
              <div className="metric-label">{m.label}</div>
              <div className="metric-value">{m.value}</div>
              <div className={`metric-change ${getChangeClass(m.change)}`}>{m.change}</div>
            </div>
          </div>
        ))}
      </div>

      <div className="analytics-content-grid">
        <div className="analytics-chart-section">
          <div className="card">
            <h3 className="section-title" style={{ marginBottom: '16px' }}>📈 数据趋势</h3>
            <div className="analytics-chart">
              {mockData.dailyTrend.map((day, idx) => (
                <div key={idx} className="chart-bar-group">
                  <div className="chart-bar-label">{day.date}</div>
                  <div
                    className="chart-bar"
                    style={{ height: `${(day.views / maxViews) * 180}px` }}
                  />
                  <div className="chart-bar-value">{(day.views / 1000).toFixed(1)}k</div>
                </div>
              ))}
            </div>
          </div>
        </div>

        <div className="analytics-platform-section">
          <div className="card">
            <h3 className="section-title" style={{ marginBottom: '16px' }}>📱 平台数据</h3>
            <div className="platform-stats-list">
              {mockData.platformStats.map(platform => (
                <div key={platform.id} className="platform-stat-item">
                  <div className="platform-stat-header">
                    <span className="platform-stat-icon">{platform.icon}</span>
                    <div className="platform-stat-info">
                      <span className="platform-stat-name">{platform.name}</span>
                      <span className="platform-stat-followers">粉丝: {platform.followers}</span>
                    </div>
                  </div>
                  <div className="platform-stat-metrics">
                    <span className="platform-stat-views">播放: {platform.views}</span>
                    <span className="platform-stat-engagement">{platform.engagement}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      <div className="card" style={{ marginTop: '24px' }}>
        <h3 className="section-title" style={{ marginBottom: '16px' }}>🏆 爆款视频排行</h3>
        <div className="analytics-table-wrapper">
          <table className="analytics-table">
            <thead>
              <tr>
                <th>排名</th>
                <th>视频标题</th>
                <th>平台</th>
                <th>播放</th>
                <th>点赞</th>
                <th>评论</th>
                <th>日期</th>
              </tr>
            </thead>
            <tbody>
              {mockData.topVideos.map((video, idx) => (
                <tr key={video.id}>
                  <td>
                    <span className={`rank-badge rank-${idx < 3 ? idx + 1 : 'default'}`}>
                      {idx + 1}
                    </span>
                  </td>
                  <td className="video-title-cell">{video.title}</td>
                  <td>
                    <span className="platform-cell">
                      {getPlatformIcon(video.platform)} {getPlatformName(video.platform)}
                    </span>
                  </td>
                  <td>{video.views}</td>
                  <td>{video.likes}</td>
                  <td>{video.comments}</td>
                  <td className="date-cell">{video.date}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </PageContainer>
  )
}

export default AnalyticsPage
