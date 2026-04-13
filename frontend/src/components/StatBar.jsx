export default function StatBar({ label, left, middle, right }) {
  return (
    <div className="statbar">
      <div className="statbar-head">
        <span>{label}</span>
        <span>{left}% / {middle}% / {right}%</span>
      </div>
      <div className="statbar-track triple">
        <div style={{ width: `${left}%` }} />
        <div style={{ width: `${middle}%` }} />
        <div style={{ width: `${right}%` }} />
      </div>
    </div>
  )
}
