import { useState, useRef, useEffect } from 'react'
import { aiService } from '../../services/ai'
import { isAIEnabled } from '../../services/api'

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
      {!isOpen && (
        <button onClick={toggleChat} className="ai-chat-fab">
          <span className="fab-icon">🤖</span>
          <span className="fab-pulse"></span>
        </button>
      )}

      {isOpen && (
        <div className="ai-chat-window">
          <div className="chat-header">
            <div className="chat-header-left">
              <button onClick={toggleChat} className="chat-btn chat-btn-minimize" title="最小化">
                −
              </button>
            </div>
            <div className="chat-header-center">
              <div className="chat-avatar">🤖</div>
              <div className="chat-info">
                <h3 className="chat-title">AI助手</h3>
                <p className="chat-status">
                  <span className="status-dot"></span>
                  在线
                </p>
              </div>
            </div>
            <div className="chat-header-right">
              <button onClick={() => setIsOpen(false)} className="chat-btn" title="关闭">
                ×
              </button>
            </div>
          </div>

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

          <div className="chat-input-area">
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyPress}
              placeholder="输入消息..."
              className="chat-input"
            />
            <button
              onClick={handleSend}
              disabled={isTyping || !input.trim()}
              className="chat-send-btn"
            >
              ➤
            </button>
          </div>
        </div>
      )}
    </>
  )
}

export default AIChat
