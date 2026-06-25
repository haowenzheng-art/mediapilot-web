import { pipeline, env } from '@xenova/transformers'

env.allowLocalModels = false
env.useBrowserCache = true

class WhisperService {
  constructor() {
    this.pipeline = null
    this.isLoading = false
    this.modelProgress = 0
  }

  async loadModel(onProgress) {
    if (this.pipeline) {
      return this.pipeline
    }

    if (this.isLoading) {
      return new Promise((resolve) => {
        const checkInterval = setInterval(() => {
          if (this.pipeline) {
            clearInterval(checkInterval)
            resolve(this.pipeline)
          }
        }, 100)
      })
    }

    this.isLoading = true

    try {
      this.pipeline = await pipeline('automatic-speech-recognition', 'Xenova/whisper-tiny.en', {
        progress_callback: (progress) => {
          if (onProgress && progress.status === 'downloading') {
            this.modelProgress = progress.progress
            onProgress(progress)
          }
        }
      })

      return this.pipeline
    } catch (error) {
      console.error('Failed to load Whisper model:', error)
      throw error
    } finally {
      this.isLoading = false
    }
  }

  async transcribe(audioData, options = {}) {
    const pipe = await this.loadModel(options.onProgress)

    try {
      const result = await pipe(audioData, {
        language: options.language || 'chinese',
        task: options.task || 'transcribe',
        return_timestamps: options.returnTimestamps || false,
        chunk_length_s: options.chunkLength || 30,
        stride_length_s: options.strideLength || 5,
      })

      return result
    } catch (error) {
      console.error('Transcription error:', error)
      throw error
    }
  }

  async transcribeFile(file, options = {}) {
    const pipe = await this.loadModel(options.onProgress)

    try {
      const audioContext = new (window.AudioContext || window.webkitAudioContext)()
      const arrayBuffer = await file.arrayBuffer()
      const audioBuffer = await audioContext.decodeAudioData(arrayBuffer)

      const audioData = this.audioBufferToFloat32Array(audioBuffer)

      const result = await pipe(audioData, {
        language: options.language || 'chinese',
        task: options.task || 'transcribe',
        return_timestamps: options.returnTimestamps || false,
        chunk_length_s: options.chunkLength || 30,
        stride_length_s: options.strideLength || 5,
        sampling_rate: audioBuffer.sampleRate,
      })

      return result
    } catch (error) {
      console.error('File transcription error:', error)
      throw error
    }
  }

  audioBufferToFloat32Array(audioBuffer) {
    const channelData = audioBuffer.getChannelData(0)
    const length = channelData.length
    const float32Array = new Float32Array(length)

    for (let i = 0; i < length; i++) {
      float32Array[i] = channelData[i]
    }

    return float32Array
  }

  getModelProgress() {
    return this.modelProgress
  }

  isModelLoaded() {
    return this.pipeline !== null
  }
}

export const whisperService = new WhisperService()
