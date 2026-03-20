import { useTheme } from '../contexts/ThemeContext'
import { motion } from 'framer-motion'

function ThemeSwitcher({ compact = false }) {
  const { currentThemeId, setTheme, themes } = useTheme()

  return (
    <div className="theme-switcher">
      {!compact && <span className="theme-label">主题：</span>}
      <div className="theme-buttons">
        {Object.values(themes).map((theme) => (
          <motion.button
            key={theme.id}
            className={`theme-btn ${currentThemeId === theme.id ? 'active' : ''}`}
            onClick={() => setTheme(theme.id)}
            whileHover={{ scale: compact ? 1.05 : 1.03 }}
            whileTap={{ scale: 0.95 }}
            title={`切换为${theme.name}风格`}
            aria-label={`切换为${theme.name}主题`}
          >
            <span className="theme-icon">{theme.icon}</span>
            {!compact && <span className="theme-name">{theme.name}</span>}
          </motion.button>
        ))}
      </div>

      <style jsx>{`
        .theme-switcher {
          display: flex;
          align-items: center;
          gap: 0.75rem;
        }

        .theme-label {
          font-size: 0.875rem;
          color: var(--text-secondary);
          white-space: nowrap;
        }

        .theme-buttons {
          display: flex;
          gap: 0.5rem;
          flex-wrap: wrap;
        }

        .theme-btn {
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 0.25rem;
          padding: 0.5rem 0.75rem;
          background: var(--glass-bg);
          backdrop-filter: blur(var(--glass-blur));
          -webkit-backdrop-filter: blur(var(--glass-blur));
          border: 1px solid var(--border-color);
          border-radius: 8px;
          cursor: pointer;
          transition: all 0.3s ease;
          color: var(--text-primary);
        }

        .theme-btn:hover {
          background: var(--card-bg);
          transform: translateY(-2px);
        }

        .theme-btn.active {
          background: var(--accent-primary);
          border-color: var(--accent-primary);
          color: var(--bg-primary);
          box-shadow: 0 0 15px var(--shadow-color);
        }

        .theme-icon {
          font-size: 1.25rem;
        }

        .theme-name {
          font-size: 0.7rem;
          white-space: nowrap;
        }

        @media (max-width: 768px) {
          .theme-switcher {
            flex-direction: column;
            align-items: flex-start;
          }

          .theme-name {
            display: none;
          }

          .theme-btn {
            padding: 0.5rem;
          }
        }
      `}</style>
    </div>
  )
}

export default ThemeSwitcher
