import { useMemo } from 'react'

// 将纯文本转换为带样式的 HTML
function parseToFormattedContent(text) {
  if (!text) return []

  const lines = text.split('\n')
  const elements = []
  let currentSection = null

  const sectionPatterns = [
    /^[#]{1,3}\s*[🔥📊💡✍️📋🎣📖🎓🎙️⭐🎬👑🎯📈📝🎯💬📱📍]*\s*(.+)$/,
    /^(热点概述|趋势分析|选题建议|文案模板|核心逻辑|标题|钩子|分镜头脚本|话题标签|账号定位|内容策略|可复制经验|差异化建议|定位对比|内容策略对比|优劣势分析|可复用经验)$/,
    /^[🔥📊💡✍️📋🎣📖🎓🎙️⭐🎬👑🎯📈📝🎯💬📱📍]\s*.+/,
  ]

  const isSectionTitle = (line) => {
    return sectionPatterns.some(pattern => pattern.test(line.trim()))
  }

  const isDivider = (line) => {
    return /^[-*_]{3,}$/.test(line.trim())
  }

  const getListNumber = (line) => {
    const match = line.match(/^(\d+)[.、]\s*/)
    return match ? parseInt(match[1]) : null
  }

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i].trim()
    if (!line) continue

    // 分隔符
    if (isDivider(line)) {
      elements.push({ type: 'divider', key: i })
      continue
    }

    // 章节标题
    if (isSectionTitle(line) && (line.includes('概述') || line.includes('分析') || line.includes('建议') || line.includes('模板') || line.includes('脚本') || line.includes('定位') || line.includes('策略') || line.includes('经验') || line.includes('标题') || line.includes('钩子') || line.includes('标签') || line.startsWith('#'))) {
      elements.push({ type: 'section-title', content: line.replace(/^#+\s*/, ''), key: i })
      continue
    }

    // 小标题（带冒号结尾的）
    if (line.endsWith('：') || line.endsWith(':')) {
      elements.push({ type: 'subsection-title', content: line, key: i })
      continue
    }

    // 列表项
    const listNum = getListNumber(line)
    if (listNum !== null) {
      elements.push({ type: 'list-item', content: line.replace(/^\d+[.、]\s*/, ''), number: listNum, key: i })
      continue
    }

    // 普通段落
    elements.push({ type: 'paragraph', content: line, key: i })
  }

  return elements
}

function AIOutputFormatter({ content }) {
  const elements = useMemo(() => parseToFormattedContent(content), [content])

  const renderElement = (el) => {
    switch (el.type) {
      case 'divider':
        return <hr key={el.key} className="divider" />

      case 'section-title':
        return (
          <div key={el.key} className="section-title">
            {el.content}
          </div>
        )

      case 'subsection-title':
        return (
          <div key={el.key} className="subsection-title">
            {el.content}
          </div>
        )

      case 'list-item':
        return (
          <div key={el.key} className="list-item">
            <span className="list-number">{el.number}.</span>
            {el.content}
          </div>
        )

      case 'paragraph':
        // 检查是否包含标签（以#开头或是话题）
        if (el.content.startsWith('#') || el.content.includes('#')) {
          const tags = el.content.split(/(?:#\w+)/g).filter(Boolean)
          const hashtags = el.content.match(/#\w+/g) || []
          if (hashtags.length > 0) {
            return (
              <div key={el.key} className="mt-3">
                {tags.map((tag, idx) => (
                  <span key={idx}>
                    {tag}
                    {hashtags[idx] && <span className="tag">{hashtags[idx]}</span>}
                  </span>
                ))}
              </div>
            )
          }
        }
        return <p key={el.key} className="mb-2">{el.content}</p>

      default:
        return null
    }
  }

  return (
    <div className="ai-output">
      {elements.map(renderElement)}
    </div>
  )
}

export default AIOutputFormatter