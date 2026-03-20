import { useState } from 'react'
import { useApp } from '../contexts/AppContext'

function CalendarPage() {
  const [currentDate, setCurrentDate] = useState(new Date())
  const [selectedDate, setSelectedDate] = useState(null)
  const [noteInput, setNoteInput] = useState('')
  const { saveCalendarNote, getCalendarNote } = useApp()

  // 香港公众假期（2026年示例）- 红色点
  const hkHolidays = {
    '2026-1-1': '元旦',
    '2026-1-28': '农历年初一',
    '2026-1-29': '农历年初二',
    '2026-1-30': '农历年初三',
    '2026-4-4': '清明节',
    '2026-4-17': '耶稣受难节',
    '2026-4-18': '耶稣受难节翌日',
    '2026-4-20': '复活节星期一',
    '2026-5-1': '劳动节',
    '2026-5-5': '佛诞',
    '2026-6-20': '端午节',
    '2026-7-1': '香港特别行政区成立纪念日',
    '2026-9-28': '中秋节翌日',
    '2026-10-1': '国庆日',
    '2026-10-2': '国庆日翌日',
    '2026-10-21': '重阳节',
    '2026-12-25': '圣诞节',
    '2026-12-26': '圣诞节后第一个周日'
  }

  // 大陆公众假期（2026年示例）- 蓝色点
  const cnHolidays = {
    '2026-1-1': '元旦',
    '2026-1-28': '春节',
    '2026-1-29': '春节',
    '2026-1-30': '春节',
    '2026-1-31': '春节',
    '2026-2-1': '春节',
    '2026-2-2': '春节',
    '2026-4-4': '清明节',
    '2026-5-1': '劳动节',
    '2026-5-2': '劳动节',
    '2026-5-3': '劳动节',
    '2026-5-4': '劳动节',
    '2026-5-5': '劳动节',
    '2026-6-20': '端午节',
    '2026-10-1': '国庆节',
    '2026-10-2': '国庆节',
    '2026-10-3': '国庆节',
    '2026-10-4': '国庆节',
    '2026-10-5': '国庆节',
    '2026-10-6': '国庆节',
    '2026-10-7': '国庆节'
  }

  // 热点内容示例
  const hotTopics = {
    '2026-1-1': [{ title: '2026年元旦假期旅游热', url: '#' }],
    '2026-1-28': [{ title: '春节营销战打响', url: '#' }],
    '2026-3-8': [{ title: '女神节营销趋势', url: '#' }, { title: '女性消费力报告', url: '#' }],
    '2026-5-1': [{ title: '五一黄金周消费报告', url: '#' }],
    '2026-6-18': [{ title: '618电商大战预热', url: '#' }],
    '2026-11-11': [{ title: '双十一购物节前瞻', url: '#' }]
  }

  const getDaysInMonth = (date) => {
    const year = date.getFullYear()
    const month = date.getMonth()
    const days = new Date(year, month + 1, 0).getDate()
    const firstDay = new Date(year, month, 1).getDay()
    return { days, firstDay }
  }

  const { days, firstDay } = getDaysInMonth(currentDate)

  const prevMonth = () => {
    setCurrentDate(new Date(currentDate.getFullYear(), currentDate.getMonth() - 1, 1))
  }

  const nextMonth = () => {
    setCurrentDate(new Date(currentDate.getFullYear(), currentDate.getMonth() + 1, 1))
  }

  const weekDays = ['日', '一', '二', '三', '四', '五', '六']
  const monthNames = ['1月', '2月', '3月', '4月', '5月', '6月', '7月', '8月', '9月', '10月', '11月', '12月']

  const getDateKey = (year, month, day) => {
    return `${year}-${month + 1}-${day}`
  }

  const isToday = (year, month, day) => {
    const today = new Date()
    return today.getFullYear() === year && today.getMonth() === month && today.getDate() === day
  }

  const selectDate = (day) => {
    const dateKey = getDateKey(currentDate.getFullYear(), currentDate.getMonth(), day)
    setSelectedDate(dateKey)
    setNoteInput(getCalendarNote(dateKey) || '')
  }

  const saveNote = () => {
    if (selectedDate && noteInput.trim()) {
      saveCalendarNote(selectedDate, noteInput)
    }
  }

  // 生成日历格子
  const calendarCells = []

  // 前面的空格
  for (let i = 0; i < firstDay; i++) {
    calendarCells.push(<td key={`empty-${i}`} className="p-1"></td>)
  }

  // 日期
  for (let day = 1; day <= days; day++) {
    const dateKey = getDateKey(currentDate.getFullYear(), currentDate.getMonth(), day)
    const isHkHoliday = hkHolidays[dateKey]
    const isCnHoliday = cnHolidays[dateKey]
    const hasNote = getCalendarNote(dateKey)
    const isSelected = selectedDate === dateKey
    const today = isToday(currentDate.getFullYear(), currentDate.getMonth(), day)

    calendarCells.push(
      <td key={day} className="p-1 text-center">
        <button
          onClick={() => selectDate(day)}
          className={`
            w-full aspect-square rounded-lg flex flex-col items-center justify-center relative
            transition-all duration-200
            ${isSelected ? 'bg-accent text-white' : 'hover:bg-bg-light'}
            ${today ? 'ring-2 ring-accent' : ''}
          `}
        >
          <span className="text-sm font-medium">{day}</span>

          {/* 假期标记 */}
          <div className="flex gap-1 mt-1">
            {isHkHoliday && <span className="w-2 h-2 rounded-full bg-red-500" title={isHkHoliday}></span>}
            {isCnHoliday && <span className="w-2 h-2 rounded-full bg-blue-500" title={isCnHoliday}></span>}
          </div>

          {/* 备注标记 */}
          {hasNote && <span className="absolute top-1 right-1 w-2 h-2 rounded-full bg-green-500"></span>}
        </button>
      </td>
    )
  }

  // 分成几行
  const rows = []
  for (let i = 0; i < calendarCells.length; i += 7) {
    rows.push(
      <tr key={`row-${i / 7}`}>
        {calendarCells.slice(i, i + 7)}
      </tr>
    )
  }

  const selectedDateHotTopics = selectedDate ? hotTopics[selectedDate] : null
  const selectedDateObj = selectedDate ? new Date(selectedDate) : null

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <h2 className="text-2xl font-bold mb-6 flex items-center gap-2">
        <span>📅</span> 发布日历
      </h2>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* 日历部分 */}
        <div className="card">
          {/* 月份导航 */}
          <div className="flex items-center justify-between mb-4">
            <button onClick={prevMonth} className="btn btn-secondary px-3 py-1 text-sm">◀ 上月</button>
            <h3 className="text-lg font-semibold">{currentDate.getFullYear()}年 {monthNames[currentDate.getMonth()]}</h3>
            <button onClick={nextMonth} className="btn btn-secondary px-3 py-1 text-sm">下月 ▶</button>
          </div>

          {/* 日历表格 */}
          <table className="w-full">
            <thead>
              <tr>
                {weekDays.map((day, idx) => (
                  <th key={idx} className={`text-center py-2 text-xs font-bold ${idx === 0 || idx === 6 ? 'text-red-500' : ''}`}>
                    {day}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {rows}
            </tbody>
          </table>

          {/* 图例 */}
          <div className="mt-4 flex flex-wrap gap-4 text-xs text-text-secondary">
            <div className="flex items-center gap-1">
              <span className="w-2 h-2 rounded-full bg-red-500"></span>
              <span>香港假期</span>
            </div>
            <div className="flex items-center gap-1">
              <span className="w-2 h-2 rounded-full bg-blue-500"></span>
              <span>大陆假期</span>
            </div>
            <div className="flex items-center gap-1">
              <span className="w-2 h-2 rounded-full bg-green-500"></span>
              <span>有备注</span>
            </div>
          </div>
        </div>

        {/* 备注和热点部分 */}
        <div className="card">
          {selectedDate ? (
            <>
              <h3 className="text-lg font-semibold mb-4">
                {selectedDateObj?.getMonth() + 1}月{selectedDateObj?.getDate()}日
              </h3>

              {/* 备注输入 */}
              <div className="mb-6">
                <h4 className="text-sm font-medium mb-2">📝 备注</h4>
                <textarea
                  value={noteInput}
                  onChange={(e) => setNoteInput(e.target.value)}
                  placeholder="添加备注..."
                  className="w-full h-24 p-3 rounded-lg border border-border bg-bg-secondary focus:outline-none focus:ring-2 focus:ring-accent focus:border-transparent"
                ></textarea>
                <button onClick={saveNote} className="btn btn-primary mt-2 px-4 py-2 text-sm">
                  保存备注
                </button>
              </div>

              {/* 热点链接 */}
              {selectedDateHotTopics && selectedDateHotTopics.length > 0 && (
                <div>
                  <h4 className="text-sm font-medium mb-2">🔥 当日热点</h4>
                  <ul className="space-y-2">
                    {selectedDateHotTopics.map((topic, idx) => (
                      <li key={idx}>
                        <a href={topic.url} className="text-sm text-accent hover:underline">
                          → {topic.title}
                        </a>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* 假期信息 */}
              {(() => {
                const dateKey = selectedDate
                const hkHoliday = hkHolidays[dateKey]
                const cnHoliday = cnHolidays[dateKey]
                if (hkHoliday || cnHoliday) {
                  return (
                    <div className="mt-6">
                      <h4 className="text-sm font-medium mb-2">🎊 假期</h4>
                      <div className="space-y-1">
                        {hkHoliday && (
                          <div className="flex items-center gap-2 text-sm">
                            <span className="w-2 h-2 rounded-full bg-red-500"></span>
                            <span>香港: {hkHoliday}</span>
                          </div>
                        )}
                        {cnHoliday && (
                          <div className="flex items-center gap-2 text-sm">
                            <span className="w-2 h-2 rounded-full bg-blue-500"></span>
                            <span>大陆: {cnHoliday}</span>
                          </div>
                        )}
                      </div>
                    </div>
                  )
                }
                return null
              })()}
            </>
          ) : (
            <div className="text-center py-12 text-text-secondary">
              <p className="text-4xl mb-2">👆</p>
              <p>点击日期查看详情</p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default CalendarPage
