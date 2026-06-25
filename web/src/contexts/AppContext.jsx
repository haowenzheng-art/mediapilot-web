/**
 * AppContext — 兼容层
 * 重新导出拆分后的 HistoryContext, CalendarContext, TagsContext
 * 保持 useApp 和 HISTORY_TYPES 的向后兼容
 */
import { useHistory, HISTORY_TYPES } from './HistoryContext'
import { useCalendarNotes } from './CalendarContext'
import { useTags } from './TagsContext'

export { HISTORY_TYPES }

// 兼容旧的 useApp() 调用
export function useApp() {
  const history = useHistory()
  const calendar = useCalendarNotes()
  const tags = useTags()

  return {
    // 历史
    history: history.history,
    addHistory: history.addHistory,
    deleteHistory: history.deleteHistory,
    clearHistory: history.clearHistory,
    getHistoryByType: history.getHistoryByType,
    // 日历
    calendarNotes: calendar.calendarNotes,
    saveCalendarNote: calendar.saveCalendarNote,
    getCalendarNote: calendar.getCalendarNote,
    deleteCalendarNote: calendar.deleteCalendarNote,
    // 标签
    customTags: tags.customTags,
    addCustomTag: tags.addCustomTag,
    deleteCustomTag: tags.deleteCustomTag,
    updateCustomTag: tags.updateCustomTag,
    resetTags: tags.resetTags,
    DEFAULT_TAGS: tags.DEFAULT_TAGS,
  }
}

// 兼容旧的 AppProvider — 组合三个 Provider
import { HistoryProvider } from './HistoryContext'
import { CalendarProvider } from './CalendarContext'
import { TagsProvider } from './TagsContext'

export function AppProvider({ children }) {
  return (
    <HistoryProvider>
      <CalendarProvider>
        <TagsProvider>
          {children}
        </TagsProvider>
      </CalendarProvider>
    </HistoryProvider>
  )
}
