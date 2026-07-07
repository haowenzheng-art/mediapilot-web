/**
 * 深度思考 Toggle 组件（v3 改造）
 *
 * 让用户控制是否启用 reasoning_content 流式输出。
 * 默认开启，用户可在生成前手动关闭（响应更快但无思考过程）。
 *
 * 用法：
 *   <ReasoningToggle enabled={enableReasoning} onChange={setEnableReasoning} />
 */
export function ReasoningToggle({ enabled, onChange, label = '深度思考' }) {
  const handleChange = (e) => {
    onChange(e.target.checked)
  }

  return (
    <label
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: '8px',
        cursor: 'pointer',
        userSelect: 'none',
        fontSize: '14px',
        color: 'var(--text-primary)',
      }}
      title="启用后显示 AI 思考过程（reasoning），响应稍慢但质量更高"
    >
      <span
        style={{
          position: 'relative',
          display: 'inline-block',
          width: '36px',
          height: '20px',
          background: enabled ? 'var(--accent-primary)' : 'var(--bg-tertiary)',
          borderRadius: '10px',
          transition: 'background 0.2s',
          flexShrink: 0,
        }}
      >
        <input
          type="checkbox"
          checked={enabled}
          onChange={handleChange}
          style={{
            opacity: 0,
            width: 0,
            height: 0,
            position: 'absolute',
          }}
        />
        <span
          style={{
            position: 'absolute',
            top: '2px',
            left: enabled ? '18px' : '2px',
            width: '16px',
            height: '16px',
            background: '#fff',
            borderRadius: '50%',
            transition: 'left 0.2s',
            pointerEvents: 'none',
          }}
        />
      </span>
      <span>🧠 {label}</span>
    </label>
  )
}