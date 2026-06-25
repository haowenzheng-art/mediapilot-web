import express from 'express'
import cors from 'cors'
import path from 'path'
import { createServer as createViteServer } from 'vite'
import { fileURLToPath } from 'url'

const __filename = fileURLToPath(import.meta.url)
const __dirname = path.dirname(__filename)

const PORT = process.env.PORT || 3000
const isDev = process.env.NODE_ENV !== 'production'

const app = express()

// 中间件
app.use(cors())
app.use(express.json({ limit: '10mb' }))

// 简单的内存数据库（生产环境应该用真实数据库）
const dataStore = {
  platformData: [],
  history: []
}

// ===== API 接口 =====

// 健康检查
app.get('/api/health', (req, res) => {
  res.json({ status: 'ok', timestamp: new Date().toISOString() })
})

// 插件状态检查
app.get('/api/extension/status', (req, res) => {
  res.json({ status: 'ok', message: 'MediaPilot is running' })
})

// 接收插件数据
app.post('/api/extension/data', (req, res) => {
  try {
    const data = req.body

    // 添加时间戳
    const record = {
      ...data,
      id: Date.now(),
      savedAt: new Date().toISOString()
    }

    // 保存到数据存储
    dataStore.platformData.unshift(record)

    // 只保留最近 1000 条
    if (dataStore.platformData.length > 1000) {
      dataStore.platformData = dataStore.platformData.slice(0, 1000)
    }

    // 同步到 localStorage (前端可以读取)
    res.json({
      success: true,
      message: '数据已保存',
      id: record.id
    })
  } catch (error) {
    console.error('保存数据错误:', error)
    res.status(500).json({
      success: false,
      error: error.message
    })
  }
})

// 获取所有平台数据
app.get('/api/platform-data', (req, res) => {
  res.json({
    success: true,
    data: dataStore.platformData
  })
})

// 获取单条数据
app.get('/api/platform-data/:id', (req, res) => {
  const record = dataStore.platformData.find(
    item => item.id === parseInt(req.params.id)
  )

  if (record) {
    res.json({ success: true, data: record })
  } else {
    res.status(404).json({ success: false, error: '数据不存在' })
  }
})

// 删除数据
app.delete('/api/platform-data/:id', (req, res) => {
  const index = dataStore.platformData.findIndex(
    item => item.id === parseInt(req.params.id)
  )

  if (index !== -1) {
    dataStore.platformData.splice(index, 1)
    res.json({ success: true, message: '数据已删除' })
  } else {
    res.status(404).json({ success: false, error: '数据不存在' })
  }
})

// 清空所有数据
app.delete('/api/platform-data', (req, res) => {
  dataStore.platformData = []
  res.json({ success: true, message: '所有数据已清空' })
})

// 保存历史记录
app.post('/api/history', (req, res) => {
  try {
    const { type, data } = req.body

    const record = {
      id: Date.now(),
      type,
      data,
      timestamp: new Date().toISOString()
    }

    dataStore.history.unshift(record)

    if (dataStore.history.length > 500) {
      dataStore.history = dataStore.history.slice(0, 500)
    }

    res.json({ success: true, id: record.id })
  } catch (error) {
    console.error('保存历史错误:', error)
    res.status(500).json({ success: false, error: error.message })
  }
})

// 获取历史记录
app.get('/api/history', (req, res) => {
  const { type } = req.query

  let data = dataStore.history
  if (type) {
    data = data.filter(item => item.type === type)
  }

  res.json({ success: true, data })
})

// ===== 前端服务 =====

if (isDev) {
  // 开发环境：使用 Vite 开发服务器
  let viteServer = null

  const startVite = async () => {
    viteServer = await createViteServer({
      server: {
        middlewareMode: true
      },
      appType: 'spa'
    })

    app.use(viteServer.middlewares)

    // 启动服务器
    app.listen(PORT, () => {
      console.log(`\n🚀 MediaPilot 服务器已启动`)
      console.log(`📱 前端: http://localhost:${PORT}`)
      console.log(`🔌 API: http://localhost:${PORT}/api`)
      console.log(`\n按 Ctrl+C 停止服务器\n`)
    })
  }

  startVite().catch(console.error)
} else {
  // 生产环境：提供静态文件
  app.use(express.static(path.join(__dirname, 'dist')))

  // SPA 路由支持
  app.get('*', (req, res) => {
    res.sendFile(path.join(__dirname, 'dist/index.html'))
  })
}

// 优雅关闭
process.on('SIGTERM', () => {
  console.log('\n👋 正在关闭服务器...')
  process.exit(0)
})

process.on('SIGINT', () => {
  console.log('\n👋 正在关闭服务器...')
  process.exit(0)
})
