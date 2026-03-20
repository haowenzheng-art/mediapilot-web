import { createContext, useContext, useState, useEffect } from 'react'
import { THEMES } from '../themes'

const themeIdMap = {
  'space': 'spaceCyber',
  'chinese': 'chineseStyle',
  'cyberpunk': 'cyberpunk',
  'pixar': 'pixar',
  'anime': 'anime',
  'abstract': 'abstract',
}

const ThemeContext = createContext()

export function ThemeProvider({ children }) {
  const [currentThemeId, setCurrentThemeId] = useState(() => {
    const saved = localStorage.getItem('mediapilot-theme')
    if (saved && themeIdMap[saved]) {
      return themeIdMap[saved]
    }
    return saved || 'spaceCyber'
  })

  const currentTheme = THEMES[currentThemeId] || THEMES.spaceCyber

  useEffect(() => {
    const root = document.documentElement
    Object.entries(currentTheme.cssVars).forEach(([key, value]) => {
      root.style.setProperty(key, value)
    })
    root.setAttribute('data-theme', currentThemeId)
    localStorage.setItem('mediapilot-theme', currentThemeId)
  }, [currentThemeId, currentTheme])

  const setTheme = (themeId) => {
    const newThemeId = themeIdMap[themeId] || themeId
    if (THEMES[newThemeId]) {
      setCurrentThemeId(newThemeId)
    }
  }

  return (
    <ThemeContext.Provider value={{
      currentTheme,
      currentThemeId,
      setTheme,
      themes: THEMES,
    }}>
      {children}
    </ThemeContext.Provider>
  )
}

export function useTheme() {
  return useContext(ThemeContext)
}
