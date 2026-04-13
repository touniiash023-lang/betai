import { useEffect, useMemo, useState } from 'react'
import { fetchUpcomingMatches } from '../services/api'
import MatchCard from '../components/MatchCard'
import { COMPETITIONS, DEFAULT_CODES } from '../data/competitions'

function StatCard({ label, value, help }) {
  return (
    <div className="card compact-card">
      <div className="small muted">{label}</div>
      <div className="stat-number">{value}</div>
      <div className="small muted">{help}</div>
    </div>
  )
}

function LeaguePill({ item, active, onClick }) {
  return (
    <button type="button" className={`league-pill ${active ? 'active' : ''}`} onClick={() => onClick(item.code)}>
      <span>{item.icon}</span>
      <span>{item.name}</span>
    </button>
  )
}

export default function Dashboard() {
  const [matches, setMatches] = useState([])
  const [days, setDays] = useState(3)
  const [selectedCodes, setSelectedCodes] = useState(DEFAULT_CODES)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const competitions = selectedCodes.join(',')

  const loadMatches = async () => {
    try {
      setLoading(true)
      setError('')
      const result = await fetchUpcomingMatches({ days, competitions })
      setMatches(result)
    } catch (err) {
      setError(err?.response?.data?.error || err.message)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadMatches()
  }, [])

  const toggleCompetition = (code) => {
    setSelectedCodes((current) => {
      const exists = current.includes(code)
      if (exists) {
        if (current.length === 1) return current
        return current.filter((item) => item !== code)
      }
      return [...current, code]
    })
  }

  const grouped = useMemo(() => {
    const map = new Map()
    matches.forEach((match) => {
      const key = match.competition?.name || 'Autres compétitions'
      if (!map.has(key)) map.set(key, [])
      map.get(key).push(match)
    })
    return Array.from(map.entries()).sort((a, b) => a[0].localeCompare(b[0]))
  }, [matches])

  const summary = useMemo(() => {
    const teams = new Set()
    const leagues = new Set()
    matches.forEach((match) => {
      teams.add(match.homeTeam?.name)
      teams.add(match.awayTeam?.name)
      leagues.add(match.competition?.name)
    })

    const nextKickoff = matches
      .map((match) => new Date(match.utcDate).getTime())
      .filter((value) => Number.isFinite(value))
      .sort((a, b) => a - b)[0]

    return {
      matchCount: matches.length,
      leagueCount: leagues.size,
      teamCount: teams.size,
      nextKickoff: nextKickoff ? new Date(nextKickoff).toLocaleString() : '-',
    }
  }, [matches])

  return (
    <section className="page-stack">
      <div className="hero hero-v3 card gradient-hero">
        <div className="hero-grid">
          <div>
            <span className="badge soft">Interface premium</span>
            <h2>Dashboard premium des grandes compétitions</h2>
            <p>
              Interface plus propre, sélecteur rapide de ligues, résumé visuel et fiches détaillées pour
              Premier League, La Liga, Bundesliga, Serie A, Ligue 1 et Champions League.
            </p>
          </div>
          <div className="hero-side-note">
            <div className="small muted">Mode</div>
            <strong>Analyse informative</strong>
            <p className="small muted">Les chiffres restent indicatifs. Aucun résultat réel n’est garanti.</p>
          </div>
        </div>

        <div className="grid four">
          <StatCard label="Matchs détectés" value={summary.matchCount} help="Sur la fenêtre sélectionnée" />
          <StatCard label="Compétitions" value={summary.leagueCount} help="Grandes ligues actives" />
          <StatCard label="Équipes" value={summary.teamCount} help="Clubs présents dans la liste" />
          <StatCard label="Prochain coup d’envoi" value={summary.nextKickoff} help="Date du premier match à venir" />
        </div>
      </div>

      <section className="card filters-card">
        <div className="section-head">
          <h3>Compétitions suivies</h3>
          <span className="small muted">{selectedCodes.length} ligue(s) activée(s)</span>
        </div>
        <div className="league-pills">
          {COMPETITIONS.map((item) => (
            <LeaguePill key={item.code} item={item} active={selectedCodes.includes(item.code)} onClick={toggleCompetition} />
          ))}
        </div>

        <div className="filters-grid top-space">
          <label>
            <span className="small muted">Fenêtre</span>
            <select value={days} onChange={(e) => setDays(Number(e.target.value))}>
              <option value={1}>1 jour</option>
              <option value={3}>3 jours</option>
              <option value={5}>5 jours</option>
              <option value={7}>7 jours</option>
            </select>
          </label>

          <label className="grow">
            <span className="small muted">Codes actifs</span>
            <input value={competitions} readOnly />
          </label>

          <button className="button" onClick={loadMatches}>Actualiser</button>
        </div>
      </section>

      {loading && <div className="card">Chargement des matchs…</div>}
      {error && <div className="card error">Erreur: {error}</div>}

      {!loading && !error && matches.length === 0 && (
        <div className="card">Aucun match trouvé pour cette plage de dates ou ces compétitions.</div>
      )}

      {!loading && !error && grouped.map(([competition, items]) => (
        <section key={competition} className="page-stack">
          <div className="section-head">
            <h3>{competition}</h3>
            <span className="small muted">{items.length} match(s)</span>
          </div>
          <div className="grid three">
            {items.map((match) => <MatchCard key={match.id} match={match} />)}
          </div>
        </section>
      ))}
    </section>
  )
}
