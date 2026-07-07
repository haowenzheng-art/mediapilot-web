import { useState } from 'react'
import { useHotSearch } from '../../hooks/use-hot-search'
import PageContainer from '../../components/common/PageContainer'

const getTrendIcon = (trend) => {
  switch (trend) {
    case 'up': return '📈'
    case 'down': return '📉'
    default: return '➡️'
  }
}

const formatNumber = (num) => {
  if (num >= 10000) return (num / 10000).toFixed(1) + '万'
  if (num >= 1000) return (num / 1000).toFixed(1) + 'k'
  return Math.floor(num).toLocaleString()
}

const formatTime = (dateStr) => {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  const now = new Date()
  const diff = Math.floor((now - date) / 1000)

  if (diff < 60) return '刚刚'
  if (diff < 3600) return `${Math.floor(diff / 60)}分钟前`
  if (diff < 86400) return `${Math.floor(diff / 3600)}小时前`
  if (diff < 604800) return `${Math.floor(diff / 86400)}天前`

  return date.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' })
}

/**
 * 降级 / 缓存 提示条（v3 改造）
 *
 * - freshness='degraded'：有平台失败，黄条提示
 * - used_cache=true：命中缓存，灰条提示"缓存于 X 秒前"
 */
function DegradedNotice({ result }) {
  if (!result) return null
  const { freshness, degraded_platforms, sixty_failed_platforms, used_cache, cached_at } = result

  if (freshness === 'fresh' && !used_cache) return null

  // 缓存命中
  if (used_cache && cached_at) {
    const cacheAgeSec = Math.floor((Date.now() - new Date(cached_at).getTime()) / 1000)
    let ageLabel
    if (cacheAgeSec < 60) ageLabel = `${cacheAgeSec} 秒前`
    else if (cacheAgeSec < 3600) ageLabel = `${Math.floor(cacheAgeSec / 60)} 分钟前`
    else ageLabel = `${Math.floor(cacheAgeSec / 3600)} 小时前`

    return (
      <div
        style={{
          padding: '12px 16px',
          marginBottom: '12px',
          background: 'rgba(59, 130, 246, 0.08)',
          border: '1px solid rgba(59, 130, 246, 0.25)',
          borderRadius: '8px',
          fontSize: '13px',
          color: 'var(--text-secondary)',
        }}
      >
        📦 命中缓存（{ageLabel}），可点击"搜索"按钮强制刷新
      </div>
    )
  }

  // 降级
  if (freshness === 'degraded') {
    const failedPlatforms = sixty_failed_platforms && sixty_failed_platforms.length > 0
      ? sixty_failed_platforms
      : (degraded_platforms || [])
    return (
      <div
        style={{
          padding: '12px 16px',
          marginBottom: '12px',
          background: 'rgba(245, 158, 11, 0.08)',
          border: '1px solid rgba(245, 158, 11, 0.3)',
          borderRadius: '8px',
          fontSize: '13px',
          color: 'var(--text-primary)',
        }}
      >
        <div style={{ fontWeight: '600', marginBottom: '4px' }}>
          ⚠️ 部分平台数据获取失败
        </div>
        <div style={{ color: 'var(--text-secondary)', fontSize: '12px' }}>
          {failedPlatforms.length > 0
            ? `失败：${failedPlatforms.join('、')}。已自动用百度新闻补充结果。`
            : '已自动降级到部分数据源。'}
        </div>
      </div>
    )
  }

  return null
}

function HotSearchPage() {
  const [expandedTopics, setExpandedTopics] = useState(new Set())
  const [aiSummaries, setAiSummaries] = useState(new Map())
  const [loadingTopics, setLoadingTopics] = useState(new Set())

  const {
    keyword, setKeyword,
    platforms, togglePlatform,
    days, setDays,
    result, loading, error,
    search, exportData,
    platformsList,
  } = useHotSearch()

  const fetchAiSummary = async (topic) => {
    const topicKey = topic.title

    if (expandedTopics.has(topicKey)) {
      const newExpanded = new Set(expandedTopics)
      newExpanded.delete(topicKey)
      setExpandedTopics(newExpanded)
      return
    }

    setExpandedTopics(prev => new Set([...prev, topicKey]))
    setLoadingTopics(prev => new Set([...prev, topicKey]))

    try {
      const response = await fetch('/api/v1/trending/summary', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          title: topic.title,
          summary: topic.summary || '',
          url: topic.source_url || topic.url,
          source: topic.source
        })
      })

      const data = await response.json()
      if (data.success) {
        setAiSummaries(prev => new Map([...prev, [topicKey, data.data]]))
      } else {
        setAiSummaries(prev => new Map([...prev, [topicKey, { summary: '生成总结失败，请稍后重试' }]]))
      }
    } catch (err) {
      setAiSummaries(prev => new Map([...prev, [topicKey, { summary: '生成总结失败，请稍后重试' }]]))
    } finally {
      setLoadingTopics(prev => {
        const newLoading = new Set(prev)
        newLoading.delete(topicKey)
        return newLoading
      })
    }
  }

  const copyToClipboard = async (text, type) => {
    try {
      await navigator.clipboard.writeText(text)
      alert(`已复制${type}到剪贴板`)
    } catch (err) {
      alert('复制失败，请手动复制')
    }
  }

  return (
    <PageContainer title="热点搜索" description="发现行业热点，获取创作灵感">
      <div className="search-form">
        <div className="search-form-group">
          <input
            type="text"
            value={keyword}
            onChange={(e) => setKeyword(e.target.value)}
            placeholder="输入关键词，如：AI、健身、美食..."
            disabled={loading}
          />
        </div>

        <div className="search-form-group">
          <div className="search-form-label">选择平台</div>
          <div className="search-form-platforms">
            {platformsList.map(p => (
              <button
                key={p.id}
                onClick={() => togglePlatform(p.id)}
                disabled={loading}
                className={`platform-btn ${platforms.includes(p.id) ? 'active' : ''}`}
                title={p.name}
              >
                {p.icon} {p.name}
              </button>
            ))}
          </div>
        </div>

        <div className="search-form-group">
          <div className="search-form-range-label">
            搜索时间范围：<strong>{days}</strong> 天
          </div>
          <input
            type="range" min="1" max="30" value={days}
            onChange={(e) => setDays(parseInt(e.target.value))}
            disabled={loading}
            style={{ width: '100%', opacity: loading ? 0.5 : 1 }}
          />
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', color: 'var(--text-tertiary)', marginTop: '4px' }}>
            <span>1天</span>
            <span>7天</span>
            <span>14天</span>
            <span>30天</span>
          </div>
        </div>

        {error && (
          <div className="alert alert-error" style={{ marginBottom: '16px' }}>{error}</div>
        )}

        <button
          onClick={search}
          disabled={!keyword.trim() || platforms.length === 0 || loading}
          className="btn btn-primary btn-full btn-lg"
        >
          {loading ? (
            <>
              <span className="loading-spinner"></span>
              搜索中...
            </>
          ) : (
            <>
              <span style={{ marginRight: '6px' }}>🔍</span>
              开始搜索
            </>
          )}
        </button>
      </div>

      {result && (
        <div className="search-results">
          {/* 订阅提示 */}
          <div style={{
            padding: '12px 16px',
            background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
            borderRadius: '8px',
            marginBottom: '16px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            boxShadow: '0 2px 8px rgba(102, 126, 234, 0.2)'
          }}>
            <div>
              <div style={{ color: 'white', fontSize: '14px', fontWeight: '600', marginBottom: '4px' }}>
                📬 想要持续追踪这些话题？
              </div>
              <div style={{ color: 'rgba(255,255,255,0.85)', fontSize: '12px' }}>
                订阅话题后，系统会自动推送最新热点到您的首页
              </div>
            </div>
            <button
              onClick={() => window.dispatchEvent(new CustomEvent('tab-change', { detail: 'subscription' }))}
              style={{
                padding: '8px 16px',
                fontSize: '13px',
                fontWeight: '600',
                background: 'white',
                color: '#667eea',
                border: 'none',
                borderRadius: '6px',
                cursor: 'pointer',
                whiteSpace: 'nowrap'
              }}
            >
              前往订阅 →
            </button>
          </div>

          <div className="export-buttons">
            <button onClick={() => exportData('csv')} className="export-btn" disabled={loading}>
              📄 导出 CSV
            </button>
            <button onClick={() => exportData('xlsx')} className="export-btn" disabled={loading}>
              📊 导出 Excel
            </button>
          </div>

          <div className="result-stats">
            找到 <strong>{result.total_count}</strong> 个相关热点
          </div>

          {/* v3 改造：降级 / 缓存 提示 */}
          <DegradedNotice result={result} />

          <div className="hot-topic-grid">
            {result.hot_topics.map((topic, index) => (
              <div key={index} className="hot-topic-card">
                <div className="hot-topic-header">
                  <h3
                    className="hot-topic-title"
                    onClick={() => fetchAiSummary(topic)}
                    style={{
                      cursor: 'pointer',
                      transition: 'all 0.2s',
                      color: expandedTopics.has(topic.title) ? 'var(--accent-primary)' : 'inherit'
                    }}
                    onMouseEnter={(e) => e.target.style.opacity = '0.7'}
                    onMouseLeave={(e) => e.target.style.opacity = '1'}
                  >
                    {expandedTopics.has(topic.title) ? '✓ ' : ''}{topic.title}
                  </h3>
                  <div className="hot-topic-heat">
                    {getTrendIcon(topic.trend_direction)} {formatNumber(topic.heat_value)}
                  </div>
                </div>

                <div className="hot-topic-meta">
                  <span className="hot-topic-platform">
                    {platformsList.find(p => p.id === topic.source || p.name === topic.source)?.name || topic.source}
                  </span>
                  {topic.published_at && (
                    <span className="hot-topic-time">
                      ⏰ {formatTime(topic.published_at)}
                    </span>
                  )}
                </div>

                {expandedTopics.has(topic.title) && (
                  <div style={{ marginTop: '12px', padding: '12px', background: 'var(--bg-secondary)', borderRadius: '8px' }}>
                    {loadingTopics.has(topic.title) ? (
                      <div style={{ textAlign: 'center', padding: '20px' }}>
                        <span className="loading-spinner"></span>
                        AI正在分析...
                      </div>
                    ) : aiSummaries.get(topic.title)?.summary ? (
                      <div>
                        <div style={{ display: 'flex', gap: '8px', marginBottom: '12px', flexWrap: 'wrap' }}>
                          <button
                            onClick={() => copyToClipboard(aiSummaries.get(topic.title).summary, '内容')}
                            style={{
                              padding: '6px 16px',
                              fontSize: '13px',
                              fontWeight: '600',
                              background: 'var(--accent-primary)',
                              color: 'white',
                              border: 'none',
                              borderRadius: '6px',
                              cursor: 'pointer',
                              display: 'flex',
                              alignItems: 'center',
                              gap: '6px'
                            }}
                          >
                            ⚡ 一键复制内容
                          </button>
                          <button
                            onClick={() => copyToClipboard(topic.title, '标题')}
                            style={{
                              padding: '6px 16px',
                              fontSize: '13px',
                              background: 'var(--bg-tertiary)',
                              color: 'var(--text-primary)',
                              border: 'none',
                              borderRadius: '6px',
                              cursor: 'pointer'
                            }}
                          >
                            复制标题
                          </button>
                        </div>
                        <div style={{ fontSize: '13px', lineHeight: '1.6', color: 'var(--text-primary)', maxHeight: '400px', overflow: 'auto', whiteSpace: 'pre-wrap' }}>
                          {aiSummaries.get(topic.title).summary}
                        </div>
                        <div style={{ marginTop: '8px', fontSize: '11px', color: 'var(--text-tertiary)' }}>
                          💡 复制内容 → 文案生成助手 | 复制标题 → 脚本生成助手
                        </div>
                        <button
                          onClick={() => {
                            const content = aiSummaries.get(topic.title).summary
                            // 用 sessionStorage 桥接，避免目标页未 mount 时事件丢失
                            sessionStorage.setItem('copywriting:pending_hotspot', content)
                            window.dispatchEvent(new CustomEvent('tab-change', { detail: 'copywriting' }))
                          }}
                          style={{
                            marginTop: '8px',
                            padding: '8px 16px',
                            fontSize: '12px',
                            background: 'var(--bg-primary)',
                            color: 'var(--accent-primary)',
                            border: '1px solid var(--accent-primary)',
                            borderRadius: '6px',
                            cursor: 'pointer',
                            width: '100%'
                          }}
                        >
                          🚀 使用此内容生成口播文案
                        </button>
                      </div>
                    ) : null}
                  </div>
                )}

                {topic.summary && !expandedTopics.has(topic.title) && (
                  <div className="hot-topic-summary">{topic.summary}</div>
                )}

                {topic.category && (
                  <div style={{ fontSize: '11px', color: 'var(--text-tertiary)' }}>
                    📁 {topic.category}
                  </div>
                )}

                {(topic.source_url || topic.url) && (
                  <a
                    href={topic.source_url || topic.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="hot-topic-link"
                    onClick={(e) => e.stopPropagation()}
                  >
                    查看原文 →
                  </a>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </PageContainer>
  )
}

export default HotSearchPage
