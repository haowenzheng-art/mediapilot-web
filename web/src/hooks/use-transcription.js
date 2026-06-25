import { useState, useRef, useEffect, useCallback } from 'react'
import { uploadMedia, pollMediaTask } from '../services/media'

const ERROR_MESSAGES = {
  'not-allowed': '麦克风权限被拒绝，请在浏览器设置中允许麦克风访问',
  'no-speech': '没有检测到语音',
  'audio-capture': '无法获取音频输入',
  'network': '网络错误',
  'aborted': '识别已中止',
}

export function useTranscription() {
  const [mode, setMode] = useState('file')
  const [audioFile, setAudioFile] = useState(null)
  const [transcription, setTranscription] = useState('')
  const [timestamps, setTimestamps] = useState([])
  const [outline, setOutline] = useState([])
  const [isTranscribing, setIsTranscribing] = useState(false)
  const [isRecording, setIsRecording] = useState(false)
  const [progress, setProgress] = useState(0)
  const [taskError, setTaskError] = useState('')
  const [taskId, setTaskId] = useState(null)
  const [recognitionSupported, setRecognitionSupported] = useState(true)
  const [recognitionError, setRecognitionError] = useState('')
  const fileInputRef = useRef(null)
  const recognitionRef = useRef(null)
  const finalTranscriptRef = useRef('')
  const interimTranscriptRef = useRef('')
  // 用户希望持续录音（区别于 SpeechRecognition 自身的 onend，浏览器静音几秒会自动停）
  const wantRecordingRef = useRef(false)

  // 初始化浏览器语音识别（realtime 模式用）—— 实例仅创建一次
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
    }

    recognition.onresult = (event) => {
      let interim = ''
      let final = ''
      for (let i = event.resultIndex; i < event.results.length; i++) {
        const transcript = event.results[i][0].transcript
        if (event.results[i].isFinal) final += transcript
        else interim += transcript
      }
      finalTranscriptRef.current += final
      interimTranscriptRef.current = interim
      setTranscription(finalTranscriptRef.current + interimTranscriptRef.current)
    }

    recognition.onerror = (event) => {
      setRecognitionError(ERROR_MESSAGES[event.error] || `语音识别错误: ${event.error}`)
      // aborted/no-speech 是常态，不要因此切掉用户意图
      if (event.error !== 'no-speech' && event.error !== 'aborted') {
        wantRecordingRef.current = false
        setIsTranscribing(false)
      }
      setIsRecording(false)
    }

    recognition.onend = () => {
      setIsRecording(false)
      // 只有用户仍希望录音时才自动续接
      if (wantRecordingRef.current) {
        try { recognition.start() } catch (e) {}
      }
    }

    recognitionRef.current = recognition

    return () => {
      wantRecordingRef.current = false
      try { recognition.stop() } catch (e) {}
    }
  }, [])

  const handleFileChange = useCallback((e) => {
    const file = e.target.files[0]
    if (file) {
      setAudioFile(file)
      setTaskError('')
      setTranscription('')
      setTimestamps([])
      setOutline([])
      setProgress(0)
      setTaskId(null)
    }
  }, [])

  const handleDrop = useCallback((e) => {
    e.preventDefault()
    const file = e.dataTransfer.files[0]
    if (file && (file.type.startsWith('audio/') || file.type.startsWith('video/'))) {
      setAudioFile(file)
      setTaskError('')
      setTranscription('')
      setTimestamps([])
      setOutline([])
      setProgress(0)
      setTaskId(null)
    }
  }, [])

  // 真实文件转写：上传 → 轮询任务状态
  const transcribeFile = useCallback(async () => {
    if (!audioFile) return
    setIsTranscribing(true)
    setProgress(0)
    setTranscription('')
    setTimestamps([])
    setOutline([])
    setTaskError('')
    setTaskId(null)

    try {
      const uploadResult = await uploadMedia(audioFile)
      const newTaskId = uploadResult.task_id
      setTaskId(newTaskId)
      setProgress(5)

      const finalData = await pollMediaTask(newTaskId, {
        onProgress: (data, attempt) => {
          // processing 阶段给一个伪进度感
          const base = 10
          const max = 90
          const step = Math.min(max, base + attempt * 3)
          setProgress(step)
        },
      })

      setTranscription(finalData.transcript || '')
      setTimestamps(finalData.timestamps || [])
      setOutline(finalData.outline || [])
      setProgress(100)
    } catch (err) {
      setTaskError(err.message || '转写失败')
      setProgress(0)
    } finally {
      setIsTranscribing(false)
    }
  }, [audioFile])

  const startRecording = useCallback(async () => {
    if (!recognitionRef.current) {
      setRecognitionError('您的浏览器不支持语音识别，请使用Chrome或Edge浏览器')
      return
    }
    try {
      setTranscription('')
      setTaskError('')
      finalTranscriptRef.current = ''
      interimTranscriptRef.current = ''
      wantRecordingRef.current = true
      setIsTranscribing(true)
      recognitionRef.current.start()
    } catch (e) {
      wantRecordingRef.current = false
      setIsTranscribing(false)
      setRecognitionError('启动语音识别失败，请刷新页面重试')
    }
  }, [])

  const stopRecording = useCallback(() => {
    // 先清除意图，避免 onend 自动 restart
    wantRecordingRef.current = false
    setIsTranscribing(false)
    setIsRecording(false)
    try { recognitionRef.current?.stop() } catch (e) {}
    try { recognitionRef.current?.abort() } catch (e) {}
  }, [])

  const clearAll = useCallback(() => {
    setAudioFile(null)
    setTranscription('')
    setTimestamps([])
    setOutline([])
    setProgress(0)
    setTaskError('')
    setTaskId(null)
    setRecognitionError('')
    if (fileInputRef.current) fileInputRef.current.value = ''
  }, [])

  const copyTranscription = useCallback(() => {
    // 优先复制时间轴拼接版（Whisper 中文长音频整段拼接易丢标点，
    // 分段独立、各带时间戳，复制时按 [mm:ss] 文本 一行一段更准确）
    let text = ''
    if (timestamps && timestamps.length > 0) {
      text = timestamps.map(t => `[${t.time}] ${t.text}`).join('\n')
    } else {
      text = transcription
    }
    if (text) {
      navigator.clipboard.writeText(text)
      alert('已复制到剪贴板')
    }
  }, [transcription, timestamps])

  const switchMode = useCallback((newMode) => {
    setMode(newMode)
    setTranscription('')
    setTimestamps([])
    setOutline([])
    setTaskError('')
    setTaskId(null)
  }, [])

  return {
    mode, switchMode,
    audioFile, handleFileChange, handleDrop, fileInputRef,
    transcription, timestamps, outline, taskId, taskError,
    isTranscribing, isRecording, progress,
    recognitionSupported, recognitionError,
    transcribeFile, startRecording, stopRecording, clearAll, copyTranscription,
  }
}
