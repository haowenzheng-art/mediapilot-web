/**
 * 风格选择器组件
 */

function StyleSelector({ style, setStyle, styles, disabled = false }) {
  return (
    <div style={{ marginBottom: '24px' }}>
      <div style={{
        fontSize: '12px',
        color: 'var(--text-tertiary)',
        marginBottom: '12px'
      }}>
        脚本风格
      </div>
      <div style={{
        display: 'flex',
        gap: '12px',
        flexWrap: 'wrap'
      }}>
        {styles.map((s) => (
          <button
            key={s.id}
            onClick={() => setStyle(s.id)}
            disabled={disabled}
            style={{
              padding: '12px 20px',
              fontSize: '14px',
              background: style === s.id ? 'var(--accent-primary)' : 'var(--bg-secondary)',
              color: style === s.id ? 'white' : 'var(--text-primary)',
              border: style === s.id ? 'none' : '1px solid var(--border-color)',
              borderRadius: '8px',
              cursor: disabled ? 'not-allowed' : 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              opacity: disabled ? 0.5 : 1,
              transition: 'all 0.2s'
            }}
          >
            <span style={{ fontSize: '18px' }}>{s.icon}</span>
            <span style={{ fontWeight: '500' }}>{s.name}</span>
          </button>
        ))}
      </div>
    </div>
  )
}

export default StyleSelector
