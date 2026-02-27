import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import App from './App'
import './index.css'

// Dash0 Website SDK — injected via environment variable at build time
if (import.meta.env.VITE_DASH0_INGEST_ENDPOINT) {
  import('@dash0hq/opentelemetry').then(({ Dash0 }) => {
    Dash0.init({
      endpoint: import.meta.env.VITE_DASH0_INGEST_ENDPOINT,
      dataset: import.meta.env.VITE_DASH0_DATASET || 'default',
    })
  }).catch(() => {})
}

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <BrowserRouter>
      <App />
    </BrowserRouter>
  </React.StrictMode>
)
