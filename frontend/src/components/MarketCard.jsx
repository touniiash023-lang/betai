export default function MarketCard({ title, value, subtitle, accent = '' }) {
  return (
    <div className={`card market-card ${accent}`}>
      <div className="small muted">{title}</div>
      <div className="market-value">{value}</div>
      {subtitle ? <div className="small muted">{subtitle}</div> : null}
    </div>
  )
}
