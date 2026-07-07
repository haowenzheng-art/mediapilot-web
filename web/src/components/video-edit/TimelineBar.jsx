/**
 * 视频剪辑时间轴可视化（v3 改造）
 *
 * 横向 bar（宽度 = originalDuration 秒）：
 * - 绿色 = 保留段（kept_segments）
 * - 红色 = 删除段（removed_segments），hover 显示删除原因
 * - 底部 10% 间隔的时间刻度
 *
 * 让用户一眼看出哪些时段被剪掉了、为什么剪。
 */
export function TimelineBar({ keptSegments, removedSegments, originalDuration }) {
  if (!originalDuration || originalDuration <= 0) return null

  const totalSec = originalDuration

  // 标准化 segments 到百分比宽度
  const keptPct = (keptSegments || []).map((seg) => {
    const [start, end] = Array.isArray(seg) ? seg : [seg.start, seg.end]
    return {
      start,
      end,
      leftPct: Math.max(0, (start / totalSec) * 100),
      widthPct: Math.max(0, ((end - start) / totalSec) * 100),
    }
  })
  const removedPct = (removedSegments || []).map((seg) => {
    const start = seg.start ?? seg[0]
    const end = seg.end ?? seg[1]
    return {
      start,
      end,
      text: seg.text,
      reason: seg.reason,
      leftPct: Math.max(0, (start / totalSec) * 100),
      widthPct: Math.max(0, ((end - start) / totalSec) * 100),
    }
  })

  // 时间刻度（每 10% 一个 tick）
  const ticks = []
  for (let i = 0; i <= 10; i++) {
    const sec = Math.round((i / 10) * totalSec)
    const m = Math.floor(sec / 60)
    const s = sec % 60
    ticks.push({
      pct: i * 10,
      label: `${m}:${s.toString().padStart(2, '0')}`,
    })
  }

  return (
    <div style={{ marginTop: '8px' }}>
      <p
        style={{
          fontSize: '13px',
          fontWeight: '500',
          marginBottom: '8px',
          color: 'var(--text-secondary)',
        }}
      >
        🗺️ 剪辑时间轴
      </p>
      <div
        style={{
          position: 'relative',
          width: '100%',
          height: '32px',
          background: 'var(--bg-tertiary)',
          borderRadius: 'var(--radius-sm)',
          overflow: 'hidden',
        }}
      >
        {/* 保留段（绿） */}
        {keptPct.map((seg, idx) => (
          <div
            key={`kept-${idx}`}
            style={{
              position: 'absolute',
              left: `${seg.leftPct}%`,
              width: `${seg.widthPct}%`,
              top: 0,
              bottom: 0,
              background: 'rgba(34, 197, 94, 0.55)',
            }}
            title={`保留 ${formatTime(seg.start)} → ${formatTime(seg.end)}`}
          />
        ))}
        {/* 删除段（红） */}
        {removedPct.map((seg, idx) => (
          <div
            key={`removed-${idx}`}
            style={{
              position: 'absolute',
              left: `${seg.leftPct}%`,
              width: `${seg.widthPct}%`,
              top: 0,
              bottom: 0,
              background: 'rgba(239, 68, 68, 0.7)',
              borderLeft: '1px solid rgba(255,255,255,0.3)',
              borderRight: '1px solid rgba(255,255,255,0.3)',
              cursor: 'help',
            }}
            title={
              seg.reason
                ? `${formatTime(seg.start)} → ${formatTime(seg.end)}  ${seg.reason}${seg.text ? `\n"${seg.text}"` : ''}`
                : `${formatTime(seg.start)} → ${formatTime(seg.end)}`
            }
          />
        ))}
      </div>
      {/* 时间刻度 */}
      <div
        style={{
          position: 'relative',
          width: '100%',
          height: '20px',
          marginTop: '4px',
        }}
      >
        {ticks.map((tick, idx) => (
          <div
            key={idx}
            style={{
              position: 'absolute',
              left: `${tick.pct}%`,
              transform: 'translateX(-50%)',
              fontSize: '10px',
              color: 'var(--text-tertiary)',
              fontFamily: 'monospace',
            }}
          >
            {tick.label}
          </div>
        ))}
      </div>
      {/* 图例 */}
      <div
        style={{
          display: 'flex',
          gap: '16px',
          marginTop: '12px',
          fontSize: '11px',
          color: 'var(--text-tertiary)',
        }}
      >
        <span style={{ display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
          <span
            style={{
              display: 'inline-block',
              width: '12px',
              height: '12px',
              background: 'rgba(34, 197, 94, 0.55)',
              borderRadius: '2px',
            }}
          />
          保留段
        </span>
        <span style={{ display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
          <span
            style={{
              display: 'inline-block',
              width: '12px',
              height: '12px',
              background: 'rgba(239, 68, 68, 0.7)',
              borderRadius: '2px',
            }}
          />
          删除段（hover 查看原因）
        </span>
      </div>
    </div>
  )
}

function formatTime(sec) {
  if (sec == null) return '--:--'
  const m = Math.floor(sec / 60)
  const s = Math.floor(sec % 60)
  return `${m}:${s.toString().padStart(2, '0')}`
}