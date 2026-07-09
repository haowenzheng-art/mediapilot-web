import React from 'react'
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import './styles/notion.css'
import App from './App.jsx'
import { AppProvider } from './contexts/AppContext.jsx'
import { HotTopicProvider } from './contexts/HotTopicContext.jsx'

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true };
  }

  componentDidCatch(error, errorInfo) {
    console.error("Application error:", error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div style={{
          padding: '2rem',
          textAlign: 'center',
          background: '#000000',
          color: '#ffffff'
        }}>
          <h1>应用出现错误</h1>
          <p>请刷新页面或联系管理员</p>
        </div>
      );
    }
    return this.props.children;
  }
}

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <ErrorBoundary>
      <AppProvider>
        <HotTopicProvider>
          <App />
        </HotTopicProvider>
      </AppProvider>
    </ErrorBoundary>
  </StrictMode>,
)
