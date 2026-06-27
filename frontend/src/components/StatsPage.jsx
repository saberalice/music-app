import { useEffect, useState } from 'react'
import {
  Bar,
  BarChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { getGenres, getTopArtists, sync } from '../api'

export default function StatsPage() {
  const [artists, setArtists] = useState([])
  const [genres, setGenres] = useState([])
  const [loading, setLoading] = useState(true)
  const [syncing, setSyncing] = useState(false)
  const [error, setError] = useState(null)

  async function load() {
    setLoading(true)
    setError(null)
    try {
      // 兩個請求一起發,快一點
      const [a, g] = await Promise.all([getTopArtists(), getGenres()])
      setArtists(a || [])
      setGenres(g || [])
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
  }, [])

  async function handleSync() {
    setSyncing(true)
    setError(null)
    try {
      await sync() // 從 Spotify 抓最新資料進 DB
      await load() // 再重新載入統計
    } catch (e) {
      setError(e.message)
    } finally {
      setSyncing(false)
    }
  }

  return (
    <div>
      <div className="toolbar">
        <button className="btn" onClick={handleSync} disabled={syncing}>
          {syncing ? '同步中…' : '從 Spotify 同步'}
        </button>
      </div>

      {error && <p className="error">⚠️ {error}</p>}
      {loading ? (
        <p className="muted">載入中…</p>
      ) : (
        <>
          <section>
            <h2>最常聽歌手 Top 10</h2>
            {artists.length === 0 ? (
              <Empty />
            ) : (
              <ol className="artist-list">
                {artists.map((a) => (
                  <li key={a.rank}>
                    <strong>{a.name}</strong>
                    {a.genres.length > 0 && (
                      <span className="genres">{a.genres.join(' · ')}</span>
                    )}
                  </li>
                ))}
              </ol>
            )}
          </section>

          <section>
            <h2>曲風分佈</h2>
            {genres.length === 0 ? (
              <Empty />
            ) : (
              <ResponsiveContainer
                width="100%"
                height={Math.max(220, genres.length * 32)}
              >
                <BarChart
                  data={genres}
                  layout="vertical"
                  margin={{ left: 30, right: 20 }}
                >
                  <XAxis type="number" allowDecimals={false} />
                  <YAxis type="category" dataKey="genre" width={130} />
                  <Tooltip />
                  <Bar dataKey="count" fill="#1db954" radius={[0, 4, 4, 0]} />
                </BarChart>
              </ResponsiveContainer>
            )}
          </section>
        </>
      )}
    </div>
  )
}

function Empty() {
  return <p className="muted">還沒有資料,先按上面的「從 Spotify 同步」。</p>
}
