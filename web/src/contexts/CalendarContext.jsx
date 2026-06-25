import { createContext, useContext, useState, useEffect } from 'react'

const CalendarContext = createContext()

export function CalendarProvider({ children }) {
  const [calendarNotes, setCalendarNotes] = useState(() => {
    const saved = localStorage.getItem('mediapilot-calendar-notes')
    return saved ? JSON.parse(saved) : {}
  })

  useEffect(() => {
    localStorage.setItem('mediapilot-calendar-notes', JSON.stringify(calendarNotes))
  }, [calendarNotes])

  const saveCalendarNote = (dateKey, note) => {
    setCalendarNotes(prev => ({ ...prev, [dateKey]: note }))
  }

  const getCalendarNote = (dateKey) => {
    return calendarNotes[dateKey] || ''
  }

  const deleteCalendarNote = (dateKey) => {
    setCalendarNotes(prev => {
      const newNotes = { ...prev }
      delete newNotes[dateKey]
      return newNotes
    })
  }

  return (
    <CalendarContext.Provider value={{ calendarNotes, saveCalendarNote, getCalendarNote, deleteCalendarNote }}>
      {children}
    </CalendarContext.Provider>
  )
}

export function useCalendarNotes() {
  return useContext(CalendarContext)
}
