import { useState, useCallback } from 'react'
import { useRequest } from './use-request'
import { videoService } from '../services/video'
import { getCurrentUser } from '../services/auth'

const PLATFORMS = [
  { id: 'bilibili', name: 'B站', icon: '📺' },
]

export function useVideoAnalysis() {
  const [videoUrl, setVideoUrl] = useState('')
  const [platform, setPlatform] = useState('bilibili')
  const [videoInfo, setVideoInfo] = useState(null)
  const [transcript, setTranscript] = useState(null)
  const { loading: isLoadingInfo, error: fetchError, run: runFetch } = useRequest(videoService.fetchVideo)
  const { loading: isLoadingTranscript, error: transcriptError, run: runTranscript } = useRequest(videoService.getTranscript)
  const currentUser = getCurrentUser()

  const error = fetchError || transcriptError

  const fetchVideo = useCallback(() => {
    if (!videoUrl.trim()) return
    runFetch(videoUrl, platform).then(data => {
      setVideoInfo(data)
      setTranscript(null)
    }).catch(() => {})
  }, [videoUrl, platform, runFetch])

  const getTranscript = useCallback(() => {
    if (!videoInfo?.video_id) return
    runTranscript(videoInfo.video_id).then(data => {
      setTranscript(data)
    }).catch(() => {})
  }, [videoInfo, runTranscript])

  return {
    videoUrl, setVideoUrl,
    platform, setPlatform,
    videoInfo, transcript,
    isLoadingInfo, isLoadingTranscript, error,
    fetchVideo, getTranscript,
    currentUser, platforms: PLATFORMS,
  }
}
