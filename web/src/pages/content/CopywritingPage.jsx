import { useState, useEffect } from 'react'
import { useCopywriting } from '../../hooks/use-copywriting'
import { copywritingService } from '../../services/copywriting'
import PageContainer from '../../components/common/PageContainer'

function PersonaInput({ persona, setPersona, personas, onCreatePersona, onSelectPersona }) {
  const [showNewInput, setShowNewInput] = useState(false)
  const [newPersona, setNewPersona] = useState('')

  const handleCreatePersona = () => {
    if (newPersona.trim()) {
      onCreatePersona(newPersona)
      setNewPersona('')
      setShowNewInput(false)
    }
  }

  return (
    <div style={{ marginBottom: '16px' }}>
      <div style={{ fontSize: '12px', color: 'var(--text-tertiary)', marginBottom: '8px' }}>
        人设（决定文案风格和视角）
      </div>

      <div style={{ marginBottom: '12px' }}>
        <input
          type="text"
          value={persona}
          onChange={(e) => setPersona(e.target.value)}
          placeholder="例如：大厂AI产品经理、健身教练、美食博主..."
          style={{
            width: '100%',
            padding: '12px 16px',
            fontSize: '14px',
            border: '1px solid var(--border-color)',
            borderRadius: '8px',
            background: 'var(--bg-secondary)',
            color: 'var(--text-primary)'
          }}
        />
      </div>

      {personas.length > 0 && !showNewInput && (
        <div style={{ marginBottom: '12px' }}>
          <div style={{ fontSize: '12px', color: 'var(--text-secondary)', marginBottom: '8px' }}>
            最近使用的人设
          </div>
          <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
            {personas.map((p) => (
              <button
                key={p.id}
                onClick={() => onSelectPersona(p.persona_description)}
                style={{
                  padding: '8px 16px',
                  fontSize: '13px',
                  background: persona === p.persona_description
                    ? 'var(--accent-primary)'
                    : 'var(--bg-tertiary)',
                  color: persona === p.persona_description
                    ? 'white'
                    : 'var(--text-primary)',
                  border: 'none',
                  borderRadius: '20px',
                  cursor: 'pointer',
                  transition: 'all 0.2s'
                }}
              >
                {p.persona_description}
              </button>
            ))}
          </div>
        </div>
      )}

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        {!showNewInput ? (
          <button
            onClick={() => setShowNewInput(true)}
            style={{
              padding: '8px 16px',
              fontSize: '13px',
              color: 'var(--accent-primary)',
              background: 'transparent',
              border: '1px solid var(--accent-primary)',
              borderRadius: '8px',
              cursor: 'pointer'
            }}
          >
            + 保存当前人设
          </button>
        ) : (
          <div style={{ display: 'flex', gap: '8px', alignItems: 'center', flex: 1 }}>
            <input
              type="text"
              value={newPersona}
              onChange={(e) => setNewPersona(e.target.value)}
              placeholder="输入新的人设..."
              style={{
                flex: 1,
                padding: '8px 12px',
                fontSize: '13px',
                border: '1px solid var(--border-color)',
                borderRadius: '6px',
                background: 'var(--bg-secondary)',
                color: 'var(--text-primary)'
              }}
            />
            <button
              onClick={() => setShowNewInput(false)}
              style={{
                padding: '6px 12px',
                fontSize: '13px',
                background: 'var(--bg-tertiary)',
                color: 'var(--text-secondary)',
                border: 'none',
                borderRadius: '6px',
                cursor: 'pointer'
              }}
            >
              取消
            </button>
            <button
              onClick={handleCreatePersona}
              style={{
                padding: '6px 12px',
                fontSize: '13px',
                background: 'var(--accent-primary)',
                color: 'white',
                border: 'none',
                borderRadius: '6px',
                cursor: 'pointer'
              }}
            >
              保存
            </button>
          </div>
        )}
      </div>
    </div>
  )
}

function ModeSelector({ mode, setMode, modes }) {
  return (
    <div style={{ marginBottom: '24px' }}>
      <div style={{ fontSize: '12px', color: 'var(--text-tertiary)', marginBottom: '8px' }}>
        生成模式
      </div>
      <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
        {modes.map((m) => (
          <button
            key={m.id}
            onClick={() => setMode(m.id)}
            style={{
              padding: '12px 20px',
              fontSize: '14px',
              background: mode === m.id ? 'var(--accent-primary)' : 'var(--bg-secondary)',
              color: mode === m.id ? 'white' : 'var(--text-primary)',
              border: mode === m.id ? 'none' : '1px solid var(--border-color)',
              borderRadius: '8px',
              cursor: 'pointer',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'flex-start',
              gap: '4px'
            }}
          >
            <span style={{ fontWeight: '600' }}>{m.name}</span>
            <span style={{ fontSize: '11px', color: mode === m.id ? 'rgba(255,255,255,0.8)' : 'var(--text-tertiary)' }}>
              {m.description}
            </span>
          </button>
        ))}
      </div>
    </div>
  )
}

function ContentInput({ mode, topic, setTopic, hotspotContent, setHotspotContent, originalText, setOriginalText }) {
  if (mode === 'from_zero') {
    return (
      <div style={{ marginBottom: '24px' }}>
        <div style={{ fontSize: '12px', color: 'var(--text-tertiary)', marginBottom: '8px' }}>
          输入话题
        </div>
        <textarea
          value={topic}
          onChange={(e) => setTopic(e.target.value)}
          placeholder="输入你想要创作的话题...&#10;&#10;例如：&#10;• 如何提高工作效率&#10;• 保险入门指南&#10;• 健身减脂的30个真相"
          rows={4}
          style={{
            width: '100%',
            padding: '12px 16px',
            fontSize: '14px',
            border: '1px solid var(--border-color)',
            borderRadius: '8px',
            background: 'var(--bg-secondary)',
            color: 'var(--text-primary)',
            resize: 'vertical',
            lineHeight: '1.6'
          }}
        />
      </div>
    )
  } else if (mode === 'hotspot') {
    return (
      <div style={{ marginBottom: '24px' }}>
        <div style={{ fontSize: '12px', color: 'var(--text-tertiary)', marginBottom: '8px' }}>
          粘贴热点内容（从热点搜索复制的介绍和总结）
        </div>
        <textarea
          value={hotspotContent}
          onChange={(e) => setHotspotContent(e.target.value)}
          placeholder="在此粘贴热点内容..."
          rows={6}
          style={{
            width: '100%',
            padding: '12px 16px',
            fontSize: '14px',
            border: '1px solid var(--border-color)',
            borderRadius: '8px',
            background: 'var(--bg-secondary)',
            color: 'var(--text-primary)',
            resize: 'vertical',
            lineHeight: '1.6'
          }}
        />
      </div>
    )
  } else {
    return (
      <div style={{ marginBottom: '24px' }}>
        <div style={{ fontSize: '12px', color: 'var(--text-tertiary)', marginBottom: '8px' }}>
          粘贴原文（需要改写的文案）
        </div>
        <textarea
          value={originalText}
          onChange={(e) => setOriginalText(e.target.value)}
          placeholder="在此粘贴需要改写的文案..."
          rows={6}
          style={{
            width: '100%',
            padding: '12px 16px',
            fontSize: '14px',
            border: '1px solid var(--border-color)',
            borderRadius: '8px',
            background: 'var(--bg-secondary)',
            color: 'var(--text-primary)',
            resize: 'vertical',
            lineHeight: '1.6'
          }}
        />
      </div>
    )
  }
}

function RewriteOptions({ onRewrite, rewriteDirections, loading }) {
  return (
    <div style={{ marginTop: '24px', padding: '16px', background: 'var(--bg-secondary)', borderRadius: '8px' }}>
      <div style={{ fontSize: '13px', fontWeight: '600', color: 'var(--text-secondary)', marginBottom: '12px' }}>
        再改改
      </div>
      <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
        {rewriteDirections.map((dir) => (
          <button
            key={dir.id}
            onClick={() => onRewrite(dir.id)}
            disabled={loading}
            style={{
              padding: '10px 20px',
              fontSize: '14px',
              background: 'var(--bg-primary)',
              color: 'var(--text-primary)',
              border: '1px solid var(--border-color)',
              borderRadius: '8px',
              cursor: loading ? 'not-allowed' : 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              opacity: loading ? 0.5 : 1
            }}
          >
            <span style={{ fontSize: '18px' }}>{dir.icon}</span>
            {dir.name}
          </button>
        ))}
      </div>
    </div>
  )
}

function CopywritingResult({ result, onCopy, onRewrite, rewriteDirections, loading }) {
  if (!result) return null

  return (
    <div style={{
      padding: '24px',
      background: 'var(--bg-secondary)',
      borderRadius: '12px',
      border: '1px solid var(--border-color)'
    }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '16px' }}>
        <div>
          <div style={{ fontSize: '12px', color: 'var(--text-tertiary)', marginBottom: '4px' }}>标题</div>
          <div style={{ fontSize: '18px', fontWeight: '600', color: 'var(--text-primary)' }}>
            {result.title}
          </div>
        </div>
        <button
          onClick={onCopy}
          style={{
            padding: '8px 16px',
            fontSize: '13px',
            background: 'var(--accent-primary)',
            color: 'white',
            border: 'none',
            borderRadius: '6px',
            cursor: 'pointer'
          }}
        >
          复制全文
        </button>
      </div>

      {result.hooks && result.hooks.length > 0 && (
        <div style={{ marginBottom: '16px' }}>
          <div style={{ fontSize: '12px', color: 'var(--text-tertiary)', marginBottom: '8px' }}>钩子（点击使用）</div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            {result.hooks.map((hook, idx) => (
              <div
                key={idx}
                style={{
                  padding: '10px 14px',
                  background: 'var(--bg-primary)',
                  borderRadius: '6px',
                  fontSize: '13px',
                  color: 'var(--text-primary)',
                  cursor: 'pointer'
                }}
                onClick={() => {
                  navigator.clipboard.writeText(hook).then(() => {
                    alert('钩子已复制')
                  })
                }}
              >
                {idx + 1}. {hook}
              </div>
            ))}
          </div>
        </div>
      )}

      <div>
        <div style={{ fontSize: '12px', color: 'var(--text-tertiary)', marginBottom: '8px' }}>文案正文</div>
        <div style={{
          padding: '16px',
          background: 'var(--bg-primary)',
          borderRadius: '8px',
          fontSize: '14px',
          lineHeight: '1.8',
          color: 'var(--text-primary)',
          whiteSpace: 'pre-wrap'
        }}>
          {result.content}
        </div>
      </div>

      <RewriteOptions onRewrite={onRewrite} rewriteDirections={rewriteDirections} loading={loading} />
    </div>
  )
}

function CopywritingPage() {
  const {
    mode, setMode,
    persona, setPersona,
    personas, setPersonas,
    topic, setTopic,
    hotspotContent, setHotspotContent,
    originalText, setOriginalText,
    result, setResult,
    loading, error, setError,
    generate, rewrite, copyResult,
    modes, rewriteDirections,
    createPersona, selectPersona
  } = useCopywriting()

  useEffect(() => {
    // 加载人设列表
    const fetchPersonas = async () => {
      try {
        const data = await copywritingService.getPersonas()
        if (data.success) {
          setPersonas(data.data.personas || [])
        }
      } catch (err) {
        console.error('获取人设列表失败:', err)
      }
    }
    fetchPersonas()

    // 消费来自热点页的待粘贴内容（mount 时即检查，避免事件竞争）
    const pending = sessionStorage.getItem('copywriting:pending_hotspot')
    if (pending) {
      setMode('hotspot')
      setHotspotContent(pending)
      sessionStorage.removeItem('copywriting:pending_hotspot')
    }

    // 兼容旧的事件式跳转（同 tab 内派发时仍可工作）
    const handlePaste = (e) => {
      const content = e.detail
      if (content) {
        setMode('hotspot')
        setHotspotContent(content)
      }
    }

    window.addEventListener('copywriting-paste', handlePaste)

    return () => {
      window.removeEventListener('copywriting-paste', handlePaste)
    }
  }, [])

  const handleGenerate = () => {
    generate()
  }

  const handleRewrite = (direction) => {
    rewrite(direction)
  }

  return (
    <PageContainer title="口播文案生成" description="输入人设，AI自动生成口播文案">
      <div style={{ maxWidth: '800px', margin: '0 auto' }}>
        <PersonaInput
          persona={persona}
          setPersona={setPersona}
          personas={personas}
          onCreatePersona={createPersona}
          onSelectPersona={selectPersona}
        />

        <ModeSelector mode={mode} setMode={setMode} modes={modes} />

        <ContentInput
          mode={mode}
          topic={topic}
          setTopic={setTopic}
          hotspotContent={hotspotContent}
          setHotspotContent={setHotspotContent}
          originalText={originalText}
          setOriginalText={setOriginalText}
        />

        {error && (
          <div style={{
            padding: '12px 16px',
            marginBottom: '16px',
            background: 'rgba(239, 68, 68, 0.1)',
            border: '1px solid rgba(239, 68, 68, 0.3)',
            borderRadius: '8px',
            fontSize: '13px',
            color: '#dc2626'
          }}>
            {error}
          </div>
        )}

        <button
          onClick={handleGenerate}
          disabled={loading || !persona.trim()}
          style={{
            width: '100%',
            padding: '14px 24px',
            fontSize: '16px',
            fontWeight: '600',
            background: loading || !persona.trim() ? 'var(--text-tertiary)' : 'var(--accent-primary)',
            color: 'white',
            border: 'none',
            borderRadius: '10px',
            cursor: loading || !persona.trim() ? 'not-allowed' : 'pointer',
            opacity: loading || !persona.trim() ? 0.6 : 1
          }}
        >
          {loading ? (
            <>
              <span className="loading-spinner" style={{ marginRight: '8px' }}></span>
              生成中...
            </>
          ) : (
            '生成文案'
          )}
        </button>

        {result && (
          <CopywritingResult
            result={result}
            onCopy={copyResult}
            onRewrite={handleRewrite}
            rewriteDirections={rewriteDirections}
            loading={loading}
          />
        )}
      </div>
    </PageContainer>
  )
}

export default CopywritingPage
