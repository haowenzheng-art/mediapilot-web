import { useVideoEdit } from '../../hooks/use-video-edit'
import { VideoPreviewPlayer } from '../../components/video-edit/VideoPreviewPlayer'
import { TimelineBar } from '../../components/video-edit/TimelineBar'

function formatTime(sec) {
  if (sec == null) return '--:--'
  const m = Math.floor(sec / 60)
  const s = Math.floor(sec % 60)
  return `${m}:${s.toString().padStart(2, '0')}`
}

function VideoEditPage() {
  const {
    videoFile, fileInputRef, handleFileChange, handleDrop,
    taskId, status, progress, result, error,
    strength, setStrength,
    startEdit, clearAll, downloadVideo, downloadSubtitle,
  } = useVideoEdit()

  const isProcessing = status === 'uploading' || status === 'processing'
  const hasResult = status === 'completed' && result

  return (
    <div style={{ padding: '24px 0', minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      <div style={{ textAlign: 'center', marginBottom: '32px', padding: '0 24px' }}>
        <h1 style={{ fontSize: '28px', fontWeight: '700', color: 'var(--text-primary)', marginBottom: '8px' }}>AI 视频剪辑</h1>
        <p style={{ fontSize: '14px', color: 'var(--text-secondary)' }}>自动识别并删除口播视频中的磕巴片段（嗯/啊/重复），输出干净视频 + 字幕</p>
      </div>

      <div style={{ maxWidth: '1200px', margin: '0 auto', padding: '0 24px', display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(380px, 1fr))', gap: '24px', width: '100%' }}>
        {/* 左：上传 + 设置 */}
        <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          <h3 style={{ fontSize: '16px', fontWeight: '600', margin: 0 }}>上传视频</h3>

          {!videoFile ? (
            <div
              onClick={() => fileInputRef.current?.click()}
              onDrop={handleDrop}
              onDragOver={(e) => e.preventDefault()}
              style={{ padding: '48px 24px', border: '2px dashed var(--border-color)', borderRadius: 'var(--radius-lg)', textAlign: 'center', cursor: 'pointer', transition: 'all 0.15s ease' }}
              onMouseEnter={(e) => { e.currentTarget.style.borderColor = 'var(--primary)'; e.currentTarget.style.background = 'var(--bg-secondary)' }}
              onMouseLeave={(e) => { e.currentTarget.style.borderColor = 'var(--border-color)'; e.currentTarget.style.background = 'transparent' }}
            >
              <input ref={fileInputRef} type="file" accept="video/*" onChange={handleFileChange} style={{ display: 'none' }} />
              <div style={{ fontSize: '48px', marginBottom: '16px' }}>🎬</div>
              <p style={{ fontSize: '16px', fontWeight: '500', marginBottom: '8px' }}>点击或拖拽视频到这里</p>
              <p style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>支持 MP4, MOV, AVI, MKV</p>
            </div>
          ) : (
            <div style={{ padding: '16px', border: '1px solid var(--border-color)', borderRadius: 'var(--radius-md)', background: 'var(--bg-secondary)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                  <div style={{ width: '48px', height: '48px', borderRadius: 'var(--radius-md)', background: 'var(--bg-tertiary)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '24px' }}>🎬</div>
                  <div>
                    <p style={{ fontSize: '14px', fontWeight: '500' }}>{videoFile.name}</p>
                    <p style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>{(videoFile.size / 1024 / 1024).toFixed(2)} MB</p>
                  </div>
                </div>
                {!isProcessing && (
                  <button onClick={clearAll} style={{ background: 'transparent', border: 'none', color: 'var(--text-tertiary)', cursor: 'pointer', padding: '8px' }}>✕</button>
                )}
              </div>

              {status === 'idle' && (
                <button onClick={startEdit} className="btn btn-primary btn-full btn-lg">
                  开始 AI 剪辑
                </button>
              )}

              {isProcessing && (
                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px', fontSize: '13px' }}>
                    <span style={{ color: 'var(--text-secondary)' }}>
                      {status === 'uploading' ? '上传中...' : 'AI 分析中（转写 + LLM 判断 + FFmpeg 剪切）...'}
                    </span>
                    <span style={{ fontWeight: '500' }}>{progress}%</span>
                  </div>
                  <div style={{ height: '4px', borderRadius: '2px', background: 'var(--bg-tertiary)', overflow: 'hidden' }}>
                    <div style={{ height: '100%', width: `${progress}%`, background: 'var(--primary)', transition: 'width 0.3s ease' }} />
                  </div>
                </div>
              )}
            </div>
          )}

          {/* 剪辑强度选择 */}
          <div style={{ padding: '16px', background: 'var(--bg-secondary)', borderRadius: 'var(--radius-md)' }}>
            <p style={{ fontSize: '13px', fontWeight: '500', marginBottom: '12px', color: 'var(--text-primary)' }}>剪辑强度</p>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '8px' }}>
              {[
                { value: 'conservative', label: '轻柔', desc: '仅删语气词', color: 'var(--success)' },
                { value: 'medium', label: '标准', desc: '语气词+停顿', color: 'var(--primary)' },
                { value: 'aggressive', label: '强力', desc: '全面清理', color: 'var(--warning)' },
              ].map((opt) => (
                <button
                  key={opt.value}
                  onClick={() => setStrength(opt.value)}
                  disabled={isProcessing}
                  style={{
                    padding: '10px 8px',
                    borderRadius: 'var(--radius-md)',
                    border: strength === opt.value ? `2px solid ${opt.color}` : '2px solid var(--border-color)',
                    background: strength === opt.value ? `${opt.color}15` : 'transparent',
                    cursor: isProcessing ? 'not-allowed' : 'pointer',
                    textAlign: 'center',
                    transition: 'all 0.15s ease',
                  }}
                >
                  <div style={{ fontSize: '14px', fontWeight: '600', color: strength === opt.value ? opt.color : 'var(--text-primary)', marginBottom: '2px' }}>{opt.label}</div>
                  <div style={{ fontSize: '11px', color: 'var(--text-tertiary)' }}>{opt.desc}</div>
                </button>
              ))}
            </div>
          </div>

          {error && (
            <div className="alert alert-error">
              <p style={{ fontWeight: '500' }}>处理失败</p>
              <p style={{ fontSize: '13px', marginTop: '4px' }}>{error}</p>
              {taskId && <p style={{ fontSize: '12px', marginTop: '4px', color: 'var(--text-tertiary)' }}>任务 ID: {taskId}</p>}
            </div>
          )}

          <div style={{ padding: '16px', background: 'var(--bg-secondary)', borderRadius: 'var(--radius-md)' }}>
            <p style={{ fontSize: '13px', fontWeight: '500', marginBottom: '8px', color: 'var(--text-primary)' }}>使用提示</p>
            <ul style={{ fontSize: '13px', color: 'var(--text-secondary)', paddingLeft: '20px', lineHeight: '1.8' }}>
              <li>对口播视频效果最好（有明显磕巴/重复/语气词）</li>
              <li>AI 用 LLM 智能判断哪些是无效片段，不会粗暴删"然后/这个"</li>
              <li>处理时间约 = 视频时长的 2-3 倍（转写 + LLM）</li>
              <li>每分钟视频消耗 15 配额</li>
            </ul>
          </div>
        </div>

        {/* 右：结果 */}
        <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <h3 style={{ fontSize: '16px', fontWeight: '600', margin: 0 }}>剪辑结果</h3>
            {hasResult && (
              <div style={{ display: 'flex', gap: '8px' }}>
                <button onClick={downloadVideo} className="btn btn-primary" style={{ padding: '6px 14px', fontSize: '13px' }}>📥 视频</button>
                <button onClick={downloadSubtitle} className="btn btn-secondary" style={{ padding: '6px 14px', fontSize: '13px' }}>📄 字幕</button>
              </div>
            )}
          </div>

          {hasResult ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              {/* v3 改造：360p preview 视频（v3 用户先预览，满意再下载） */}
              {result.preview_video_path && (
                <VideoPreviewPlayer taskId={taskId} sourceVideoName={result.source_video_name} />
              )}

              {/* 统计卡片 */}
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '12px' }}>
                <div style={{ padding: '12px 16px', background: 'var(--bg-secondary)', borderRadius: 'var(--radius-md)' }}>
                  <p style={{ fontSize: '12px', color: 'var(--text-secondary)', marginBottom: '4px' }}>原始时长</p>
                  <p style={{ fontSize: '18px', fontWeight: '600' }}>{formatTime(result.original_duration)}</p>
                </div>
                <div style={{ padding: '12px 16px', background: 'var(--bg-secondary)', borderRadius: 'var(--radius-md)' }}>
                  <p style={{ fontSize: '12px', color: 'var(--text-secondary)', marginBottom: '4px' }}>剪辑后</p>
                  <p style={{ fontSize: '18px', fontWeight: '600' }}>{formatTime(result.final_duration)}</p>
                </div>
                <div style={{ padding: '12px 16px', background: 'var(--bg-secondary)', borderRadius: 'var(--radius-md)' }}>
                  <p style={{ fontSize: '12px', color: 'var(--text-secondary)', marginBottom: '4px' }}>删除片段</p>
                  <p style={{ fontSize: '18px', fontWeight: '600' }}>{result.removed_segments?.length || 0}</p>
                </div>
              </div>

              {/* v3 改造：剪辑时间轴可视化（绿=保留 / 红=删除） */}
              {(result.kept_segments?.length || result.removed_segments?.length) && (
                <TimelineBar
                  keptSegments={result.kept_segments || []}
                  removedSegments={result.removed_segments || []}
                  originalDuration={result.original_duration}
                />
              )}

              {/* 删除片段列表 */}
              {result.removed_segments && result.removed_segments.length > 0 && (
                <div>
                  <p style={{ fontSize: '13px', fontWeight: '500', marginBottom: '8px', color: 'var(--text-secondary)' }}>
                    🗑️ 删除的无效片段
                  </p>
                  <div style={{ padding: '12px 16px', border: '1px solid var(--border-color)', borderRadius: 'var(--radius-md)', background: 'var(--bg-secondary)', maxHeight: '240px', overflow: 'auto' }}>
                    {result.removed_segments.map((seg, idx) => (
                      <div key={idx} style={{ padding: '8px 0', borderBottom: idx < result.removed_segments.length - 1 ? '1px solid var(--border-color)' : 'none', fontSize: '13px' }}>
                        <div style={{ display: 'flex', gap: '12px', alignItems: 'flex-start' }}>
                          <span style={{ color: 'var(--text-tertiary)', fontFamily: 'monospace', flexShrink: 0, fontSize: '12px' }}>
                            {formatTime(seg.start)} → {formatTime(seg.end)}
                          </span>
                          <span style={{ color: 'var(--text-primary)', flex: 1 }}>{seg.text || '（无文字）'}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* 干净转写文本 */}
              {result.transcript && (
                <div>
                  <p style={{ fontSize: '13px', fontWeight: '500', marginBottom: '8px', color: 'var(--text-secondary)' }}>
                    ✅ 干净转写（已去除磕巴）
                  </p>
                  <div style={{ padding: '12px 16px', border: '1px solid var(--border-color)', borderRadius: 'var(--radius-md)', background: 'var(--bg-secondary)', maxHeight: '200px', overflow: 'auto', fontSize: '13px', lineHeight: '1.7', whiteSpace: 'pre-wrap' }}>
                    {result.transcript}
                  </div>
                </div>
              )}

              {taskId && (
                <p style={{ fontSize: '12px', color: 'var(--text-tertiary)' }}>任务 ID: {taskId}</p>
              )}
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '64px 24px', color: 'var(--text-tertiary)', minHeight: '400px' }}>
              <div style={{ fontSize: '48px', marginBottom: '16px' }}>🎬</div>
              <p style={{ fontSize: '14px' }}>{isProcessing ? 'AI 正在分析视频...' : '上传视频开始 AI 剪辑'}</p>
              {isProcessing && (
                <p style={{ fontSize: '12px', marginTop: '8px', color: 'var(--text-tertiary)' }}>
                  视频越长处理越久，请耐心等待
                </p>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default VideoEditPage
