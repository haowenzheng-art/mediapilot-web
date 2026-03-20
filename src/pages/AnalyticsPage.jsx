import { useState } from 'react'

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

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold flex items-center gap-2">
          <span>📊</span> 数据分析
        </h2>
        <div className="flex items-center gap-4">
          <select
            value={timeRange}
            onChange={(e) => setTimeRange(e.target.value)}
            className="px-4 py-2 bg-card border border-border rounded-lg focus:outline-none focus:border-primary"
          >
            {timeRanges.map(r => (
              <option key={r.id} value={r.id}>{r.name}</option>
            ))}
          </select>
        </div>
      </div>

      {/* 平台筛选 */}
      <div className="card mb-6">
        <div className="flex flex-wrap gap-2">
          {platforms.map(platform => (
            <button
              key={platform.id}
              onClick={() => setSelectedPlatform(platform.id)}
              className={`px-4 py-2 rounded-lg flex items-center gap-2 transition-all ${
                selectedPlatform === platform.id
                  ? 'bg-primary text-white'
                  : 'bg-bg-light hover:bg-bg-light/80'
              }`}
            >
              <span>{platform.icon}</span>
              <span>{platform.name}</span>
            </button>
          ))}
        </div>
      </div>

      {/* 数据概览卡片 */}
      <div className="grid md:grid-cols-2 lg:grid-cols-5 gap-4 mb-6">
        <div className="card">
          <div className="flex items-center justify-between mb-2">
            <span className="text-secondary text-sm">总播放</span>
            <span className="text-2xl">👁️</span>
          </div>
          <p className="text-2xl font-bold">{mockData.overview.totalViews}</p>
          <p className="text-sm text-green-500 mt-1">{mockData.overview.viewsChange}</p>
        </div>

        <div className="card">
          <div className="flex items-center justify-between mb-2">
            <span className="text-secondary text-sm">总点赞</span>
            <span className="text-2xl">❤️</span>
          </div>
          <p className="text-2xl font-bold">{mockData.overview.totalLikes}</p>
          <p className="text-sm text-green-500 mt-1">{mockData.overview.likesChange}</p>
        </div>

        <div className="card">
          <div className="flex items-center justify-between mb-2">
            <span className="text-secondary text-sm">总评论</span>
            <span className="text-2xl">💬</span>
          </div>
          <p className="text-2xl font-bold">{mockData.overview.totalComments}</p>
          <p className="text-sm text-green-500 mt-1">{mockData.overview.commentsChange}</p>
        </div>

        <div className="card">
          <div className="flex items-center justify-between mb-2">
            <span className="text-secondary text-sm">总分享</span>
            <span className="text-2xl">🔄</span>
          </div>
          <p className="text-2xl font-bold">{mockData.overview.totalShares}</p>
          <p className="text-sm text-green-500 mt-1">{mockData.overview.sharesChange}</p>
        </div>

        <div className="card">
          <div className="flex items-center justify-between mb-2">
            <span className="text-secondary text-sm">新增粉丝</span>
            <span className="text-2xl">👥</span>
          </div>
          <p className="text-2xl font-bold">{mockData.overview.newFollowers}</p>
          <p className="text-sm text-green-500 mt-1">{mockData.overview.followersChange}</p>
        </div>
      </div>

      <div className="grid lg:grid-cols-3 gap-6">
        {/* 趋势图 */}
        <div className="lg:col-span-2">
          <div className="card">
            <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
              <span>📈</span> 数据趋势
            </h3>
            <div className="h-64 flex items-end justify-between gap-2 px-4">
              {mockData.dailyTrend.map((day, idx) => (
                <div key={idx} className="flex-1 flex flex-col items-center gap-2">
                  <div className="text-xs text-secondary">{day.date}</div>
                  <div
                    className="w-full bg-gradient-to-t from-primary to-primary/60 rounded-t-lg transition-all hover:opacity-80"
                    style={{ height: `${(day.views / maxViews) * 180}px` }}
                  />
                  <div className="text-xs text-secondary">{(day.views / 1000).toFixed(1)}k</div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* 平台数据 */}
        <div className="card">
          <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <span>📱</span> 平台数据
          </h3>
          <div className="space-y-4">
            {mockData.platformStats.map(platform => (
              <div key={platform.id} className="p-3 bg-bg-light rounded-lg border border-border">
                <div className="flex items-center gap-3 mb-2">
                  <span className="text-2xl">{platform.icon}</span>
                  <div className="flex-1">
                    <p className="font-medium">{platform.name}</p>
                    <p className="text-sm text-secondary">粉丝: {platform.followers}</p>
                  </div>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-secondary">播放: {platform.views}</span>
                  <span className="text-primary font-medium">{platform.engagement}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* 爆款视频排行 */}
      <div className="card mt-6">
        <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
          <span>🏆</span> 爆款视频排行
        </h3>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="text-left text-secondary text-sm border-b border-border">
                <th className="pb-3 font-medium">排名</th>
                <th className="pb-3 font-medium">视频标题</th>
                <th className="pb-3 font-medium">平台</th>
                <th className="pb-3 font-medium">播放</th>
                <th className="pb-3 font-medium">点赞</th>
                <th className="pb-3 font-medium">评论</th>
                <th className="pb-3 font-medium">日期</th>
              </tr>
            </thead>
            <tbody>
              {mockData.topVideos.map((video, idx) => (
                <tr key={video.id} className="border-b border-border/50 hover:bg-bg-light/50">
                  <td className="py-4">
                    <span className={`inline-flex items-center justify-center w-8 h-8 rounded-full text-sm font-bold ${
                      idx === 0 ? 'bg-yellow-500 text-white' :
                      idx === 1 ? 'bg-gray-400 text-white' :
                      idx === 2 ? 'bg-amber-600 text-white' :
                      'bg-bg-light text-secondary'
                    }`}>
                      {idx + 1}
                    </span>
                  </td>
                  <td className="py-4 font-medium max-w-md truncate">{video.title}</td>
                  <td className="py-4">
                    <span className="flex items-center gap-1">
                      {getPlatformIcon(video.platform)} {getPlatformName(video.platform)}
                    </span>
                  </td>
                  <td className="py-4">{video.views}</td>
                  <td className="py-4">{video.likes}</td>
                  <td className="py-4">{video.comments}</td>
                  <td className="py-4 text-secondary">{video.date}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}

export default AnalyticsPage
