function ContentCard({ content, onViewDetail, onEdit, onDelete }) {
  const getTypeIcon = (type) => {
    switch (type) {
      case 'script': return '🎬'
      case 'copywriting': return '🎤'
      case 'video': return '📹'
      case 'audio': return '🎙️'
      default: return '📄'
    }
  }

  const getTypeName = (type) => {
    const typeMap = {
      'script': '拍摄脚本',
      'copywriting': '口播文案',
      'video': '视频',
      'audio': '音频'
    }
    return typeMap[type] || type
  }

  const formatDate = (dateString) => {
    if (!dateString) return ''
    return new Date(dateString).toLocaleDateString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit'
    })
  }

  return (
    <div
      onClick={() => onViewDetail(content.id)}
      style={{
        padding: '20px',
        background: 'var(--bg-secondary)',
        borderRadius: '12px',
        border: '1px solid var(--border-color)',
        cursor: 'pointer',
        transition: 'all 0.2s ease',
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.borderColor = 'var(--primary)'
        e.currentTarget.style.transform = 'translateY(-2px)'
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.borderColor = 'var(--border-color)'
        e.currentTarget.style.transform = 'translateY(0)'
      }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '12px' }}>
        <div style={{
          width: '36px',
          height: '36px',
          borderRadius: '50%',
          background: 'var(--bg-tertiary)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontSize: '18px',
        }}>
          {getTypeIcon(content.content_type)}
        </div>
        <span style={{
          padding: '3px 10px',
          background: 'var(--bg-tertiary)',
          color: 'var(--text-secondary)',
          borderRadius: '12px',
          fontSize: '11px',
          fontWeight: '500',
        }}>
          {getTypeName(content.content_type)}
        </span>
      </div>

      <h3 style={{
        fontSize: '15px',
        fontWeight: '600',
        color: 'var(--text-primary)',
        marginBottom: '8px',
        lineHeight: '1.4',
        overflow: 'hidden',
        textOverflow: 'ellipsis',
        display: '-webkit-box',
        WebkitLineClamp: 2,
        WebkitBoxOrient: 'vertical',
      }}>
        {content.title || '未命名内容'}
      </h3>

      <p style={{
        fontSize: '13px',
        color: 'var(--text-secondary)',
        marginBottom: '12px',
        lineHeight: '1.5',
        overflow: 'hidden',
        textOverflow: 'ellipsis',
        display: '-webkit-box',
        WebkitLineClamp: 3,
        WebkitBoxOrient: 'vertical',
        flex: 1,
      }}>
        {content.summary || content.content?.substring(0, 150) || '暂无摘要'}
      </p>

      {content.topics && content.topics.length > 0 && (
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px', marginBottom: '8px' }}>
          {content.topics.slice(0, 3).map((topic, idx) => (
            <span key={idx} style={{
              padding: '2px 8px',
              background: 'var(--bg-tertiary)',
              color: 'var(--text-secondary)',
              borderRadius: '4px',
              fontSize: '11px',
            }}>
              {topic.name || topic.topic}
            </span>
          ))}
          {content.topics.length > 3 && (
            <span style={{ padding: '2px 6px', color: 'var(--text-tertiary)', fontSize: '11px' }}>
              +{content.topics.length - 3}
            </span>
          )}
        </div>
      )}

      {/* C1: 显示来源热点（hot_topic_id + title + source）—— 跨需求追踪 */}
      {content.hot_topic_id && (
        <div
          title={content.hot_topic_title || content.hot_topic_id}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '4px',
            padding: '4px 8px',
            marginBottom: '8px',
            background: 'linear-gradient(135deg, rgba(255,107,107,0.08) 0%, rgba(255,107,107,0.03) 100%)',
            borderLeft: '2px solid #ff6b6b',
            borderRadius: '4px',
            fontSize: '11px',
            color: 'var(--text-secondary)',
          }}
        >
          <span style={{ color: '#ff6b6b' }}>🔥</span>
          <span style={{
            overflow: 'hidden',
            textOverflow: 'ellipsis',
            whiteSpace: 'nowrap',
            flex: 1,
          }}>
            {content.hot_topic_title || content.hot_topic_id}
          </span>
          {content.hot_topic_source && (
            <span style={{ color: 'var(--text-tertiary)', fontSize: '10px', flexShrink: 0 }}>
              · {content.hot_topic_source}
            </span>
          )}
        </div>
      )}

      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        paddingTop: '10px',
        borderTop: '1px solid var(--border-color)',
      }}>
        <span style={{ fontSize: '11px', color: 'var(--text-tertiary)' }}>
          {formatDate(content.created_at)}
        </span>

        <div style={{ display: 'flex', gap: '4px' }}>
          {onEdit && (
            <button
              onClick={(e) => { e.stopPropagation(); onEdit(content) }}
              style={{
                padding: '4px 8px',
                background: 'transparent',
                border: 'none',
                color: 'var(--text-tertiary)',
                cursor: 'pointer',
                fontSize: '12px',
                borderRadius: '4px',
              }}
              onMouseEnter={(e) => { e.currentTarget.style.color = 'var(--primary)' }}
              onMouseLeave={(e) => { e.currentTarget.style.color = 'var(--text-tertiary)' }}
              title="编辑"
            >
              ✏️
            </button>
          )}
          {onDelete && (
            <button
              onClick={(e) => { e.stopPropagation(); onDelete(content.id) }}
              style={{
                padding: '4px 8px',
                background: 'transparent',
                border: 'none',
                color: 'var(--text-tertiary)',
                cursor: 'pointer',
                fontSize: '12px',
                borderRadius: '4px',
              }}
              onMouseEnter={(e) => { e.currentTarget.style.color = 'var(--error)' }}
              onMouseLeave={(e) => { e.currentTarget.style.color = 'var(--text-tertiary)' }}
              title="删除"
            >
              🗑️
            </button>
          )}
        </div>
      </div>
    </div>
  )
}

export default ContentCard
