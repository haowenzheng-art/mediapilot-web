import { useRef, useState } from 'react'
import { API_BASE_URL } from '../../services/api'

/**
 * 视频预览播放器（v3 改造）
 *
 * 用户先 preview 满意，再点下载原画质视频。
 * 后端 GET /api/v1/media/video-edit/{task_id}/preview 返回 inline + Range。
 */
export function VideoPreviewPlayer({ taskId, sourceVideoName }) {
  const videoRef = useRef(null)
  const [error, setError] = useState(null)

  if (!taskId) return null

  const src = `${API_BASE_URL}/api/v1/media/video-edit/${taskId}/preview`

  return (
    <div
      style={{
        padding: '12px',
        background: 'var(--bg-secondary)',
        border: '1px solid var(--border-color)',
        borderRadius: 'var(--radius-md)',
      }}
    >
      <video
        ref={videoRef}
        controls
        preload="metadata"
        src={src}
        style={{
          width: '100%',
          borderRadius: 'var(--radius-sm)',
          background: '#000',
          maxHeight: '480px',
        }}
        onError={() => setError('预览加载失败，请下载完整视频查看')}
      />
      {error && (
        <div
          style={{
            marginTop: '8px',
            padding: '8px 12px',
            background: 'rgba(239, 68, 68, 0.1)',
            border: '1px solid rgba(239, 68, 68, 0.3)',
            borderRadius: 'var(--radius-sm)',
            fontSize: '12px',
            color: '#dc2626',
          }}
        >
          {error}
        </div>
      )}
      <p
        style={{
          marginTop: '8px',
          fontSize: '11px',
          color: 'var(--text-tertiary)',
          textAlign: 'center',
        }}
      >
        360p 预览（高压缩）。满意后点右上"📥 视频"下载原画质。
      </p>
    </div>
  )
}