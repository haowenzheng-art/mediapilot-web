import { motion } from 'framer-motion'

const FEATURES = [
  { id: 'shoot-script', icon: '📝', title: '拍摄脚本', desc: 'AI 生成视频拍摄脚本' },
  { id: 'trending', icon: '⚡', title: '热点搜索', desc: '发现行业热门话题' },
  { id: 'copywriting', icon: '🎤', title: '口播文案', desc: '一键生成口播内容' },
  { id: 'video-analysis', icon: '🎥', title: '视频分析', desc: '解析视频内容数据' },
  { id: 'transcription', icon: '💬', title: '语音转写', desc: '音频转文字内容' },
  { id: 'subscription', icon: '📬', title: '话题订阅', desc: '订阅热点自动推送' },
]

export default function HeroSection({ currentUser, onLoginClick, onFeatureClick }) {
  return (
    <div className="hero-cover">
      <div className="hero-content">
        {/* Logo */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '12px',
            marginBottom: '48px',
          }}
        >
          <span style={{ fontSize: '48px' }}>🚀</span>
          <span style={{
            fontSize: '40px',
            fontWeight: '700',
            letterSpacing: '-0.03em',
          }}>
            Media
            <span style={{
              background: 'linear-gradient(135deg, #ffffff, #cccccc)',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
              backgroundClip: 'text',
            }}>Pilot</span>
          </span>
        </motion.div>

        {/* Title */}
        <motion.h1
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.5, delay: 0.1 }}
          className="hero-title"
          style={{
            fontSize: 'clamp(32px, 6vw, 56px)',
            fontWeight: '700',
            lineHeight: '1.07',
            marginBottom: '24px',
            letterSpacing: '-0.03em',
          }}
        >
          内容创作全流程<br />
          <span style={{
            background: 'linear-gradient(135deg, #ffffff, #cccccc)',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
            backgroundClip: 'text',
          }}>
            一站式解决方案
          </span>
        </motion.h1>

        {/* Subtitle */}
        <motion.p
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.5, delay: 0.2 }}
          style={{
            fontSize: 'clamp(14px, 2vw, 18px)',
            color: 'var(--text-secondary)',
            lineHeight: '1.7',
            letterSpacing: '-0.2px',
            marginBottom: '64px',
            maxWidth: '600px',
            margin: '0 auto 64px',
          }}
        >
          从热点发现到内容创作，从数据分析到发布规划<br />
          让每一个创作环节都更高效
        </motion.p>

        {/* Features */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.3 }}
        >
          <div className="feature-cards">
            {FEATURES.map((feature, index) => (
              <motion.div
                key={feature.id}
                className="feature-card"
                onClick={() => onFeatureClick(feature.id)}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3, delay: 0.4 + index * 0.05 }}
                whileHover={{
                  y: -4,
                  scale: 1.02,
                  boxShadow: 'rgba(0,0,0,0.12) 0px 8px 24px 0px',
                }}
                style={{
                  padding: '28px',
                  background: 'linear-gradient(180deg, #1a1a1a 0%, #111111 100%)',
                  borderRadius: '12px',
                  boxShadow: 'rgba(0,0,0,0.06) 0px 2px 8px 0px',
                  border: 'none',
                  cursor: 'pointer',
                }}
              >
                <div className="feature-icon">{feature.icon}</div>
                <h3 className="feature-title">{feature.title}</h3>
                <p className="feature-desc">{feature.desc}</p>
              </motion.div>
            ))}
          </div>
        </motion.div>

        {/* CTA Buttons */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.5, delay: 0.5 }}
          style={{
            display: 'flex',
            gap: '16px',
            justifyContent: 'center',
            marginTop: '48px',
            flexWrap: 'wrap',
          }}
        >
          {!currentUser ? (
            <button
              onClick={onLoginClick}
              className="btn btn-primary btn-lg"
              style={{ minWidth: '140px' }}
            >
              登录开始使用
            </button>
          ) : (
            <button
              onClick={() => onFeatureClick('shoot-script')}
              className="btn btn-primary btn-lg"
              style={{ minWidth: '140px' }}
            >
              开始创作
            </button>
          )}
          <button
            onClick={() => onFeatureClick('trending')}
            className="btn btn-secondary btn-lg"
            style={{ minWidth: '140px' }}
          >
            发现热点
          </button>
        </motion.div>
      </div>
    </div>
  )
}
