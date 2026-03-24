console.log('[MediaPilot Popup] Script starting...')

// 等待 DOM 加载
document.addEventListener('DOMContentLoaded', () => {
  console.log('[MediaPilot Popup] DOM loaded')
  init()
})

function init() {
  console.log('[MediaPilot Popup] init() called')

  // 检查必需的 DOM 元素
  const connectBtn = document.getElementById('connectBtn')
  const captureBtn = document.getElementById('captureBtn')
  const sendBtn = document.getElementById('sendBtn')
  const statusEl = document.getElementById('status')
  const urlInput = document.getElementById('mediaPilotUrl')
  const tokenInput = document.getElementById('userToken')
  const historyEl = document.getElementById('history')
  const dataPreviewEl = document.getElementById('dataPreview')

  if (!connectBtn || !captureBtn || !sendBtn || !statusEl || !urlInput || !tokenInput) {
    console.error('[MediaPilot Popup] Missing DOM elements!')
    return
  }

  console.log('[MediaPilot Popup] All DOM elements found')

  // 加载设置
  loadSettings()

  // 绑定事件
  connectBtn.addEventListener('click', handleConnect)
  captureBtn.addEventListener('click', handleCapture)
  sendBtn.addEventListener('click', handleSend)
  urlInput.addEventListener('input', handleUrlChange)
  tokenInput.addEventListener('input', handleTokenChange)

  console.log('[MediaPilot Popup] Events bound')

  // 获取数据
  fetchCurrentData()
}

function loadSettings() {
  chrome.storage.local.get(['mediaPilotUrl', 'userToken', 'isConnected'], (result) => {
    console.log('[MediaPilot Popup] Loaded settings:', result)

    if (result.mediaPilotUrl) {
      document.getElementById('mediaPilotUrl').value = result.mediaPilotUrl
    }

    if (result.userToken) {
      document.getElementById('userToken').value = result.userToken
    }

    if (result.isConnected && result.mediaPilotUrl) {
      document.getElementById('status').textContent = '已连接'
      document.getElementById('status').classList.add('connected')
      checkConnection(result.mediaPilotUrl)
    }
  })
}

function saveSettings() {
  const mediaPilotUrl = document.getElementById('mediaPilotUrl').value.trim()
  const userToken = document.getElementById('userToken').value.trim()

  chrome.storage.local.set({ mediaPilotUrl, userToken })
}

function handleUrlChange() {
  const url = document.getElementById('mediaPilotUrl').value.trim()
  console.log('[MediaPilot Popup] URL changed:', url)
  saveSettings()
}

function handleTokenChange() {
  const token = document.getElementById('userToken').value.trim()
  console.log('[MediaPilot Popup] Token changed:', token ? '***' : 'none')
  saveSettings()
}

function handleConnect() {
  console.log('[MediaPilot Popup] Connect button clicked')

  const url = document.getElementById('mediaPilotUrl').value.trim()
  const token = document.getElementById('userToken').value.trim()

  if (!url) {
    alert('请输入 MediaPilot 网站地址')
    return
  }

  console.log('[MediaPilot Popup] Connecting to:', url)
  checkConnection(url, token)
}

function checkConnection(url, token) {
  console.log('[MediaPilot Popup] Checking connection...')

  const btn = document.getElementById('connectBtn')
  const statusEl = document.getElementById('status')

  btn.disabled = true
  btn.textContent = '连接中...'

  fetch(`${url}/api/extension/status`, {
    method: 'GET',
    headers: token ? { 'Authorization': `Bearer ${token}` } : {}
  })
  .then(res => {
    console.log('[MediaPilot Popup] Status response:', res.status)
    return res.json()
  })
  .then(data => {
    console.log('[MediaPilot Popup] Status data:', data)

    if (data.status === 'ok') {
      statusEl.textContent = '已连接'
      statusEl.classList.add('connected')
      chrome.storage.local.set({ isConnected: true })
    } else {
      statusEl.textContent = '连接失败'
      statusEl.classList.remove('connected')
      chrome.storage.local.set({ isConnected: false })
    }
  })
  .catch(error => {
    console.error('[MediaPilot Popup] Connection error:', error)
    statusEl.textContent = '连接失败'
    statusEl.classList.remove('connected')
    chrome.storage.local.set({ isConnected: false })
  })
  .finally(() => {
    btn.disabled = false
    btn.textContent = '连接 MediaPilot'
  })
}

function handleCapture() {
  console.log('[MediaPilot Popup] Capture button clicked')

  chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
    if (!tabs[0]) {
      alert('无法获取当前标签页')
      return
    }

    console.log('[MediaPilot Popup] Sending message to tab:', tabs[0].id)

    chrome.tabs.sendMessage(tabs[0].id, { action: 'getData' }, (response) => {
      if (chrome.runtime.lastError) {
        console.error('[MediaPilot Popup] Message error:', chrome.runtime.lastError)
        alert('无法获取数据，请确保在小红书页面使用')
        return
      }

      console.log('[MediaPilot Popup] Got response:', response)

      if (response && response.success) {
        console.log('[MediaPilot Popup] Data:', response.data)
        renderData(response.data)

        // 启用按钮
        document.getElementById('captureBtn').disabled = false

        // 添加到历史
        addToHistory(response.data)

        // 复制到剪贴板
        const dataStr = JSON.stringify(response.data, null, 2)
        navigator.clipboard.writeText(dataStr)

        alert('数据已抓取并复制到剪贴板！\n\n可以直接粘贴到 MediaPilot')
      } else {
        alert('数据获取失败')
        renderEmptyState()
      }
    })
  })
}

function handleSend() {
  console.log('[MediaPilot Popup] Send button clicked')

  const url = document.getElementById('mediaPilotUrl').value.trim()
  const token = document.getElementById('userToken').value.trim()
  const statusEl = document.getElementById('status')

  if (statusEl.textContent !== '已连接') {
    alert('请先连接 MediaPilot')
    return
  }

  if (!url) {
    alert('请输入 MediaPilot 网站地址')
    return
  }

  const btn = document.getElementById('sendBtn')
  btn.disabled = true
  btn.textContent = '同步中...'

  fetch(`${url}/api/extension/data`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { 'Authorization': `Bearer ${token}` } : {})
    },
    body: JSON.stringify(lastScrapedData)
  })
  .then(res => res.json())
  .then(data => {
    if (data.success) {
      alert('数据同步成功！')
    } else {
      alert('同步失败：' + (data.error || '未知错误'))
    }
  })
  .catch(error => {
    console.error('[MediaPilot Popup] Send error:', error)
    alert('同步失败：' + error.message)
  })
  .finally(() => {
    btn.disabled = false
    btn.textContent = '同步到 MediaPilot'
  })
}

let lastScrapedData = null

function fetchCurrentData() {
  console.log('[MediaPilot Popup] Fetching current data...')

  chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
    if (!tabs[0]) {
      console.log('[MediaPilot Popup] No active tab')
      return
    }

    console.log('[MediaPilot Popup] Active tab ID:', tabs[0].id)

    chrome.tabs.sendMessage(tabs[0].id, { action: 'getData' }, (response) => {
      if (chrome.runtime.lastError) {
        console.log('[MediaPilot Popup] Content script not loaded')
        renderEmptyState()
        return
      }

      if (response && response.success && response.data) {
        console.log('[MediaPilot Popup] Got data:', response.data)
        lastScrapedData = response.data
        renderData(response.data)
        document.getElementById('captureBtn').disabled = false
      } else {
        console.log('[MediaPilot Popup] No data or error')
        renderEmptyState()
      }
    })
  })
}

function renderEmptyState() {
  document.getElementById('dataPreview').innerHTML = `
    <div class="empty-state">
      <div class="empty-icon">📋</div>
      <p>访问小红书创作者中心或笔记页面</p>
    </div>
  `
}

function renderData(data) {
  const previewEl = document.getElementById('dataPreview')

  if (data.type === 'account') {
    previewEl.innerHTML = `
      <div class="data-item">
        <span class="data-label">平台</span>
        <span class="data-value">${data.platform || '未知'}</span>
      </div>
      <div class="data-item">
        <span class="data-label">账号名称</span>
        <span class="data-value">${data.nickname || '未知'}</span>
      </div>
      <div class="data-item">
        <span class="data-label">粉丝数</span>
        <span class="data-value">${data.fans || 'N/A'}</span>
      </div>
      <div class="data-item">
        <span class="data-label">总播放</span>
        <span class="data-value">${data.totalViews || 'N/A'}</span>
      </div>
      <div class="data-item">
        <span class="data-label">总点赞</span>
        <span class="data-value">${data.totalLikes || 'N/A'}</span>
      </div>
    `
  } else if (data.type === 'note') {
    previewEl.innerHTML = `
      <div class="data-item">
        <span class="data-label">平台</span>
        <span class="data-value">${data.platform || '未知'}</span>
      </div>
      <div class="data-item">
        <span class="data-label">笔记ID</span>
        <span class="data-value">${data.noteId || '未知'}</span>
      </div>
      <div class="data-item">
        <span class="data-label">标题</span>
        <span class="data-value">${data.title || 'N/A'}</span>
      </div>
      <div class="data-item">
        <span class="data-label">播放</span>
        <span class="data-value">${data.views || 'N/A'}</span>
      </div>
      <div class="data-item">
        <span class="data-label">点赞</span>
        <span class="data-value">${data.likes || 'N/A'}</span>
      </div>
      <div class="data-item">
        <span class="data-label">收藏</span>
        <span class="data-value">${data.collects || 'N/A'}</span>
      </div>
      <div class="data-item">
        <span class="data-label">评论</span>
        <span class="data-value">${data.comments || 'N/A'}</span>
      </div>
    `
  } else {
    previewEl.innerHTML = `
      <div class="empty-state">
        <div class="empty-icon">⚠️</div>
        <p>未知的数据类型: ${data.type || 'N/A'}</p>
      </div>
    `
  }
}

function addToHistory(data) {
  chrome.storage.local.get(['captureHistory'], (result) => {
    const history = result.captureHistory || []
    history.unshift({
      ...data,
      timestamp: Date.now()
    })

    // 只保留最近10条
    if (history.length > 10) {
      history.splice(10)
    }

    chrome.storage.local.set({ captureHistory: history })
    renderHistory(history)
  })
}

function renderHistory(history) {
  const historyEl = document.getElementById('history')

  if (!historyEl) return

  if (history.length === 0) {
    historyEl.innerHTML = `
      <div class="empty-history">
        <p class="text-sm text-secondary">暂无抓取记录</p>
      </div>
    `
    return
  }

  historyEl.innerHTML = history.map((item, idx) => `
    <div class="history-item">
      <div class="history-time">${formatTime(item.timestamp)}</div>
      <div class="history-content">
        ${item.platform} - ${item.type}: ${item.title || item.noteId || '未知'}
      </div>
    </div>
  `).join('')
}

function formatTime(timestamp) {
  const date = new Date(timestamp)
  const now = new Date()
  const diff = now - date

  if (diff < 60000) return '刚刚'
  if (diff < 3600000) return `${Math.floor(diff / 60000)}分钟前`
  if (diff < 86400000) return `${Math.floor(diff / 3600000)}小时前`
  return date.toLocaleDateString()
}

console.log('[MediaPilot Popup] Script loaded')
