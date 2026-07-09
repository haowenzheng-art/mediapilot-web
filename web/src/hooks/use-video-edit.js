import { useState, useRef, useCallback, useEffect } from 'react'
import { uploadVideoEdit, pollVideoEditTask, getVideoEditSegments, downloadVideoEditFile, listVideoEditTasks, getVideoEditTask, reapplyVideoEdit } from '../services/video-edit'

export function useVideoEdit() {
  const [videoFile, setVideoFile] = useState(null)
  const [taskId, setTaskId] = useState(null)
  const [status, setStatus] = useState('idle')  // idle, uploading, processing, completed, failed
  const [progress, setProgress] = useState(0)
  const [result, setResult] = useState(null)
  const [segments, setSegments] = useState(null)
  const [error, setError] = useState(null)
  const [strength, setStrength] = useState('medium')  // conservative / medium / aggressive
  // B1: 历史任务列表
  const [history, setHistory] = useState([])
  const [historyLoading, setHistoryLoading] = useState(false)
  // B3: 用户微调 segments 状态
  // segments_state 记录每个 segment 当前的 kept/removed 状态，初始 = AI 决策
  // dirty = true 表示有未应用的修改
  const [segmentsState, setSegmentsState] = useState({ kept: [], removed: [] })
  const [reapplying, setReapplying] = useState(false)
  const fileInputRef = useRef(null)

  const handleFileChange = useCallback((e) => {
    const file = e.target.files[0]
    if (file) {
      setVideoFile(file)
      setError(null)
      setResult(null)
      setSegments(null)
      setTaskId(null)
      setStatus('idle')
      setProgress(0)
    }
  }, [])

  const handleDrop = useCallback((e) => {
    e.preventDefault()
    const file = e.dataTransfer.files[0]
    if (file && file.type.startsWith('video/')) {
      setVideoFile(file)
      setError(null)
      setResult(null)
      setSegments(null)
      setTaskId(null)
      setStatus('idle')
      setProgress(0)
    }
  }, [])

  const startEdit = useCallback(async () => {
    if (!videoFile) return
    setStatus('uploading')
    setProgress(0)
    setError(null)
    setResult(null)
    setSegments(null)
    try {
      const uploadResult = await uploadVideoEdit(videoFile, { strength })
      const newTaskId = uploadResult.task_id
      setTaskId(newTaskId)
      setStatus('processing')

      const finalData = await pollVideoEditTask(newTaskId, {
        onProgress: (data, attempt) => {
          // 5%-90% 模拟进度
          const step = Math.min(90, 5 + attempt * 2)
          setProgress(step)
        },
      })

      setResult(finalData)
      setStatus('completed')
      setProgress(100)

      // 单独拉取一次片段详情
      try {
        const segs = await getVideoEditSegments(newTaskId)
        setSegments(segs)
        // B3: 初始化 segmentsState（用 AI 原始决策）
        setSegmentsState({
          kept: (segs.kept_segments || []).map(s => [s.start, s.end]),
          removed: (segs.removed_segments || []).map(s => ({
            start: s.start, end: s.end, text: s.text || '', reason: s.reason || '',
          })),
        })
      } catch (e) {
        // 拉取失败不影响主结果，result 里也有
        console.warn('拉取片段详情失败:', e)
      }
    } catch (err) {
      setError(err.message || '视频剪辑失败')
      setStatus('failed')
      setProgress(0)
    }
  }, [videoFile, strength])

  const clearAll = useCallback(() => {
    setVideoFile(null)
    setTaskId(null)
    setStatus('idle')
    setProgress(0)
    setResult(null)
    setSegments(null)
    setError(null)
    if (fileInputRef.current) fileInputRef.current.value = ''
  }, [])

  const downloadVideo = useCallback(async () => {
    if (!taskId) return
    const filename = `edited_${result?.source_video_name || taskId}.mp4`
    try {
      await downloadVideoEditFile(taskId, 'video', filename)
    } catch (e) {
      setError(e.message)
    }
  }, [taskId, result])

  const downloadSubtitle = useCallback(async () => {
    if (!taskId) return
    const ext = result?.subtitle_format || 'srt'
    const filename = `subtitle_${taskId}.${ext}`
    try {
      await downloadVideoEditFile(taskId, 'subtitle', filename)
    } catch (e) {
      setError(e.message)
    }
  }, [taskId, result])

  // B1: 加载历史任务
  const loadHistory = useCallback(async () => {
    setHistoryLoading(true)
    try {
      const data = await listVideoEditTasks(0, 20)
      setHistory(data.tasks || [])
    } catch (e) {
      console.warn('加载剪辑历史失败:', e)
    } finally {
      setHistoryLoading(false)
    }
  }, [])

  // 首次 mount 自动加载
  useEffect(() => {
    loadHistory()
  }, [loadHistory])

  // B1: 重看历史任务的结果（拉取 task 详情）
  const viewHistoryTask = useCallback(async (historyTaskId) => {
    try {
      setStatus('processing')
      setError(null)
      setResult(null)
      setSegments(null)
      setTaskId(historyTaskId)
      const data = await getVideoEditTask(historyTaskId)
      if (data.status === 'completed') {
        setResult(data)
        setStatus('completed')
        setProgress(100)
      } else if (data.status === 'failed') {
        setError(data.error || '历史任务失败')
        setStatus('failed')
      } else {
        // 还在跑 — 拉取最新状态
        const final = await pollVideoEditTask(historyTaskId, {})
        setResult(final)
        setStatus('completed')
        setProgress(100)
      }
      // 拉取 segments
      try {
        const segs = await getVideoEditSegments(historyTaskId)
        setSegments(segs)
        // B3: 初始化 segmentsState
        setSegmentsState({
          kept: (segs.kept_segments || []).map(s => [s.start, s.end]),
          removed: (segs.removed_segments || []).map(s => ({
            start: s.start,
            end: s.end,
            text: s.text || '',
            reason: s.reason || '',
          })),
        })
      } catch (e) { /* ignore */ }
    } catch (e) {
      setError(e.message || '加载历史任务失败')
      setStatus('failed')
    }
  }, [])

  // B3: 切换单个 segment 的状态（kept ↔ removed）
  const toggleSegment = useCallback((idx, currentState) => {
    setSegmentsState(prev => {
      const kept = [...prev.kept]
      const removed = [...prev.removed]
      if (currentState === 'kept') {
        // kept → removed：移出 kept，加到 removed
        const [s, e] = kept[idx]
        removed.push({ start: s, end: e, text: '', reason: '用户微调：删除' })
        kept.splice(idx, 1)
      } else {
        // removed → kept：移出 removed，加到 kept（按时间排序）
        const seg = removed[idx]
        kept.push([seg.start, seg.end])
        kept.sort((a, b) => a[0] - b[0])
        removed.splice(idx, 1)
      }
      return { kept, removed }
    })
  }, [])

  // B3: 检查是否有未应用的修改
  const isDirty = useCallback(() => {
    if (!result || !segmentsState.kept.length) return false
    const origKept = (result.kept_segments || []).map(s => [s.start, s.end])
    if (origKept.length !== segmentsState.kept.length) return true
    return origKept.some((seg, i) => {
      const cur = segmentsState.kept[i]
      return !cur || Math.abs(seg[0] - cur[0]) > 0.01 || Math.abs(seg[1] - cur[1]) > 0.01
    })
  }, [result, segmentsState])

  // B3: 应用修改并重新生成
  const reapplySegments = useCallback(async () => {
    if (!taskId || !segmentsState.kept.length) return
    setReapplying(true)
    setError(null)
    try {
      await reapplyVideoEdit(taskId, segmentsState.kept)
      // 重新拉取结果
      const data = await getVideoEditTask(taskId)
      setResult(data)
      const segs = await getVideoEditSegments(taskId)
      setSegments(segs)
      setSegmentsState({
        kept: (segs.kept_segments || []).map(s => [s.start, s.end]),
        removed: (segs.removed_segments || []).map(s => ({
          start: s.start, end: s.end, text: s.text || '', reason: s.reason || '',
        })),
      })
    } catch (e) {
      setError(e.message || '应用修改失败')
    } finally {
      setReapplying(false)
    }
  }, [taskId, segmentsState])

  // B3: 重置为 AI 原始决策
  const resetSegments = useCallback(() => {
    if (!result) return
    setSegmentsState({
      kept: (result.kept_segments || []).map(s => [s.start, s.end]),
      removed: (result.removed_segments || []).map(s => ({
        start: s.start, end: s.end, text: s.text || '', reason: s.reason || '',
      })),
    })
  }, [result])

  return {
    videoFile, fileInputRef, handleFileChange, handleDrop,
    taskId, status, progress, result, segments, error,
    strength, setStrength,
    startEdit, clearAll, downloadVideo, downloadSubtitle,
    // B1: 历史任务
    history, historyLoading, loadHistory, viewHistoryTask,
    // B3: 微调 segments
    segmentsState, toggleSegment, isDirty, reapplySegments, reapplying, resetSegments,
  }
}
