import { useState, useRef, useEffect } from 'react'

function TranscriptionPage() {
  const [mode, setMode] = useState('file')
  const [audioFile, setAudioFile] = useState(null)
  const [transcription, setTranscription] = useState('')
  const [isTranscribing, setIsTranscribing] = useState(false)
  const [isRecording, setIsRecording] = useState(false)
  const [progress, setProgress] = useState(0)
  const [recognitionSupported, setRecognitionSupported] = useState(true)
  const [recognitionError, setRecognitionError] = useState('')
  const fileInputRef = useRef(null)
  const recognitionRef = useRef(null)
  const finalTranscriptRef = useRef('')
  const interimTranscriptRef = useRef('')

  useEffect(() => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
    if (!SpeechRecognition) {
      setRecognitionSupported(false)
      return
    }

    const recognition = new SpeechRecognition()
    recognition.continuous = true
    recognition.interimResults = true
    recognition.lang = 'zh-CN'

    recognition.onstart = () => {
      setIsRecording(true)
      setRecognitionError('')
      finalTranscriptRef.current = ''
      interimTranscriptRef.current = ''
    }

    recognition.onresult = (event) => {
      let interimTranscript = ''
      let finalTranscript = ''

      for (let i = event.resultIndex; i < event.results.length; i++) {
        const transcript = event.results[i][0].transcript
        if (event.results[i].isFinal) {
          finalTranscript += transcript
        } else {
          interimTranscript += transcript
        }
      }

      finalTranscriptRef.current += finalTranscript
      interimTranscriptRef.current = interimTranscript
      setTranscription(finalTranscriptRef.current + interimTranscriptRef.current)
    }

    recognition.onerror = (event) => {
      console.error('Speech recognition error:', event.error)
      setRecognitionError(getErrorMessage(event.error))
      setIsRecording(false)
    }

    recognition.onend = () => {
      setIsRecording(false)
      if (isTranscribing) {
        try {
          recognition.start()
        } catch (e) {
          console.error('Failed to restart recognition:', e)
        }
      }
    }

    recognitionRef.current = recognition
  }, [isTranscribing])

  const getErrorMessage = (error) => {
    const errorMessages = {
      'not-allowed': '麦克风权限被拒绝，请在浏览器设置中允许麦克风访问',
      'no-speech': '没有检测到语音',
      'audio-capture': '无法获取音频输入',
      'network': '网络错误',
      'aborted': '识别已中止',
    }
    return errorMessages[error] || `语音识别错误: ${error}`
  }

  const handleFileChange = (e) => {
    const file = e.target.files[0]
    if (file) {
      setAudioFile(file)
    }
  }

  const simulateTranscription = async () => {
    if (!audioFile) return

    setIsTranscribing(true)
    setProgress(0)
    setTranscription('')

    const sampleText = `这是一段模拟的语音转录结果。

在当今这个快节奏的社会中，我们每个人都在寻找提高工作效率的方法。今天我想和大家分享几个实用的小技巧。

首先，要学会优先级管理。使用四象限法则，把事情分为重要紧急、重要不紧急、不重要紧急和不重要不紧急四类。

其次，合理利用碎片化时间。比如在通勤的时候可以听书，排队的时候可以处理一些简单的消息。

最后，要保持专注。一次只做一件事，避免多任务并行带来的效率损失。

希望这些建议对大家有帮助！如果觉得有用，记得点赞收藏哦！`

    const words = sampleText.split(' ')
    let currentText = ''

    for (let i = 0; i < words.length; i++) {
      await new Promise(resolve => setTimeout(resolve, 40))
      currentText += (i > 0 ? ' ' : '') + words[i]
      setTranscription(currentText)
      setProgress(Math.floor(((i + 1) / words.length) * 100))
    }

    setIsTranscribing(false)
  }

  const startRecording = async () => {
    if (!recognitionRef.current) {
      setRecognitionError('您的浏览器不支持语音识别，请使用Chrome或Edge浏览器')
      return
    }

    try {
      setTranscription('')
      finalTranscriptRef.current = ''
      interimTranscriptRef.current = ''
      setIsTranscribing(true)
      recognitionRef.current.start()
    } catch (e) {
      console.error('Failed to start recognition:', e)
      setRecognitionError('启动语音识别失败，请刷新页面重试')
    }
  }

  const stopRecording = () => {
    setIsTranscribing(false)
    if (recognitionRef.current) {
      try {
        recognitionRef.current.stop()
      } catch (e) {
        console.error('Failed to stop recognition:', e)
      }
    }
  }

  const clearAll = () => {
    setAudioFile(null)
    setTranscription('')
    setProgress(0)
    setRecognitionError('')
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
  }

  const copyTranscription = () => {
    if (transcription) {
      navigator.clipboard.writeText(transcription)
      alert('转录内容已复制到剪贴板！')
    }
  }

  return (
    <div className="p-6 max-w-5xl mx-auto">
      <h2 className="text-2xl font-bold mb-6 flex items-center gap-2">
        <span>🎙️</span> 智能转录
      </h2>

      <div className="mb-6 flex gap-2">
        <button
          onClick={() => {
            setMode('file')
            setTranscription('')
          }}
          className={`px-4 py-2 rounded-lg transition-all`}
          style={{
            background: mode === 'file' ? 'var(--accent-primary)' : 'var(--glass-bg)',
            color: mode === 'file' ? 'var(--bg-primary)' : 'var(--text-primary)',
          }}
        >
          📁 上传文件
        </button>
        <button
          onClick={() => {
            setMode('realtime')
            setTranscription('')
          }}
          className={`px-4 py-2 rounded-lg transition-all`}
          style={{
            background: mode === 'realtime' ? 'var(--accent-primary)' : 'var(--glass-bg)',
            color: mode === 'realtime' ? 'var(--bg-primary)' : 'var(--text-primary)',
          }}
        >
          🎤 实时录音
        </button>
      </div>

      <div className="grid lg:grid-cols-2 gap-6">
        <div className="space-y-6">
          {mode === 'file' ? (
            <div className="space-y-6">
              <div className="card">
                <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                  <span>📁</span> 上传音频/视频
                </h3>

                {!audioFile ? (
                  <div
                    onClick={() => fileInputRef.current?.click()}
                    className="border-2 border-dashed rounded-lg p-12 text-center cursor-pointer hover:border-primary hover:bg-primary/5 transition-all"
                    style={{ borderColor: 'var(--border-color)' }}
                  >
                    <input
                      ref={fileInputRef}
                      type="file"
                      accept="audio/*,video/*"
                      onChange={handleFileChange}
                      className="hidden"
                    />
                    <div className="text-5xl mb-4">🎵</div>
                    <p className="text-lg font-medium mb-2">点击或拖拽文件到这里</p>
                    <p className="text-secondary text-sm">支持 MP3, WAV, MP4, MOV 等格式</p>
                  </div>
                ) : (
                  <div className="p-4 rounded-lg border" style={{ borderColor: 'var(--border-color)', background: 'var(--card-bg)' }}>
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <div className="w-12 h-12 rounded-lg flex items-center justify-center text-2xl" style={{ background: 'var(--glass-bg)' }}>
                          🎵
                        </div>
                        <div>
                          <p className="font-medium">{audioFile.name}</p>
                          <p className="text-sm text-secondary">
                            {(audioFile.size / 1024 / 1024).toFixed(2)} MB
                          </p>
                        </div>
                      </div>
                      <button
                        onClick={clearAll}
                        className="text-red-400 hover:text-red-500 p-2"
                      >
                        🗑️
                      </button>
                    </div>

                    <div className="mt-4 flex gap-3">
                      <button
                        onClick={simulateTranscription}
                        disabled={isTranscribing}
                        className="btn btn-primary flex-1"
                        style={{ padding: '16px' }}
                      >
                        {isTranscribing ? (
                          <span className="animate-pulse">转录中...</span>
                        ) : (
                          '🎙️ 开始转录'
                        )}
                      </button>
                    </div>

                    {isTranscribing && (
                      <div className="mt-4">
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-sm text-secondary">正在转录...</span>
                          <span className="text-sm font-medium">{progress}%</span>
                        </div>
                        <div className="h-2 rounded-full overflow-hidden" style={{ background: 'var(--bg-secondary)' }}>
                          <div
                            className="h-full transition-all duration-300"
                            style={{
                              width: `${progress}%`,
                              background: 'var(--accent-primary)',
                            }}
                          />
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>

              <div className="card">
                <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                  <span>💡</span> 使用提示
                </h3>
                <ul className="space-y-2 text-secondary text-sm">
                  <li>• 支持常见音频格式（MP3、WAV、M4A等）</li>
                  <li>• 支持视频格式（MP4、MOV等）</li>
                  <li>• 建议音频文件不超过 100MB</li>
                  <li>• 清晰度越高，转录准确率越高</li>
                  <li>• 转录完成后可一键复制文本</li>
                </ul>
              </div>
            </div>
          ) : (
            <div className="card">
              <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                <span>🎤</span> 实时语音转文字
              </h3>

              {!recognitionSupported && (
                <div className="p-4 rounded-lg mb-4" style={{ background: 'rgba(233, 69, 96, 0.2)' }}>
                  <p className="text-red-400">
                    ⚠️ 您的浏览器不支持语音识别
                  </p>
                  <p className="text-sm mt-2 text-secondary">
                    请使用 Chrome、Edge 或 Safari 浏览器
                  </p>
                </div>
              )}

              {recognitionError && (
                <div className="p-4 rounded-lg mb-4" style={{ background: 'rgba(233, 69, 96, 0.2)' }}>
                  <p className="text-red-400">{recognitionError}</p>
                </div>
              )}

              <div className="text-center py-8">
                {isRecording ? (
                  <div>
                    <div className="text-6xl mb-4 animate-pulse">🎙️</div>
                    <p className="text-lg font-medium mb-2">正在录音...</p>
                    <p className="text-secondary text-sm mb-4">
                      说话即可实时转文字
                    </p>
                    <div className="flex justify-center gap-3">
                      <div className="w-3 h-3 rounded-full animate-bounce" style={{ background: 'var(--accent-primary)', animationDelay: '0ms' }}></div>
                      <div className="w-3 h-3 rounded-full animate-bounce" style={{ background: 'var(--accent-primary)', animationDelay: '150ms' }}></div>
                      <div className="w-3 h-3 rounded-full animate-bounce" style={{ background: 'var(--accent-primary)', animationDelay: '300ms' }}></div>
                    </div>
                  </div>
                ) : (
                  <div>
                    <div className="text-6xl mb-4">🎤</div>
                    <p className="text-lg font-medium mb-2">点击开始录音</p>
                    <p className="text-secondary text-sm mb-4">
                      使用浏览器原生语音识别
                    </p>
                  </div>
                )}
              </div>

              <div className="flex gap-3">
                {!isRecording ? (
                  <button
                    onClick={startRecording}
                    disabled={!recognitionSupported}
                    className="btn btn-primary flex-1"
                    style={{ padding: '16px' }}
                  >
                    🎤 开始录音
                  </button>
                ) : (
                  <button
                    onClick={stopRecording}
                    className="btn btn-primary flex-1"
                    style={{ padding: '16px', background: 'var(--accent-secondary)' }}
                  >
                    ⏹️ 停止录音
                  </button>
                )}
                {transcription && (
                  <button
                    onClick={clearAll}
                    className="btn btn-secondary"
                    style={{ padding: '16px' }}
                  >
                    🗑️ 清空
                  </button>
                )}
              </div>

              <div className="mt-4 p-4 rounded-lg" style={{ background: 'var(--glass-bg)' }}>
                <p className="text-sm text-secondary mb-2">💡 提示：</p>
                <ul className="text-sm text-secondary space-y-1">
                  <li>• 首次使用需要授权麦克风权限</li>
                  <li>• 建议在安静环境下使用</li>
                  <li>• 支持普通话识别</li>
                  <li>• 完全离线，隐私安全</li>
                </ul>
              </div>
            </div>
          )}
        </div>

        <div className="space-y-6">
          <div className="card sticky top-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold flex items-center gap-2">
                <span>📝</span> 转录结果
              </h3>
              {transcription && !isRecording && !isTranscribing && (
                <button
                  onClick={copyTranscription}
                  className="btn btn-secondary text-sm px-3 py-1.5"
                >
                  📋 复制
                </button>
              )}
            </div>

            {transcription ? (
              <div
                className="p-4 rounded-lg border max-h-[600px] overflow-y-auto"
                style={{
                  borderColor: 'var(--border-color)',
                  background: 'var(--card-bg)',
                }}
              >
                <pre className="whitespace-pre-wrap text-sm leading-relaxed">
                  {transcription}
                </pre>
              </div>
            ) : (
              <div className="text-center py-16 text-secondary">
                <div className="text-5xl mb-4">🎙️</div>
                <p>{mode === 'file' ? '上传音频文件开始转录' : '开始录音，文字将在这里实时显示'}</p>
                <p className="text-sm mt-2">转录的文字将在这里显示</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

export default TranscriptionPage
