import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import App from './App'
import './styles.css'

const savedTheme = localStorage.getItem('wordmaster-site-theme')
document.documentElement.dataset.theme = savedTheme === 'dark' || savedTheme === 'light'
  ? savedTheme
  : window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode><BrowserRouter><App /></BrowserRouter></React.StrictMode>,
)
