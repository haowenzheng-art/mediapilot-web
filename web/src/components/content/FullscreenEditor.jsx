import { useState, useRef, useEffect } from 'react'

export default function FullscreenEditor({
  // 输入相关
  value = '',
  onChange,
  placeholder = '',
  disabled = false,
  minHeight = '60vh',

  // 输出相关
  output = null,
  outputComponent: OutputComponent = null,

  // 操作相关
  actionLabel = '提交',
  onAction,
  actionDisabled = false,
  isLoading = false,

  // 工具栏
  toolbarLeft = null,
  toolbarRight = null,

  // 选项
  showPreview = true,
  previewCollapsed = false,
  onPreviewToggle,

  // 事件
  onKeyDown,
}) {
  const [showPreviewState, setShowPreviewState] = useState(!previewCollapsed)
  const [wordCount, setWordCount] = useState(0)
  const [charCount, setCharCount] = useState(0)
  const textareaRef = useRef(null)

  // 受控预览状态
  const shouldShowPreview = onPreviewToggle !== undefined
    ? !previewCollapsed
    : showPreviewState

  const handlePreviewToggle = () => {
    if (onPreviewToggle) {
      onPreviewToggle()
    } else {
      setShowPreviewState(!showPreviewState)
    }
  }

  // 统计字数
  useEffect(() => {
    const text = value || ''
    setCharCount(text.length)
    // 简单的字数统计（按空格分词）
    setWordCount(text.trim() ? text.trim().split(/\s+/).length : 0)
  }, [value])

  // 自动聚焦
  useEffect(() => {
    if (textareaRef.current && !disabled) {
      textareaRef.current.focus()
    }
  }, [])

  // 处理键盘事件
  const handleKeyDown = (e) => {
    // Ctrl/Cmd + Enter 提交
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
      e.preventDefault()
      if (onAction && !actionDisabled && !isLoading) {
        onAction()
      }
    }

    if (onKeyDown) {
      onKeyDown(e)
    }
  }

  return (
    <div className="fullscreen-editor" style={{ minHeight, display: 'flex', height: '100%' }}>
      {/* 输入区域 */}
      <div
        style={{
          flex: shouldShowPreview && OutputComponent ? '0 0 70%' : '1 1 100%',
          display: 'flex',
          flexDirection: 'column',
          borderRight: shouldShowPreview && OutputComponent ? '1px solid var(--border-color)' : 'none',
        }}
      >
        {/* 顶部工具栏 */}
        {(toolbarLeft || toolbarRight) && (
          <div style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            padding: '12px 24px',
            borderBottom: '1px solid var(--border-color)',
          }}>
            <div>{toolbarLeft}</div>
            <div>{toolbarRight}</div>
          </div>
        )}

        {/* 文本输入区 */}
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
          <textarea
            ref={textareaRef}
            value={value}
            onChange={(e) => onChange?.(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={placeholder}
            disabled={disabled || isLoading}
            style={{
              flex: 1,
              width: '100%',
              padding: '32px',
              fontSize: '16px',
              lineHeight: '1.8',
              color: 'var(--text-primary)',
              background: 'transparent',
              border: 'none',
              outline: 'none',
              resize: 'none',
              fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
            }}
          />

          {/* 底部状态栏 */}
          <div style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            padding: '12px 24px',
            borderTop: '1px solid var(--border-color)',
            background: 'var(--bg-secondary)',
          }}>
            <div style={{
              display: 'flex',
              gap: '16px',
              fontSize: '13px',
              color: 'var(--text-tertiary)',
            }}>
              <span>{charCount} 字符</span>
              <span>{wordCount} 词</span>
              <span style={{ color: 'var(--text-tertiary)' }}>
                (Ctrl/Cmd + Enter 提交)
              </span>
            </div>

            <button
              onClick={onAction}
              disabled={actionDisabled || isLoading}
              className="btn btn-primary btn-lg"
              style={{
                minWidth: '120px',
              }}
            >
              {isLoading ? (
                <span style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <span style={{ animation: 'spin 1s linear infinite' }}>⏳</span>
                  处理中...
                </span>
              ) : (
                actionLabel
              )}
            </button>
          </div>
        </div>
      </div>

      {/* 预览区域 */}
      {shouldShowPreview && OutputComponent && (
        <div
          style={{
            flex: '0 0 30%',
            display: 'flex',
            flexDirection: 'column',
            overflow: 'hidden',
            background: 'var(--bg-secondary)',
          }}
        >
          {/* 预览头部 */}
          <div style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            padding: '12px 24px',
            borderBottom: '1px solid var(--border-color)',
          }}>
            <span style={{
              fontSize: '14px',
              fontWeight: '600',
              color: 'var(--text-secondary)',
            }}>
              输出预览
            </span>
            <button
              onClick={handlePreviewToggle}
              style={{
                background: 'transparent',
                border: 'none',
                color: 'var(--text-tertiary)',
                cursor: 'pointer',
                padding: '4px',
              }}
              title="隐藏预览"
            >
              ✕
            </button>
          </div>

          {/* 预览内容 */}
          <div style={{
            flex: 1,
            overflow: 'auto',
            padding: '24px',
          }}>
            {output ? (
              <OutputComponent data={output} />
            ) : (
              <div style={{
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                justifyContent: 'center',
                height: '100%',
                color: 'var(--text-tertiary)',
                textAlign: 'center',
              }}>
                <span style={{ fontSize: '48px', marginBottom: '16px' }}>✨</span>
                <p>输入内容后，结果将在这里显示</p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* 预览折叠按钮（当预览隐藏时显示） */}
      {!shouldShowPreview && OutputComponent && (
        <button
          onClick={handlePreviewToggle}
          style={{
            position: 'absolute',
            right: '24px',
            bottom: '80px',
            padding: '12px 16px',
            background: 'var(--bg-primary)',
            border: '1px solid var(--border-color)',
            borderRadius: 'var(--radius-md)',
            color: 'var(--text-secondary)',
            cursor: 'pointer',
            fontSize: '14px',
            fontWeight: '500',
            boxShadow: 'var(--shadow-md)',
          }}
        >
          显示预览 →
        </button>
      )}

      <style>{`
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  )
}
