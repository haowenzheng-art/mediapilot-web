import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'
import { AppProvider } from './contexts/AppContext.jsx'
import { ThemeProvider } from './contexts/ThemeContext.jsx'

const checkCSSSupport = () => {
  if (!window.CSS || !CSS.supports) {
    document.documentElement.classList.add('no-css-vars')
    console.warn('CSS variables not supported, using fallback theme')
    return false
  }
  return CSS.supports('color', 'var(--fake-var)')
}

checkCSSSupport()

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <ThemeProvider>
      <AppProvider>
        <App />
      </AppProvider>
    </ThemeProvider>
  </StrictMode>,
)
