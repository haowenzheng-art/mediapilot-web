// Background Service Worker
chrome.runtime.onInstalled.addListener((details) => {
  if (details.reason === 'install') {
    console.log('[MediaPilot] Extension installed')

    // 打开欢迎页
    chrome.tabs.create({
      url: 'https://vercel.app/extension/welcome'
    })
  }
})

// 监听来自 content script 的消息
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'sendData') {
    // 处理自动发送的数据
    console.log('[MediaPilot] Received data:', request.data)

    // 保存到 storage
    chrome.storage.local.get(['autoSendData'], (result) => {
      const data = result.autoSendData || []
      data.unshift({
        ...request.data,
        timestamp: Date.now(),
        tabId: sender.tab?.id
      })

      // 只保留最近50条
      if (data.length > 50) {
        data.splice(50)
      }

      chrome.storage.local.set({ autoSendData: data })
    })

    sendResponse({ success: true })
  }
})

// 监听标签页更新
chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
  if (changeInfo.status === 'complete' && tab.url) {
    // 可以在这里做一些页面加载后的处理
    // 比如：自动通知用户这个页面可以抓取数据
  }
})
