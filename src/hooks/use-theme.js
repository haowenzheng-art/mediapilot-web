import { useState, useEffect } from 'react'

const THEMES = [
  { id: 'space', name: '太空赛博' },
  { id: 'chinese', name: '中国风' },
  { id: 'cyberpunk', name: '赛博朋克' },
  { id: 'pixar', name: '皮克斯漫画' },
  { id: 'anime', name: '日漫风' },
  { id: 'abstract', name: '伦敦艺术抽象' },
]

export function useTheme() {
  const [theme, setTheme] = useState(() => {
    return localStorage.getItem('mediapilot-theme') || 'space'
  })

  useEffect(() => {
    const root = window.document.documentElement
    root.setAttribute('data-theme', theme)
    localStorage.setItem('mediapilot-theme', theme)
  }, [theme])

  return { theme, setTheme, themes: THEMES }
}