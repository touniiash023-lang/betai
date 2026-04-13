import { Link } from 'react-router-dom'

function getTeamName(team) {
  return team?.shortName || team?.name || 'Team'
}

export default function MatchCard({ match }) {
  const home = getTeamName(match.homeTeam)
  const away = getTeamName(match.awayTeam)
  const date = new Date(match.utcDate)
  const competition = match.competition?.name || 'Competition'
  const venue = match.venue || 'Stade non renseigné'

  return (
    <article className="card match-card premium-match-card">
      <div className="match-card-top">
        <span className="badge ghost">{match.competition?.code || 'FB'}</span>
        <span className="small muted">{competition}</span>
      </div>

      <div className="match-teams">
        <div className="team-block">
          {match.homeTeam?.crest ? <img src={match.homeTeam.crest} alt={home} /> : <div className="crest-placeholder" />}
          <strong>{home}</strong>
          <span className="small muted">Domicile</span>
        </div>
        <div className="versus">VS</div>
        <div className="team-block">
          {match.awayTeam?.crest ? <img src={match.awayTeam.crest} alt={away} /> : <div className="crest-placeholder" />}
          <strong>{away}</strong>
          <span className="small muted">Extérieur</span>
        </div>
      </div>

      <div className="match-meta">
        <div>
          <span className="small muted">Date</span>
          <strong>{date.toLocaleString()}</strong>
        </div>
        <div>
          <span className="small muted">Journée</span>
          <strong>{match.matchday || '-'}</strong>
        </div>
        <div>
          <span className="small muted">Lieu</span>
          <strong>{venue}</strong>
        </div>
        <div>
          <span className="small muted">Statut</span>
          <strong>{match.status || 'SCHEDULED'}</strong>
        </div>
      </div>

      <Link className="button" to={`/match/${match.id}`}>Ouvrir la fiche premium</Link>
    </article>
  )
}
