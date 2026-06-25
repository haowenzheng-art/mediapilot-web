import { createContext, useContext, useState, useEffect } from 'react'

const DEFAULT_TAGS = [
  { id: 'marketing', title: '营销内容', color: '#000000' },
  { id: 'brand', title: '个人品牌', color: '#333333' },
  { id: 'service', title: '客户服务', color: '#666666' },
  { id: 'content', title: '内容创作', color: '#333333' },
  { id: 'learning', title: '学习成长', color: '#999999' },
  { id: 'other', title: '其他', color: '#666666' }
]

const TagsContext = createContext()

export function TagsProvider({ children }) {
  const [customTags, setCustomTags] = useState(() => {
    const saved = localStorage.getItem('mediapilot-custom-tags')
    return saved ? JSON.parse(saved) : DEFAULT_TAGS
  })

  useEffect(() => {
    localStorage.setItem('mediapilot-custom-tags', JSON.stringify(customTags))
  }, [customTags])

  const addCustomTag = (tag) => {
    const newTag = { ...tag, id: `custom-${Date.now()}` }
    setCustomTags(prev => [...prev, newTag])
    return newTag
  }

  const deleteCustomTag = (tagId) => {
    setCustomTags(prev => prev.filter(t => t.id !== tagId))
  }

  const updateCustomTag = (tagId, updates) => {
    setCustomTags(prev => prev.map(t => t.id === tagId ? { ...t, ...updates } : t))
  }

  const resetTags = () => {
    setCustomTags(DEFAULT_TAGS)
  }

  return (
    <TagsContext.Provider value={{ customTags, addCustomTag, deleteCustomTag, updateCustomTag, resetTags, DEFAULT_TAGS }}>
      {children}
    </TagsContext.Provider>
  )
}

export function useTags() {
  return useContext(TagsContext)
}
