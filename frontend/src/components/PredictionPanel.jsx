import MarketCard from './MarketCard'
import StatBar from './StatBar'
import RecentForm from './RecentForm'

export default function PredictionPanel({ analysis }) {
  const a = analysis?.analysis
  if (!a) return null

  return (
    <div className="details-stack">
      <div className="grid four">
        <MarketCard title="Lecture principale" value={a.main_pick} subtitle={`Confiance ${a.confidence}%`} accent="accent-blue" />
        <MarketCard title="Score probable" value={a.likely_score} subtitle={`Alternatives ${a.alternative_scores?.join(', ')}`} accent="accent-purple" />
        <MarketCard title="BTTS" value={`${a.btts_pct}%`} subtitle={a.btts ? 'Oui favorisé' : 'Non favorisé'} accent="accent-green" />
        <MarketCard title="Over 2.5" value={`${a.over_2_5_pct}%`} subtitle={`Under 2.5 ${a.under_2_5_pct}%`} accent="accent-gold" />
      </div>

      <div className="grid two">
        <section className="card">
          <h3>Lecture 1X2</h3>
          <StatBar label="Domicile / Nul / Extérieur" left={a.home_win_pct} middle={a.draw_pct} right={a.away_win_pct} />
          <div className="mini-grid top-space">
            <div><span className="small muted">1X</span><strong>{a.double_chance_1x_pct}%</strong></div>
            <div><span className="small muted">X2</span><strong>{a.double_chance_x2_pct}%</strong></div>
            <div><span className="small muted">12</span><strong>{a.double_chance_12_pct}%</strong></div>
            <div><span className="small muted">Risque</span><strong>{a.risk_badge}</strong></div>
          </div>
        </section>

        <section className="card">
          <h3>Projection buts</h3>
          <div className="mini-grid">
            <div><span className="small muted">xG domicile</span><strong>{a.expected_home_goals}</strong></div>
            <div><span className="small muted">xG extérieur</span><strong>{a.expected_away_goals}</strong></div>
            <div><span className="small muted">xG total</span><strong>{a.total_expected_goals}</strong></div>
            <div><span className="small muted">Over 1.5</span><strong>{a.over_1_5_pct}%</strong></div>
            <div><span className="small muted">Over 3.5</span><strong>{a.over_3_5_pct}%</strong></div>
            <div><span className="small muted">1re MT +0.5</span><strong>{a.first_half_over_0_5_pct}%</strong></div>
          </div>
        </section>
      </div>

      <div className="grid two">
        <section className="card">
          <h3>Classement et structure</h3>
          <div className="mini-grid">
            <div><span className="small muted">Position domicile</span><strong>{a.home_position || '-'}</strong></div>
            <div><span className="small muted">Position extérieur</span><strong>{a.away_position || '-'}</strong></div>
            <div><span className="small muted">Points domicile</span><strong>{a.home_points || '-'}</strong></div>
            <div><span className="small muted">Points extérieur</span><strong>{a.away_points || '-'}</strong></div>
            <div><span className="small muted">Clean sheet domicile</span><strong>{a.home_clean_sheet_pct}%</strong></div>
            <div><span className="small muted">Clean sheet extérieur</span><strong>{a.away_clean_sheet_pct}%</strong></div>
          </div>
        </section>

        <section className="card">
          <h3>Résumé du moteur</h3>
          <p>{a.summary}</p>
          <div className="insights-list">
            {analysis.insights?.map((line, index) => <div key={index} className="insight-item">{line}</div>)}
          </div>
        </section>
      </div>

      <div className="grid two">
        <RecentForm title="Forme domicile" data={a.home_recent} />
        <RecentForm title="Forme extérieur" data={a.away_recent} />
      </div>
    </div>
  )
}
