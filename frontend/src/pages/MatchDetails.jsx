import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { fetchAnalysis } from '../services/api'
import PredictionPanel from '../components/PredictionPanel'

export default function MatchDetails() {
  const { matchId } = useParams()
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    const load = async () => {
      try {
        setLoading(true)
        const result = await fetchAnalysis(matchId)
        setData(result)
      } catch (err) {
        setError(err?.response?.data?.error || err.message)
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [matchId])

  return (
    <section className="page-stack">
      <Link className="button secondary" to="/">← Retour dashboard</Link>
      {loading && <div className="card">Analyse du match en cours…</div>}
      {error && <div className="card error">Erreur: {error}</div>}

      {data && (
        <>
          <div className="card match-header-card premium-header">
            <div>
              <span className="badge ghost">{data.competition_code || 'MATCH'}</span>
              <h2>{data.home_team} vs {data.away_team}</h2>
              <p>{data.competition}</p>
              <p className="small muted">{new Date(data.utc_date).toLocaleString()} {data.venue ? `• ${data.venue}` : ''}</p>
            </div>
            <div className="hero-note">
              <strong>Fiche premium</strong>
              <p className="small muted">{data.disclaimer}</p>
            </div>
          </div>

          <PredictionPanel analysis={data} />
        </>
      )}
    </section>
  )
}
