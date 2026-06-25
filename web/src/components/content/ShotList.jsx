/**
 * 分镜头列表组件
 */
import { useState } from 'react'

function ShotList({ shots, onShotClick }) {
  const [expandedShot, setExpandedShot] = useState(null)

  const handleShotClick = (shot) => {
    setExpandedShot(expandedShot === shot.shot_number ? null : shot.shot_number)
    if (onShotClick) {
      onShotClick(shot)
    }
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
      {shots.map((shot, index) => (
        <div
          key={shot.shot_number}
          style={{
            padding: '16px',
            background: expandedShot === shot.shot_number
              ? 'var(--accent-primary-light)'
              : 'var(--bg-secondary)',
            borderRadius: '12px',
            border: expandedShot === shot.shot_number
              ? '2px solid var(--accent-primary)'
              : '1px solid var(--border-color)',
            cursor: 'pointer',
            transition: 'all 0.2s'
          }}
          onClick={() => handleShotClick(shot)}
        >
          {/* 镜头头部 */}
          <div style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            marginBottom: '12px'
          }}>
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: '8px'
            }}>
              <span style={{
                padding: '4px 10px',
                background: 'var(--accent-primary)',
                color: 'white',
                fontSize: '12px',
                fontWeight: '600',
                borderRadius: '6px'
              }}>
                镜头{shot.shot_number}
              </span>
              <span style={{
                padding: '4px 10px',
                background: 'var(--bg-primary)',
                color: 'var(--text-tertiary)',
                fontSize: '11px',
                borderRadius: '4px'
              }}>
                {shot.duration}
              </span>
            </div>
            <span style={{ fontSize: '20px' }}>
              {expandedShot === shot.shot_number ? '▼' : '▶'}
            </span>
          </div>

          {/* 镜头内容 */}
          <div style={{
            display: 'flex',
            flexDirection: 'column',
            gap: '10px'
          }}>
            <div>
              <span style={{
                fontSize: '12px',
                color: 'var(--text-tertiary)',
                marginRight: '6px'
              }}>
                画面:
              </span>
              <span style={{
                fontSize: '14px',
                color: 'var(--text-primary)',
                lineHeight: '1.5'
              }}>
                {shot.visual_description}
              </span>
            </div>

            <div>
              <span style={{
                fontSize: '12px',
                color: 'var(--text-tertiary)',
                marginRight: '6px'
              }}>
                台词:
              </span>
              <span style={{
                fontSize: '14px',
                color: 'var(--text-primary)',
                lineHeight: '1.6',
                fontWeight: '500'
              }}>
                {shot.dialogue}
              </span>
            </div>

            {shot.scene_suggestion && (
              <div>
                <span style={{
                  fontSize: '12px',
                  color: 'var(--text-tertiary)',
                  marginRight: '6px'
                }}>
                  场景:
                </span>
                <span style={{
                  fontSize: '13px',
                  color: 'var(--text-secondary)',
                  background: 'var(--bg-primary)',
                  padding: '4px 8px',
                  borderRadius: '4px'
                }}>
                  {shot.scene_suggestion}
                </span>
              </div>
            )}

            {shot.camera_movement && (
              <div>
                <span style={{
                  fontSize: '12px',
                  color: 'var(--text-tertiary)',
                  marginRight: '6px'
                }}>
                  运镜:
                </span>
                <span style={{
                  fontSize: '13px',
                  color: 'var(--text-secondary)',
                  background: 'var(--bg-primary)',
                  padding: '4px 8px',
                  borderRadius: '4px'
                }}>
                  {shot.camera_movement}
                </span>
              </div>
            )}
          </div>
        </div>
      ))}
    </div>
  )
}

export default ShotList
