console.log('[MediaPilot Content] Script loading...')

chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  console.log('[MediaPilot Content] Received message:', request)

  if (request.action === 'getData') {
    console.log('[MediaPilot Content] Action: getData')

    const data = scrapeData()
    console.log('[MediaPilot Content] Scraped data:', data)

    sendResponse({ success: true, data: data })
  } else {
    sendResponse({ success: false })
  }
})

function scrapeData() {
  const url = window.location.href
  const hostname = window.location.hostname

  console.log('[MediaPilot Content] Scraping URL:', url)
  console.log('[MediaPilot Content] Hostname:', hostname)

  let data = {
    platform: '小红书',
    url: url,
    type: 'note',
    scrapedAt: new Date().toISOString()
  }

  try {
    console.log('[MediaPilot Content] Attempting to scrape...')

    // 获取标题
    const titleEl = document.querySelector('#detail-title') || document.querySelector('.title')
    if (titleEl && titleEl.textContent) {
      data.title = titleEl.textContent.trim()
      console.log('[MediaPilot Content] Title found:', data.title)
    }

    // 获取评论总数（从评论区域）
    const commentsTotalEl = document.querySelector('.comments-container .total')
    if (commentsTotalEl && commentsTotalEl.textContent) {
      const text = commentsTotalEl.textContent.trim()
      const match = text.match(/(\d+)/)
      if (match) {
        data.comments = parseInt(match[1])
        console.log('[MediaPilot Content] Comments found:', data.comments)
      }
    }

    // 获取页面底部所有 count 类的元素
    const countElements = document.querySelectorAll('.count')
    console.log('[MediaPilot Content] Found .count elements:', countElements.length)

    const counts = []
    countElements.forEach((el, idx) => {
      const text = el.textContent ? el.textContent.trim() : ''
      const num = parseInt(text)
      
      if (!isNaN(num) && num > 0 && num < 1000000) {
        counts.push({
          index: idx,
          value: num,
          text: text,
          parentClass: el.parentElement ? el.parentElement.className : '',
          parentText: el.parentElement ? (el.parentElement.textContent || '').trim() : ''
        })
      }
    })

    console.log('[MediaPilot Content] Extracted counts:', counts)

    // 尝试识别点赞、收藏、评论
    // 根据小红书页面结构，通常第一个较大的数字是点赞
    if (counts.length >= 3) {
      // 排序，从大到小
      counts.sort((a, b) => b.value - a.value)
      
      console.log('[MediaPilot Content] Sorted counts:', counts)
      
      // 最大的通常是点赞
      if (counts[0] && counts[0].value > 100) {
        data.likes = counts[0].value
        console.log('[MediaPilot Content] Likes:', data.likes)
      }
      
      // 第二个通常是收藏（如果存在）
      if (counts[1] && counts[1].value > 10) {
        data.collects = counts[1].value
        console.log('[MediaPilot Content] Collects:', data.collects)
      }
    }

    // 提取笔记ID
    const noteIdMatch = url.match(/\/explore\/([a-f0-9]+)/)
    if (noteIdMatch) {
      data.noteId = noteIdMatch[1]
      console.log('[MediaPilot Content] Note ID:', data.noteId)
    }

  } catch (error) {
    console.error('[MediaPilot Content] Scrape error:', error)
  }

  console.log('[MediaPilot Content] Final data:', data)
  return data
}

console.log('[MediaPilot Content] Script loaded')
