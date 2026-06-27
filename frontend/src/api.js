// 集中所有對後端的呼叫,元件只認得這裡的函式,不直接寫 fetch 細節。
const API_BASE = 'http://127.0.0.1:8000'

async function getJson(path) {
  const res = await fetch(`${API_BASE}${path}`)
  if (res.status === 401) return null // 尚未登入
  if (!res.ok) throw new Error(`${path} 失敗 (${res.status})`)
  return res.json()
}

async function postJson(path) {
  const res = await fetch(`${API_BASE}${path}`, { method: 'POST' })
  if (!res.ok) throw new Error(`${path} 失敗 (${res.status})`)
  return res.json()
}

// 登入:直接讓瀏覽器導去後端 /login(它會再導去 Spotify)
export function loginUrl() {
  return `${API_BASE}/login`
}

export const logout = () => postJson('/logout')
export const getMe = () => getJson('/me')
export const getTopArtists = () => getJson('/stats/top-artists')
export const getGenres = () => getJson('/stats/genres')
export const sync = () => postJson('/sync')
