import { useState, useEffect } from 'react'
import { useShootScript } from '../../hooks/use-shoot-script'
import PageContainer from '../../components/common/PageContainer'
import PlatformSelector from '../../components/content/PlatformSelector'
import StyleSelector from '../../components/content/StyleSelector'
import ShotList from '../../components/content/ShotList'
import { ReasoningToggle } from '../../components/common/ReasoningToggle'
import { useHotTopic } from '../../contexts/HotTopicContext.jsx'

function StreamingIndicator({ reasoning, reasoningSupported }) {
  // shots 整体性强，仍按完成再渲染；流式阶段只显示思考过程 + 进度提示
  return (
    <div
      style={{
        marginTop: '32px',
        padding: '24px',
        background: 'var(--bg-secondary)',
        borderRadius: '12px',
        border: '1px solid var(--border-color)',
      }}
    >
      {reasoningSupported && reasoning && (
        <details
          open
          style={{
            marginBottom: '16px',
            padding: '12px 16px',
            background: 'var(--bg-primary)',
            border: '1px dashed var(--border-color)',
            borderRadius: '8px',
          }}
        >
          <summary
            style={{
              fontSize: '12px',
              fontWeight: '600',
              color: 'var(--text-tertiary)',
              cursor: 'pointer',
              userSelect: 'none',
            }}
          >
            🧠 思考过程（{reasoning.length} 字）
          </summary>
          <div
            style={{
              marginTop: '8px',
              fontSize: '12px',
              lineHeight: '1.6',
              color: 'var(--text-tertiary)',
              whiteSpace: 'pre-wrap',
              fontFamily: 'var(--font-mono, monospace)',
            }}
          >
            {reasoning}
          </div>
        </details>
      )}

      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: '12px',
          padding: '16px',
          background: 'var(--bg-primary)',
          borderRadius: '8px',
        }}
      >
        <span
          className="loading-spinner"
          style={{ fontSize: '20px', color: 'var(--accent-primary)' }}
        />
        <div style={{ flex: 1 }}>
          <div style={{ fontSize: '14px', fontWeight: '600', color: 'var(--text-primary)' }}>
            AI 正在生成拍摄脚本…
          </div>
          <div style={{ fontSize: '12px', color: 'var(--text-tertiary)', marginTop: '4px' }}>
            分镜头脚本需要完整生成后才能渲染，正在等待后端完成…
          </div>
        </div>
      </div>
    </div>
  )
}

function ScriptInfo({ result, onCopy, onExport, onRegenerate }) {
  if (!result) return null

  return (
    <div style={{
      padding: '24px',
      background: 'var(--bg-secondary)',
      borderRadius: '12px',
      border: '1px solid var(--border-color)'
    }}>
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'flex-start',
        marginBottom: '20px'
      }}>
        <div>
          <div style={{
            fontSize: '12px',
            color: 'var(--text-tertiary)',
            marginBottom: '6px'
          }}>
            标题
          </div>
          <div style={{
            fontSize: '20px',
            fontWeight: '600',
            color: 'var(--text-primary)',
            marginBottom: '16px'
          }}>
            {result.title}
          </div>

          <div style={{ marginBottom: '16px' }}>
            <div style={{
              fontSize: '12px',
              color: 'var(--text-tertiary)',
              marginBottom: '8px'
            }}>
              钩子（点击使用）
            </div>
            <div style={{
              display: 'flex',
              flexDirection: 'column',
              gap: '6px'
            }}>
              {result.hooks.map((hook, idx) => (
                <div
                  key={idx}
                  onClick={() => {
                    navigator.clipboard.writeText(hook).then(() => {
                      alert('钩子已复制')
                    })
                  }}
                  style={{
                    padding: '10px 14px',
                    background: 'var(--bg-primary)',
                    borderRadius: '6px',
                    fontSize: '13px',
                    color: 'var(--text-primary)',
                    cursor: 'pointer'
                  }}
                >
                  {idx + 1}. {hook}
                </div>
              ))}
            </div>
          </div>

          <div style={{ marginBottom: '16px' }}>
            <div style={{
              fontSize: '12px',
              color: 'var(--text-tertiary)',
              marginBottom: '6px'
            }}>
              行动号召
            </div>
            <div style={{
              padding: '10px 14px',
              background: 'rgba(59, 130, 246, 0.1)',
              borderRadius: '6px',
              fontSize: '14px',
              color: 'var(--text-primary)'
            }}>
              {result.call_to_action}
            </div>
          </div>

          {result.tags && result.tags.length > 0 && (
            <div>
              <div style={{
                fontSize: '12px',
                color: 'var(--text-tertiary)',
                marginBottom: '8px'
              }}>
                标签
              </div>
              <div style={{
                display: 'flex',
                gap: '8px',
                flexWrap: 'wrap'
              }}>
                {result.tags.map((tag, idx) => (
                  <span key={idx} style={{
                    padding: '4px 12px',
                    background: 'var(--accent-primary-light)',
                    color: 'var(--accent-primary)',
                    fontSize: '12px',
                    borderRadius: '20px'
                  }}>
                    {tag}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>

        <div style={{
          display: 'flex',
          gap: '8px',
          alignItems: 'center'
        }}>
          <button
            onClick={onCopy}
            style={{
              padding: '8px 16px',
              fontSize: '13px',
              background: 'var(--bg-primary)',
              color: 'var(--text-primary)',
              border: '1px solid var(--border-color)',
              borderRadius: '6px',
              cursor: 'pointer'
            }}
          >
            复制脚本
          </button>
          <button
            onClick={onRegenerate}
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
            重新生成
          </button>
        </div>
      </div>

      {/* 导出选项 */}
      <div style={{
        borderTop: '1px solid var(--border-color)',
        paddingTop: '16px'
      }}>
        <div style={{
          fontSize: '13px',
          color: 'var(--text-secondary)',
          marginBottom: '12px',
          fontWeight: '500'
        }}>
          导出格式
        </div>
        <div style={{
          display: 'flex',
          gap: '8px'
        }}>
          <button
            onClick={() => onExport('json')}
            style={{
              padding: '8px 16px',
              fontSize: '13px',
              background: 'var(--bg-primary)',
              color: 'var(--text-primary)',
              border: '1px solid var(--border-color)',
              borderRadius: '6px',
              cursor: 'pointer'
            }}
          >
            JSON
          </button>
          <button
            onClick={() => onExport('txt')}
            style={{
              padding: '8px 16px',
              fontSize: '13px',
              background: 'var(--bg-primary)',
              color: 'var(--text-primary)',
              border: '1px solid var(--border-color)',
              borderRadius: '6px',
              cursor: 'pointer'
            }}
          >
            TXT
          </button>
          <button
            onClick={() => onExport('csv')}
            style={{
              padding: '8px 16px',
              fontSize: '13px',
              background: 'var(--bg-primary)',
              color: 'var(--text-primary)',
              border: '1px solid var(--border-color)',
              borderRadius: '6px',
              cursor: 'pointer'
            }}
          >
            CSV
          </button>
        </div>
      </div>
    </div>
  )
}

function ShootScriptPage() {
  const {
    topic, setTopic,
    platform, setPlatform,
    duration, setDuration,
    style, setStyle,
    persona, setPersona,
    result, setResult,
    loading, error, setError,
    generate,
    exportScript,
    regenerate,
    copyScript,
    platforms,
    durations,
    styles,
    // v3 流式
    enableReasoning, setEnableReasoning,
    reasoning, reasoningSupported,
    isStreaming,
    hotTopic, setHotTopic,  // C1
  } = useShootScript()
  const { activeHotTopic, clearActiveHotTopic } = useHotTopic()

  // C1: 消费来自 HotSearchPage 的活跃热点
  useEffect(() => {
    if (activeHotTopic && !hotTopic) {
      setHotTopic(activeHotTopic)
      if (!topic.trim()) {
        setTopic(activeHotTopic.title)
      }
    }
  }, [activeHotTopic, hotTopic, setHotTopic, setTopic, topic])

  const handleExport = (format) => {
    exportScript(format)
  }

  const handleShotClick = (shot) => {
    // 可以添加更多交互，如编辑镜头等
    console.log('Selected shot:', shot)
  }

  // C1: 来自热点的来源 banner
  const sourceHotTopic = hotTopic || activeHotTopic

  return (
    <PageContainer title="拍摄脚本生成" description="AI自动生成分镜头脚本，适配不同平台">
      {sourceHotTopic && (
        <div style={{
          maxWidth: '900px',
          margin: '0 auto 16px',
          padding: '10px 16px',
          background: 'linear-gradient(135deg, rgba(255,107,107,0.08) 0%, rgba(255,107,107,0.03) 100%)',
          borderLeft: '3px solid #ff6b6b',
          borderRadius: '6px',
          fontSize: '13px',
          color: 'var(--text-primary)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
        }}>
          <div>
            <span style={{ fontWeight: '600' }}>🔥 来自热点：</span>
            <span style={{ color: 'var(--text-secondary)' }}>{sourceHotTopic.title}</span>
            {sourceHotTopic.source && (
              <span style={{ color: 'var(--text-tertiary)', marginLeft: '8px' }}>
                · 来源 {sourceHotTopic.source}
              </span>
            )}
          </div>
          <button
            onClick={() => {
              if (setHotTopic) setHotTopic(null)
              clearActiveHotTopic()
            }}
            style={{
              background: 'transparent',
              border: 'none',
              color: 'var(--text-tertiary)',
              cursor: 'pointer',
              fontSize: '16px',
              padding: '0 8px',
            }}
            title="清除来源标记"
          >×</button>
        </div>
      )}

      <div style={{ maxWidth: '900px', margin: '0 auto' }}>
        {/* 人设输入 */}
        <div style={{ marginBottom: '24px' }}>
          <div style={{
            fontSize: '12px',
            color: 'var(--text-tertiary)',
            marginBottom: '8px'
          }}>
            人设（决定脚本风格和视角）
          </div>
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

        {/* 话题输入 */}
        <div style={{ marginBottom: '24px' }}>
          <div style={{
            fontSize: '12px',
            color: 'var(--text-tertiary)',
            marginBottom: '8px'
          }}>
            话题/主题
          </div>
          <textarea
            value={topic}
            onChange={(e) => setTopic(e.target.value)}
            placeholder="输入你想要创作的话题...&#10;&#10;例如：&#10;• 如何提高工作效率&#10;• 保险入门指南&#10;• AI时代的创业机会"
            rows={3}
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

        {/* 平台选择 */}
        <PlatformSelector
          platform={platform}
          setPlatform={setPlatform}
          platforms={platforms}
          disabled={loading}
        />

        {/* 时长选择（B 站不显示，因为 B 站走默认 5-10 分钟） */}
        {platform !== 'bilibili' && (
          <div style={{ marginBottom: '24px' }}>
            <div style={{
              fontSize: '12px',
              color: 'var(--text-tertiary)',
              marginBottom: '12px'
            }}>
              视频时长
            </div>
            <div style={{
              display: 'flex',
              gap: '12px',
              flexWrap: 'wrap'
            }}>
              {durations.map((d) => (
                <button
                  key={d.id}
                  onClick={() => setDuration(d.id)}
                  disabled={loading}
                  style={{
                    padding: '14px 22px',
                    fontSize: '14px',
                    background: duration === d.id ? 'var(--accent-primary)' : 'var(--bg-secondary)',
                    color: duration === d.id ? 'white' : 'var(--text-primary)',
                    border: duration === d.id ? 'none' : '1px solid var(--border-color)',
                    borderRadius: '10px',
                    cursor: loading ? 'not-allowed' : 'pointer',
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    gap: '4px',
                    opacity: loading ? 0.5 : 1,
                    transition: 'all 0.2s'
                  }}
                >
                  <span style={{ fontSize: '15px', fontWeight: '600' }}>{d.name}</span>
                  <span style={{
                    fontSize: '11px',
                    color: duration === d.id ? 'rgba(255,255,255,0.8)' : 'var(--text-tertiary)'
                  }}>
                    {d.description}
                  </span>
                </button>
              ))}
            </div>
          </div>
        )}

        {/* 风格选择 */}
        <StyleSelector
          style={style}
          setStyle={setStyle}
          styles={styles}
          disabled={loading}
        />

        {/* v3：深度思考开关 */}
        <div style={{ marginBottom: '16px' }}>
          <ReasoningToggle
            enabled={enableReasoning}
            onChange={setEnableReasoning}
          />
        </div>

        {/* 错误提示 */}
        {error && (
          <div style={{
            padding: '12px 16px',
            marginBottom: '24px',
            background: 'rgba(239, 68, 68, 0.1)',
            border: '1px solid rgba(239, 68, 68, 0.3)',
            borderRadius: '8px',
            fontSize: '13px',
            color: '#dc2626'
          }}>
            {error}
          </div>
        )}

        {/* 生成按钮 */}
        <button
          onClick={generate}
          disabled={loading || !topic.trim()}
          style={{
            width: '100%',
            padding: '16px 24px',
            fontSize: '16px',
            fontWeight: '600',
            background: loading || !topic.trim() ? 'var(--text-tertiary)' : 'var(--accent-primary)',
            color: 'white',
            border: 'none',
            borderRadius: '10px',
            cursor: loading || !topic.trim() ? 'not-allowed' : 'pointer',
            opacity: loading || !topic.trim() ? 0.6 : 1
          }}
        >
          {loading ? (
            <>
              <span className="loading-spinner" style={{ marginRight: '8px' }}></span>
              生成中…
            </>
          ) : (
            <>
              <span style={{ marginRight: '8px' }}>🎬</span>
              生成拍摄脚本
            </>
          )}
        </button>

        {/* 流式阶段：thinking 折叠区 + 进度提示（shots 仍按完成再渲染） */}
        {isStreaming && !result && (
          <StreamingIndicator
            reasoning={reasoning}
            reasoningSupported={reasoningSupported}
          />
        )}

        {/* 生成结果 */}
        {result && (
          <>
            <div style={{
              padding: '16px',
              marginTop: '32px',
              marginBottom: '16px',
              background: 'rgba(59, 130, 246, 0.1)',
              borderRadius: '8px',
              border: '1px solid var(--accent-primary)',
              textAlign: 'center'
            }}>
              <div style={{
                fontSize: '14px',
                color: 'var(--text-primary)',
                marginBottom: '8px'
              }}>
                <span style={{ fontSize: '18px' }}>📊</span>
                <strong>预计时长：</strong>{result.estimated_duration}
              </div>
              <div style={{
                fontSize: '12px',
                color: 'var(--text-tertiary)'
              }}>
                基于{result.platform}平台特点生成{result.style}风格脚本
              </div>
            </div>

            <ScriptInfo
              result={result}
              onCopy={copyScript}
              onExport={handleExport}
              onRegenerate={regenerate}
            />

            <div style={{
              marginTop: '32px',
              marginBottom: '16px'
            }}>
              <div style={{
                fontSize: '14px',
                fontWeight: '600',
                color: 'var(--text-secondary)',
                marginBottom: '16px'
              }}>
                分镜头脚本
              </div>
              <ShotList
                shots={result.shots}
                onShotClick={handleShotClick}
              />
            </div>
          </>
        )}
      </div>
    </PageContainer>
  )
}

export default ShootScriptPage
