function ResultChip({ result }) {
  return <span className={`result-chip ${result?.toLowerCase()}`}>{result}</span>
}

export default function RecentForm({ title, data }) {
  return (
    <section className="card">
      <h3>{title}</h3>
      <div className="mini-grid">
        <div><span className="small muted">Bilan</span><strong>{data.wins}V / {data.draws}N / {data.losses}D</strong></div>
        <div><span className="small muted">Buts marqués</span><strong>{data.goals_for_avg}</strong></div>
        <div><span className="small muted">Buts encaissés</span><strong>{data.goals_against_avg}</strong></div>
        <div><span className="small muted">Clean sheets</span><strong>{data.clean_sheets}</strong></div>
      </div>

      <div className="recent-list">
        {data.recent_results?.map((item) => (
          <div key={item.id} className="recent-row">
            <div>
              <strong>{item.opponent}</strong>
              <div className="small muted">{item.venue} • {new Date(item.utcDate).toLocaleDateString()}</div>
            </div>
            <div className="recent-right">
              <span>{item.score}</span>
              <ResultChip result={item.result} />
            </div>
          </div>
        ))}
      </div>
    </section>
  )
}
