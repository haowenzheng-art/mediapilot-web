import { useState } from 'react'
import { useVideoAnalysis } from '../../hooks/use-video-analysis'
import PageContainer from '../../components/common/PageContainer'

const formatNumber = (num) => {
  if (num === undefined || num === null || num === 0) return '0'
  if (num >= 10000) return (num / 10000).toFixed(1) + '万'
  if (num >= 1000) return (num / 1000).toFixed(1) + 'k'
  return num.toLocaleString()
}

const formatDuration = (seconds) => {
  const mins = Math.floor(seconds / 60)
  const secs = seconds % 60
  return `${mins}:${secs.toString().padStart(2, '0')}`
}

function VideoAnalysisPage() {
  const {
    videoUrl, setVideoUrl,
    platform, setPlatform,
    videoInfo, transcript,
    isLoadingInfo, isLoadingTranscript, error,
    fetchVideo, getTranscript,
    platforms,
  } = useVideoAnalysis()

  const [transcriptView, setTranscriptView] = useState('full')
  const isDisabled = isLoadingInfo || isLoadingTranscript

  return (
    <PageContainer title="视频分析" description="分析视频数据，获取逐字稿">
      <div className="video-analysis-layout">
        {/* 视频链接和平台选择 */}
        <div className="video-input-section">
          <h3 className="section-title">
            <span>🔗</span>
            视频链接
          </h3>
          <div className="platform-selector">
            {platforms.map(p => (
              <button
                key={p.id}
                onClick={() => setPlatform(p.id)}
                className={`platform-btn ${platform === p.id ? 'active' : ''}`}
                disabled={isDisabled}
              >
                {p.icon} {p.name}
              </button>
            ))}
          </div>
          <div className="alert alert-info" style={{ fontSize: '13px', lineHeight: '1.7' }}>
            目前暂时支持 B站中文视频分析。其他平台视频解析和逐字稿能力尚未稳定，暂不开放入口。
          </div>
          <input
            type="text"
            value={videoUrl}
            onChange={(e) => setVideoUrl(e.target.value)}
            placeholder="粘贴 B站中文视频链接..."
            className="video-url-input"
            disabled={isDisabled}
          />
          {error && <div className="error-alert">{error}</div>}
        </div>

        {/* 视频信息 */}
        <div className="video-info-section">
          <h3 className="section-title">
            <span>📊</span>
            视频信息
          </h3>
          {videoInfo ? (
            <>
              <div className="video-info-grid">
                <div className="info-item">
                  <span className="info-label">标题</span>
                  <span className="info-value">{videoInfo.title}</span>
                </div>
                <div className="info-item">
                  <span className="info-label">时长</span>
                  <span className="info-value">{formatDuration(videoInfo.duration)}</span>
                </div>
                <div className="info-item">
                  <span className="info-label">播放</span>
                  <span className="info-value">{formatNumber(videoInfo.view_count)}</span>
                </div>
                <div className="info-item">
                  <span className="info-label">点赞</span>
                  <span className="info-value">{formatNumber(videoInfo.like_count)}</span>
                </div>
                <div className="info-item">
                  <span className="info-label">评论</span>
                  <span className="info-value">{formatNumber(videoInfo.comment_count)}</span>
                </div>
                <div className="info-item">
                  <span className="info-label">平台</span>
                  <span className="info-value">{videoInfo.platform}</span>
                </div>
              </div>
              {videoInfo.thumbnail_url && (
                <div style={{ marginTop: '20px' }}>
                  <img src={`/api/v1/video/proxy-image?url=${encodeURIComponent(videoInfo.thumbnail_url)}`} alt="视频封面" style={{ width: '100%', borderRadius: '12px', maxHeight: '240px', objectFit: 'cover' }} />
                </div>
              )}
              {videoInfo.video_url && (
                <a href={videoInfo.video_url} target="_blank" rel="noopener noreferrer" className="btn btn-primary btn-full" style={{ marginTop: '16px', textAlign: 'center' }}>
                  查看原视频 →
                </a>
              )}
            </>
          ) : (
            <div className="empty-state" style={{ padding: '40px 20px' }}>
              <div className="empty-icon">📊</div>
              <p className="empty-text">输入视频链接，获取视频信息</p>
            </div>
          )}
        </div>

        {/* 操作按钮 */}
        <div className="action-buttons">
          <button onClick={fetchVideo} disabled={isLoadingInfo || !videoUrl.trim()} className="btn btn-primary btn-large">
            {isLoadingInfo ? '获取中...' : '获取视频信息'}
          </button>
          {videoInfo && (
            <button onClick={getTranscript} disabled={isLoadingTranscript} className="btn btn-secondary btn-large"
              style={{
                backgroundColor: isLoadingTranscript ? '#666' : '#4CAF50',
                color: '#fff',
                opacity: isLoadingTranscript ? 0.7 : 1
              }}
            >
              {isLoadingTranscript ? '获取中...' : '获取逐字稿'}
            </button>
          )}
        </div>

        {/* 逐字稿 */}
        {videoInfo && !transcript && !isLoadingTranscript && (
          <div className="empty-state" style={{ padding: '20px', textAlign: 'center', color: '#999' }}>
            <p>获取视频信息后，点击"获取逐字稿"按钮</p>
          </div>
        )}

        {isLoadingTranscript && (
          <div className="loading-state" style={{ padding: '40px', textAlign: 'center' }}>
            <p style={{ fontSize: '16px', color: '#666' }}>⏳ 正在转写视频音频...</p>
            <p style={{ fontSize: '14px', color: '#999', marginTop: '10px' }}>首次使用需要加载模型，可能需要几分钟</p>
          </div>
        )}

        {transcript && (
          <div className="transcript-section">
            <div className="section-header">
              <h3 className="section-title">
                <span>📝</span>
                视频逐字稿
              </h3>
            </div>
            <div className="transcript-content">
              <div className="transcript-tabs">
                <div
                  onClick={() => setTranscriptView('full')}
                  className={`transcript-tab ${transcriptView === 'full' ? 'active' : ''}`}
                >
                  完整文本
                </div>
                <div
                  onClick={() => setTranscriptView('timeline')}
                  className={`transcript-tab ${transcriptView === 'timeline' ? 'active' : ''}`}
                >
                  时间轴
                </div>
              </div>

              <div className="transcript-body">
                {transcriptView === 'full' && (
                  <div className="full-text">
                    <h4>完整文本</h4>
                    <p>{transcript.full_transcript}</p>
                  </div>
                )}
                {transcriptView === 'timeline' && transcript.lines?.map((line, idx) => (
                  <div key={idx} className="timeline-line">
                    <span className="timeline-time">{line.time}</span>
                    <span className="timeline-text">{line.text}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>
    </PageContainer>
  )
}

export default VideoAnalysisPage
