/**
 * 视频分析服务
 */
import { request } from './api'

export const videoService = {
  async fetchVideo(url, platform) {
    return request('/api/v1/video/fetch', {
      method: 'POST',
      body: JSON.stringify({
        video_url: url,
        platform: platform || 'douyin',
      }),
    }).then(result => result.data)
  },

  async getTranscript(videoId) {
    return request('/api/v1/video/transcript', {
      method: 'POST',
      body: JSON.stringify({ video_id: videoId }),
    }).then(result => result.data)
  },
}
