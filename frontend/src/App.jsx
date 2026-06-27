import { useEffect, useState } from 'react'
import { getMe, logout, loginUrl } from './api'
import StatsPage from './components/StatsPage'

export default function App() {
  // me: undefined = 載入中, null = 未登入, object = 已登入
  const [me, setMe] = useState(undefined)
  const [error, setError] = useState(null)

  useEffect(() => {
    getMe()
      .then(setMe)
      .catch((e) => setError(e.message))
  }, [])

  async function handleLogout() {
    try {
      await logout()
      setMe(null) // 回到登入頁
    } catch (e) {
      setError(e.message)
    }
  }

  return (
    <div className="container">
      <header>
        <h1>🎵 Music App</h1>
        {me && (
          <span className="user">
            {me.display_name || me.id}
            <button className="link-btn" onClick={handleLogout}>
              登出
            </button>
          </span>
        )}
      </header>

      {error && <p className="error">⚠️ {error}（後端有開嗎?)</p>}
      {me === undefined && !error && <p className="muted">載入中…</p>}
      {me === null && <Login />}
      {me && <StatsPage />}
    </div>
  )
}

function Login() {
  return (
    <div className="login">
      <p>用 Spotify 登入來看你的聽歌統計</p>
      <a className="btn" href={loginUrl()}>
        使用 Spotify 登入
      </a>
    </div>
  )
}
