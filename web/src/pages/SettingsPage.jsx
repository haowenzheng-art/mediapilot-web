import { useEffect, useState } from 'react'
import {
  DEFAULT_PREFERENCES,
  getLocalPreferences,
  fetchPreferences,
  updatePreferences,
  resetPreferences,
} from '../services/preferences'

const THEME_OPTIONS = [
  { value: 'dark', label: '深色' },
  { value: 'light', label: '浅色' },
  { value: 'auto', label: '跟随系统' },
]

const LANGUAGE_OPTIONS = [
  { value: 'zh-CN', label: '简体中文' },
  { value: 'en-US', label: 'English' },
]

const PLATFORM_OPTIONS = [
  { value: 'douyin', label: '抖音' },
  { value: 'xiaohongshu', label: '小红书' },
  { value: 'bilibili', label: 'B站' },
]

function SettingsPage() {
  const [prefs, setPrefs] = useState(getLocalPreferences())
  const [loading, setLoading] = useState(false)
  const [status, setStatus] = useState({ kind: '', text: '' })

  useEffect(() => {
    fetchPreferences()
      .then(setPrefs)
      .catch((e) => {
        console.warn('拉取偏好失败，使用本地缓存', e)
      })
  }, [])

  const apply = async (patch) => {
    setLoading(true)
    try {
      const next = await updatePreferences(patch)
      setPrefs(next)
      setStatus({ kind: 'ok', text: '已保存' })
    } catch (e) {
      setStatus({ kind: 'err', text: e?.message || '保存失败' })
    } finally {
      setLoading(false)
      setTimeout(() => setStatus({ kind: '', text: '' }), 1500)
    }
  }

  const handleReset = async () => {
    if (!confirm('确定重置所有偏好为默认值？')) return
    setLoading(true)
    try {
      const next = await resetPreferences()
      setPrefs(next)
      setStatus({ kind: 'ok', text: '已重置为默认' })
    } catch (e) {
      setStatus({ kind: 'err', text: e?.message || '重置失败' })
    } finally {
      setLoading(false)
      setTimeout(() => setStatus({ kind: '', text: '' }), 1500)
    }
  }

  return (
    <div className="p-6 max-w-3xl mx-auto">
      <h2 className="text-2xl font-bold mb-6">设置</h2>

      <div className="space-y-6">
        <div className="card">
          <h3 className="text-lg font-semibold mb-4">外观与语言</h3>

          <div className="space-y-4">
            <Field label="主题">
              <Select
                value={prefs.theme}
                options={THEME_OPTIONS}
                disabled={loading}
                onChange={(v) => apply({ theme: v })}
              />
            </Field>

            <Field label="语言">
              <Select
                value={prefs.language}
                options={LANGUAGE_OPTIONS}
                disabled={loading}
                onChange={(v) => apply({ language: v })}
              />
            </Field>
          </div>
        </div>

        <div className="card">
          <h3 className="text-lg font-semibold mb-4">通知与编辑</h3>

          <div className="space-y-4">
            <Toggle
              label="开启推送通知"
              checked={prefs.notifications}
              disabled={loading}
              onChange={(v) => apply({ notifications: v })}
            />

            <Toggle
              label="编辑器自动保存"
              checked={prefs.auto_save}
              disabled={loading}
              onChange={(v) => apply({ auto_save: v })}
            />
          </div>
        </div>

        <div className="card">
          <h3 className="text-lg font-semibold mb-4">创作默认</h3>
          <Field label="默认平台">
            <Select
              value={prefs.default_platform}
              options={PLATFORM_OPTIONS}
              disabled={loading}
              onChange={(v) => apply({ default_platform: v })}
            />
          </Field>
        </div>

        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={handleReset}
            disabled={loading}
            className="btn btn-secondary"
          >
            重置为默认
          </button>
          {status.text && (
            <span
              className={
                status.kind === 'ok'
                  ? 'text-green-400 text-sm'
                  : 'text-red-400 text-sm'
              }
            >
              {status.text}
            </span>
          )}
        </div>

        <div className="card">
          <h3 className="text-lg font-semibold mb-4">关于</h3>
          <div className="space-y-1 text-secondary text-sm">
            <p>MediaPilot v3 — 新媒体一站式提效工具</p>
            <p>偏好设置跨设备同步，登录后自动加载。</p>
          </div>
        </div>
      </div>
    </div>
  )
}

function Field({ label, children }) {
  return (
    <div>
      <label className="block text-sm font-medium mb-2">{label}</label>
      {children}
    </div>
  )
}

function Select({ value, options, onChange, disabled }) {
  return (
    <select
      value={value}
      disabled={disabled}
      onChange={(e) => onChange(e.target.value)}
      className="w-full px-3 py-2 bg-bg-light border border-border rounded-lg focus:outline-none focus:border-primary disabled:opacity-50"
    >
      {options.map((o) => (
        <option key={o.value} value={o.value}>
          {o.label}
        </option>
      ))}
    </select>
  )
}

function Toggle({ label, checked, onChange, disabled }) {
  return (
    <label className="flex items-center justify-between cursor-pointer">
      <span className="text-sm">{label}</span>
      <input
        type="checkbox"
        checked={checked}
        disabled={disabled}
        onChange={(e) => onChange(e.target.checked)}
        className="w-5 h-5 accent-primary"
      />
    </label>
  )
}

export default SettingsPage
