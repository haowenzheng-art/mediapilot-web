import { useState, useRef, useEffect } from 'react'
import { aiService, isAIEnabled } from '../services/api'

function AIChat() {
  const [isOpen, setIsOpen] = useState(false)
  const [messages, setMessages] = useState([
    { role: 'assistant', content: '你好！我是MediaPilot AI助手，有什么可以帮你的吗？' }
  ])
  const [input, setInput] = useState('')
  const [isTyping, setIsTyping] = useState(false)
  const messagesEndRef = useRef(null)
  const aiEnabled = isAIEnabled()

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleSend = async () => {
    if (!input.trim() || isTyping) return

    const userMessage = input.trim()
    setInput('')

    setMessages(prev => [...prev, { role: 'user', content: userMessage }])
    setIsTyping(true)

    setMessages(prev => [...prev, { role: 'assistant', content: '' }])

    try {
      const chatHistory = messages.map(m => ({
        role: m.role,
        content: m.content
      })).concat([{ role: 'user', content: userMessage }])

      let fullContent = ''
      for await (const chunk of aiService.chatStream(chatHistory, { maxTokens: 800, temperature: 0.5 })) {
        fullContent += chunk
        setMessages(prev => {
          const newMessages = [...prev]
          newMessages[newMessages.length - 1] = {
            role: 'assistant',
            content: fullContent
          }
          return newMessages
        })
      }
    } catch (error) {
      console.error('Chat error:', error)
      setMessages(prev => {
        const newMessages = [...prev]
        newMessages[newMessages.length - 1] = {
          role: 'assistant',
          content: '抱歉，AI服务暂时不可用，请稍后再试。'
        }
        return newMessages
      })
    } finally {
      setIsTyping(false)
    }
  }

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const toggleChat = () => {
    if (!aiEnabled) {
      alert('🔧 AI 功能暂未开放\n\n该功能为演示版本，请联系开发者体验')
      return
    }
    setIsOpen(!isOpen)
  }

  return (
    <>
      {/* 右下角机器人图标（最小化状态） */}
      {!isOpen && (
        <button
          onClick={toggleChat}
          className="ai-chat-fab"
        >
          <span className="fab-icon">🤖</span>
          <span className="fab-pulse"></span>
        </button>
      )}

      {/* 聊天窗口（打开状态）- 智能手机风格 */}
      {isOpen && (
        <div className="ai-chat-window">
          {/* 手机顶部边框 */}
          <div className="phone-top-bezel">
            <div className="phone-notch"></div>
          </div>

          {/* 头部 */}
          <div className="chat-header">
            <div className="chat-header-left">
              <button
                onClick={toggleChat}
                className="chat-btn chat-btn-minimize"
                title="最小化"
              >
                <span className="btn-icon">−</span>
              </button>
            </div>
            <div className="chat-header-center">
              <div className="chat-avatar">
                🤖
              </div>
              <div className="chat-info">
                <h3 className="chat-title">AI助手</h3>
                <p className="chat-status">
                  <span className="status-dot"></span>
                  在线
                </p>
              </div>
            </div>
            <div className="chat-header-right">
              <button
                onClick={() => setIsOpen(false)}
                className="chat-btn chat-btn-close"
                title="关闭"
              >
                <span className="btn-icon">×</span>
              </button>
            </div>
          </div>

          {/* 消息区域 */}
          <div className="chat-messages">
            {messages.map((msg, idx) => (
              <div
                key={idx}
                className={`chat-message ${msg.role === 'user' ? 'chat-message-user' : 'chat-message-ai'}`}
              >
                <div className="chat-bubble">
                  {msg.content || (
                    <span className="typing-indicator">
                      <span></span>
                      <span></span>
                      <span></span>
                    </span>
                  )}
                </div>
              </div>
            ))}
            <div ref={messagesEndRef} />
          </div>

          {/* 输入区域 */}
          <div className="chat-input-area">
            <div className="chat-input-wrapper">
              <textarea
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyPress}
                placeholder="输入消息..."
                className="chat-input"
                rows={1}
              />
              <button
                onClick={handleSend}
                disabled={isTyping || !input.trim()}
                className="chat-send-btn"
              >
                {isTyping ? (
                  <span className="sending-icon">
                    <span></span>
                    <span></span>
                    <span></span>
                  </span>
                ) : (
                  <span className="send-arrow">→</span>
                )}
              </button>
            </div>
          </div>

          {/* 手机底部边框 */}
          <div className="phone-bottom-bezel">
            <div className="phone-gesture-bar"></div>
          </div>
        </div>
      )}
    </>
  )
}

export default AIChat
