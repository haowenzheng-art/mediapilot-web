import { useTranscription } from '../../hooks/use-transcription'

function TranscriptionPage() {
  const {
    mode, switchMode,
    audioFile, handleFileChange, handleDrop, fileInputRef,
    transcription, timestamps, outline, taskId, taskError,
    isTranscribing, isRecording, progress,
    recognitionSupported, recognitionError,
    transcribeFile, startRecording, stopRecording, clearAll, copyTranscription,
  } = useTranscription()

  return (
    <div style={{ padding: '24px 0', minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      <div style={{ textAlign: 'center', marginBottom: '32px', padding: '0 24px' }}>
        <h1 style={{ fontSize: '28px', fontWeight: '700', color: 'var(--text-primary)', marginBottom: '8px' }}>智能转录</h1>
        <p style={{ fontSize: '14px', color: 'var(--text-secondary)' }}>将语音转换为文字，支持文件上传和实时录音</p>
      </div>

      <div style={{ maxWidth: '1200px', margin: '0 auto', padding: '0 24px', display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(350px, 1fr))', gap: '24px', width: '100%' }}>
        {/* 左侧 - 输入区域 */}
        <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          {/* 模式切换 */}
          <div style={{ display: 'flex', gap: '8px' }}>
            <button onClick={() => switchMode('file')} className={`btn ${mode === 'file' ? 'btn-primary' : 'btn-ghost'}`} style={{ flex: 1 }}>📁 上传文件</button>
            <button onClick={() => switchMode('realtime')} className={`btn ${mode === 'realtime' ? 'btn-primary' : 'btn-ghost'}`} style={{ flex: 1 }}>🎤 实时录音</button>
          </div>

          {mode === 'file' ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              {!audioFile ? (
                <div
                  onClick={() => fileInputRef.current?.click()}
                  onDrop={handleDrop}
                  onDragOver={(e) => e.preventDefault()}
                  style={{ padding: '48px 24px', border: '2px dashed var(--border-color)', borderRadius: 'var(--radius-lg)', textAlign: 'center', cursor: 'pointer', transition: 'all 0.15s ease' }}
                  onMouseEnter={(e) => { e.currentTarget.style.borderColor = 'var(--primary)'; e.currentTarget.style.background = 'var(--bg-secondary)' }}
                  onMouseLeave={(e) => { e.currentTarget.style.borderColor = 'var(--border-color)'; e.currentTarget.style.background = 'transparent' }}
                >
                  <input ref={fileInputRef} type="file" accept="audio/*,video/*" onChange={handleFileChange} style={{ display: 'none' }} />
                  <div style={{ fontSize: '48px', marginBottom: '16px' }}>🎵</div>
                  <p style={{ fontSize: '16px', fontWeight: '500', marginBottom: '8px' }}>点击或拖拽文件到这里</p>
                  <p style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>支持 MP3, WAV, MP4, MOV 等格式</p>
                </div>
              ) : (
                <div style={{ padding: '16px', border: '1px solid var(--border-color)', borderRadius: 'var(--radius-md)', background: 'var(--bg-secondary)' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                      <div style={{ width: '48px', height: '48px', borderRadius: 'var(--radius-md)', background: 'var(--bg-tertiary)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '24px' }}>🎵</div>
                      <div>
                        <p style={{ fontSize: '14px', fontWeight: '500' }}>{audioFile.name}</p>
                        <p style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>{(audioFile.size / 1024 / 1024).toFixed(2)} MB</p>
                      </div>
                    </div>
                    <button onClick={clearAll} style={{ background: 'transparent', border: 'none', color: 'var(--text-tertiary)', cursor: 'pointer', padding: '8px' }}>✕</button>
                  </div>
                  <button onClick={transcribeFile} disabled={isTranscribing} className="btn btn-primary btn-full btn-lg">
                    {isTranscribing ? '转录中...' : '开始转录'}
                  </button>
                  {isTranscribing && (
                    <div>
                      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px', fontSize: '13px' }}>
                        <span style={{ color: 'var(--text-secondary)' }}>正在转录...</span>
                        <span style={{ fontWeight: '500' }}>{progress}%</span>
                      </div>
                      <div style={{ height: '4px', borderRadius: '2px', background: 'var(--bg-tertiary)', overflow: 'hidden' }}>
                        <div style={{ height: '100%', width: `${progress}%`, background: 'var(--primary)', transition: 'width 0.3s ease' }} />
                      </div>
                    </div>
                  )}
                </div>
              )}
              <div style={{ padding: '16px', background: 'var(--bg-secondary)', borderRadius: 'var(--radius-md)' }}>
                <p style={{ fontSize: '13px', fontWeight: '500', marginBottom: '8px', color: 'var(--text-primary)' }}>使用提示</p>
                <ul style={{ fontSize: '13px', color: 'var(--text-secondary)', paddingLeft: '20px', lineHeight: '1.8' }}>
                  <li>支持常见音频格式（MP3、WAV、M4A等）</li>
                  <li>支持视频格式（MP4、MOV等）</li>
                  <li>建议音频文件不超过 100MB</li>
                  <li>清晰度越高，转录准确率越高</li>
                </ul>
              </div>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              {!recognitionSupported && (
                <div className="alert alert-error">
                  <p>⚠️ 您的浏览器不支持语音识别</p>
                  <p style={{ fontSize: '13px', marginTop: '4px' }}>请使用 Chrome、Edge 或 Safari 浏览器</p>
                </div>
              )}
              {recognitionError && <div className="alert alert-error">{recognitionError}</div>}
              <div style={{ padding: '32px 24px', textAlign: 'center', background: 'var(--bg-secondary)', borderRadius: 'var(--radius-lg)' }}>
                {isRecording ? (
                  <div>
                    <div style={{ fontSize: '48px', marginBottom: '16px' }}>🎙️</div>
                    <p style={{ fontSize: '18px', fontWeight: '500', marginBottom: '8px' }}>正在录音...</p>
                    <p style={{ fontSize: '14px', color: 'var(--text-secondary)', marginBottom: '16px' }}>说话即可实时转文字</p>
                    <div style={{ display: 'flex', justifyContent: 'center', gap: '8px' }}>
                      {[0, 0.15, 0.3].map((delay, i) => (
                        <div key={i} style={{ width: '12px', height: '12px', borderRadius: '50%', background: 'var(--primary)', animation: `bounce 1s ease-in-out infinite ${delay}s` }} />
                      ))}
                    </div>
                  </div>
                ) : (
                  <div>
                    <div style={{ fontSize: '48px', marginBottom: '16px' }}>🎤</div>
                    <p style={{ fontSize: '18px', fontWeight: '500', marginBottom: '8px' }}>点击开始录音</p>
                    <p style={{ fontSize: '14px', color: 'var(--text-secondary)' }}>使用浏览器原生语音识别</p>
                  </div>
                )}
              </div>
              {!isRecording ? (
                <button onClick={startRecording} disabled={!recognitionSupported} className="btn btn-primary btn-full btn-lg">开始录音</button>
              ) : (
                <button onClick={stopRecording} className="btn btn-secondary btn-full btn-lg">停止录音</button>
              )}
              {transcription && <button onClick={clearAll} className="btn btn-ghost btn-full">清空</button>}
              <div style={{ padding: '16px', background: 'var(--bg-secondary)', borderRadius: 'var(--radius-md)' }}>
                <p style={{ fontSize: '13px', color: 'var(--text-secondary)', lineHeight: '1.8' }}>
                  💡 首次使用需要授权麦克风权限 • 建议在安静环境下使用 • 支持普通话识别 • 完全离线，隐私安全
                </p>
              </div>
            </div>
          )}
        </div>

        {/* 右侧 - 转录结果 */}
        <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <h3 style={{ fontSize: '16px', fontWeight: '600' }}>转录结果</h3>
            {transcription && !isRecording && !isTranscribing && (
              <button onClick={copyTranscription} className="btn btn-ghost" style={{ padding: '6px 12px' }}>📋 复制全部</button>
            )}
          </div>
          {taskError && (
            <div className="alert alert-error">
              <p style={{ fontWeight: '500' }}>转写失败</p>
              <p style={{ fontSize: '13px', marginTop: '4px' }}>{taskError}</p>
              {taskId && <p style={{ fontSize: '12px', marginTop: '4px', color: 'var(--text-tertiary)' }}>任务 ID: {taskId}</p>}
            </div>
          )}
          {transcription ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              {timestamps && timestamps.length > 0 ? (
                // 文件转写：以时间轴分段为主视图（Whisper 中文长音频整段拼接易丢标点，
                // 分段独立、每段带时间戳更清晰；用户用复制按钮一键拼接所有段落）
                <div style={{ padding: '16px', border: '1px solid var(--border-color)', borderRadius: 'var(--radius-md)', background: 'var(--bg-secondary)', minHeight: '240px', maxHeight: '500px', overflow: 'auto' }}>
                  {timestamps.map((line, idx) => (
                    <div key={idx} style={{ display: 'flex', gap: '12px', padding: '8px 0', fontSize: '14px', lineHeight: '1.7', borderBottom: idx < timestamps.length - 1 ? '1px solid var(--border-color)' : 'none' }}>
                      <span style={{ color: 'var(--primary)', fontFamily: 'monospace', flexShrink: 0, fontSize: '12px', paddingTop: '2px' }}>[{line.time}]</span>
                      <span style={{ color: 'var(--text-primary)', flex: 1 }}>{line.text}</span>
                    </div>
                  ))}
                </div>
              ) : (
                // 实时录音：浏览器原生识别不返回 segments，仍展示纯文本
                <div style={{ padding: '16px', border: '1px solid var(--border-color)', borderRadius: 'var(--radius-md)', background: 'var(--bg-secondary)', minHeight: '240px', maxHeight: '500px', overflow: 'auto', fontSize: '14px', lineHeight: '1.8', whiteSpace: 'pre-wrap' }}>
                  {transcription}
                </div>
              )}
              {outline && outline.length > 0 && (
                <div style={{ padding: '12px 16px', border: '1px solid var(--border-color)', borderRadius: 'var(--radius-md)', background: 'var(--bg-secondary)' }}>
                  <p style={{ fontSize: '13px', fontWeight: '500', marginBottom: '8px', color: 'var(--text-secondary)' }}>大纲</p>
                  {outline.map((item, idx) => (
                    <div key={idx} style={{ padding: '6px 0', fontSize: '13px', lineHeight: '1.6' }}>
                      <p style={{ fontWeight: '500', color: 'var(--text-primary)' }}>
                        <span style={{ color: 'var(--primary)', marginRight: '6px' }}>{item.section}</span>
                        {item.title}
                      </p>
                      <p style={{ color: 'var(--text-secondary)', marginTop: '2px' }}>{item.summary}</p>
                    </div>
                  ))}
                </div>
              )}
              {taskId && (
                <p style={{ fontSize: '12px', color: 'var(--text-tertiary)' }}>任务 ID: {taskId}</p>
              )}
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '64px 24px', color: 'var(--text-tertiary)', minHeight: '400px' }}>
              <div style={{ fontSize: '48px', marginBottom: '16px' }}>🎙️</div>
              <p style={{ fontSize: '14px' }}>{mode === 'file' ? '上传音频文件开始转录' : '开始录音，文字将在这里实时显示'}</p>
            </div>
          )}
        </div>
      </div>

      <style>{`
        @keyframes bounce {
          0%, 100% { transform: translateY(0); }
          50% { transform: translateY(-8px); }
        }
      `}</style>
    </div>
  )
}

export default TranscriptionPage
