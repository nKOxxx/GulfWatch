// API Configuration
const isDev = import.meta.env.DEV

export const API_BASE_URL = isDev 
  ? 'http://localhost:8000'
  : 'https://gulf-watch-api.onrender.com'

export const WS_BASE_URL = isDev
  ? 'ws://localhost:8000'
  : 'wss://gulf-watch-api.onrender.com'
