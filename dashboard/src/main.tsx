import ReactDOM from 'react-dom/client'
import React from 'react'
import App from './App'
import './index.css'

// Remove StrictMode to prevent double renders in development
// If you need StrictMode for catching issues, you can add it back
ReactDOM.createRoot(document.getElementById('root')!).render(
  <App />
)

