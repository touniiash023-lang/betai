import { Routes, Route, Link } from 'react-router-dom'
import Dashboard from './pages/Dashboard'
import MatchDetails from './pages/MatchDetails'

export default function App() {
  return (
    <div className="app-shell">
      <header className="topbar">
        <div>
          <div className="eyebrow">V3 Premium Interface</div>
          <h1>Football Analytics Pro</h1>
          <p>Plateforme d’analyse football avec interface premium, grandes compétitions, tendances et fiches match détaillées.</p>
        </div>
        <nav className="nav-links">
          <Link to="/">Dashboard</Link>
        </nav>
      </header>

      <main className="container">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/match/:matchId" element={<MatchDetails />} />
        </Routes>
      </main>
    </div>
  )
}
