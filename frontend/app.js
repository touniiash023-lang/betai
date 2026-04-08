const API_BASE_URL = "https://betai-backend-dovc.onrender.com";

let allMatches = [];
let currentSport = "football";
let editingId = null;

const pageTitle = document.getElementById("pageTitle");
const pageSubtitle = document.getElementById("pageSubtitle");
const matchesList = document.getElementById("matchesList");
const searchInput = document.getElementById("searchInput");
const sortSelect = document.getElementById("sortSelect");
const matchForm = document.getElementById("matchForm");
const cancelEditBtn = document.getElementById("cancelEditBtn");
const formTitle = document.getElementById("formTitle");
const loadDemoBtn = document.getElementById("loadDemoBtn");
const exportBtn = document.getElementById("exportBtn");
const importFile = document.getElementById("importFile");

const totalMatchesEl = document.getElementById("totalMatches");
const avgScoreEl = document.getElementById("avgScore");
const avgConfidenceEl = document.getElementById("avgConfidence");
const strongPredictionEl = document.getElementById("strongPrediction");

const sportNames = {
  football: "Football",
  basketball: "Basket",
  tennis: "Tennis",
  table_tennis: "Tennis de table"
};

document.querySelectorAll(".nav-btn").forEach(btn => {
  btn.addEventListener("click", () => {
    document.querySelectorAll(".nav-btn").forEach(b => b.classList.remove("active"));
    btn.classList.add("active");
    currentSport = btn.dataset.sport;
    updatePageHeader();
    resetForm();
    render();
  });
});

searchInput.addEventListener("input", render);
sortSelect.addEventListener("change", render);
cancelEditBtn.addEventListener("click", resetForm);

loadDemoBtn.addEventListener("click", async () => {
  await fetch(`${API_BASE_URL}/seed-demo`, { method: "POST" });
  await fetchMatches();
});

exportBtn.addEventListener("click", async () => {
  const res = await fetch(`${API_BASE_URL}/matches/export`);
  const data = await res.json();

  const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);

  const a = document.createElement("a");
  a.href = url;
  a.download = "matches_export.json";
  a.click();
  URL.revokeObjectURL(url);
});

importFile.addEventListener("change", async (event) => {
  const file = event.target.files[0];
  if (!file) return;

  try {
    const text = await file.text();
    const parsed = JSON.parse(text);

    const res = await fetch(`${API_BASE_URL}/matches/import`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(parsed)
    });

    if (!res.ok) throw new Error("Import impossible");
    await fetchMatches();
    alert("Import JSON réussi");
  } catch (error) {
    alert("Fichier JSON invalide");
  }

  event.target.value = "";
});

matchForm.addEventListener("submit", async (e) => {
  e.preventDefault();

  const payload = {
    sport: document.getElementById("sport").value,
    home_team: document.getElementById("homeTeam").value.trim(),
    away_team: document.getElementById("awayTeam").value.trim(),
    home_score: Number(document.getElementById("homeScore").value || 0),
    away_score: Number(document.getElementById("awayScore").value || 0),
    match_date: document.getElementById("matchDate").value || "",
    home_half_score: Number(document.getElementById("homeHalfScore").value || 0),
    away_half_score: Number(document.getElementById("awayHalfScore").value || 0),
    home_possession: Number(document.getElementById("homePossession").value || 50),
    away_possession: Number(document.getElementById("awayPossession").value || 50),
    home_shots: Number(document.getElementById("homeShots").value || 0),
    away_shots: Number(document.getElementById("awayShots").value || 0),
    home_corners: Number(document.getElementById("homeCorners").value || 0),
    away_corners: Number(document.getElementById("awayCorners").value || 0),
    home_form: Number(document.getElementById("homeForm").value || 50),
    away_form: Number(document.getElementById("awayForm").value || 50),
    home_history: Number(document.getElementById("homeHistory").value || 50),
    away_history: Number(document.getElementById("awayHistory").value || 50),
    image_url: document.getElementById("imageUrl").value.trim(),
    note: document.getElementById("note").value.trim()
  };

  const url = editingId ? `${API_BASE_URL}/matches/${editingId}` : `${API_BASE_URL}/matches`;
  const method = editingId ? "PUT" : "POST";

  const res = await fetch(url, {
    method,
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });

  if (!res.ok) {
    alert("Erreur lors de l'enregistrement");
    return;
  }

  await fetchMatches();
  resetForm();
});

function updatePageHeader() {
  pageTitle.textContent = sportNames[currentSport];
  pageSubtitle.textContent = "Pronostics statistiques avancés avec pourcentages";
}

function resetForm() {
  editingId = null;
  formTitle.textContent = "Ajouter un match";
  matchForm.reset();

  document.getElementById("sport").value = currentSport;
  document.getElementById("homeScore").value = 0;
  document.getElementById("awayScore").value = 0;
  document.getElementById("homeHalfScore").value = 0;
  document.getElementById("awayHalfScore").value = 0;
  document.getElementById("homePossession").value = 50;
  document.getElementById("awayPossession").value = 50;
  document.getElementById("homeShots").value = 0;
  document.getElementById("awayShots").value = 0;
  document.getElementById("homeCorners").value = 0;
  document.getElementById("awayCorners").value = 0;
  document.getElementById("homeForm").value = 50;
  document.getElementById("awayForm").value = 50;
  document.getElementById("homeHistory").value = 50;
  document.getElementById("awayHistory").value = 50;
}

async function fetchMatches() {
  const res = await fetch(`${API_BASE_URL}/matches`);
  allMatches = await res.json();
  render();
}

function getFilteredMatches() {
  const q = searchInput.value.trim().toLowerCase();

  let filtered = allMatches.filter(match => {
    const text = `${match.home_team} ${match.away_team} ${match.note || ""}`.toLowerCase();
    return match.sport === currentSport && (!q || text.includes(q));
  });

  const sortValue = sortSelect.value;

  if (sortValue === "confidence") {
    filtered.sort((a, b) => (b.analysis?.confidence || 0) - (a.analysis?.confidence || 0));
  } else if (sortValue === "homeWin") {
    filtered.sort((a, b) => (b.analysis?.home_win_pct || 0) - (a.analysis?.home_win_pct || 0));
  } else if (sortValue === "awayWin") {
    filtered.sort((a, b) => (b.analysis?.away_win_pct || 0) - (a.analysis?.away_win_pct || 0));
  } else {
    filtered.sort((a, b) => {
      const da = new Date(a.created_at || 0).getTime();
      const db = new Date(b.created_at || 0).getTime();
      return db - da;
    });
  }

  return filtered;
}

function renderStats(matches) {
  totalMatchesEl.textContent = matches.length;

  if (!matches.length) {
    avgScoreEl.textContent = "0";
    avgConfidenceEl.textContent = "0%";
    strongPredictionEl.textContent = "0";
    return;
  }

  const avgScore = matches.reduce((sum, m) => sum + m.home_score + m.away_score, 0) / matches.length;
  const avgConfidence = matches.reduce((sum, m) => sum + (m.analysis?.confidence || 0), 0) / matches.length;
  const strongPrediction = matches.filter(m => (m.analysis?.confidence || 0) >= 75).length;

  avgScoreEl.textContent = avgScore.toFixed(1);
  avgConfidenceEl.textContent = `${Math.round(avgConfidence)}%`;
  strongPredictionEl.textContent = strongPrediction;
}

function getWinnerTag(match) {
  const winner = match.analysis?.winner || "-";
  if (winner === "Nul") return "Pronostic équilibré";
  return `Favori : ${winner}`;
}

function render() {
  const matches = getFilteredMatches();
  renderStats(matches);

  if (!matches.length) {
    matchesList.innerHTML = `<div class="empty-state">Aucun match disponible pour ce sport.</div>`;
    return;
  }

  matchesList.innerHTML = matches.map(match => {
    const a = match.analysis || {};
    const img = match.image_url
      ? `<img class="match-image" src="${escapeAttr(match.image_url)}" alt="match" />`
      : `<div class="match-image"></div>`;

    const progressWidth = Math.max(5, Math.min(100, a.confidence || 0));

    return `
      <div class="match-card">
        <div class="match-top">
          <div>
            <div class="match-sport">${escapeHtml(sportNames[match.sport] || match.sport)}</div>
            <div class="match-title">${escapeHtml(match.home_team)} vs ${escapeHtml(match.away_team)}</div>
            <div class="score-box">
              <span>Score</span>
              <strong>${match.home_score}</strong>
              <span>-</span>
              <strong>${match.away_score}</strong>
            </div>
            <div class="match-date">${escapeHtml(match.match_date || "Date non précisée")}</div>
          </div>
          ${img}
        </div>

        <div class="percent-grid">
          <div class="percent-card">
            <span>Victoire domicile</span>
            <strong>${a.home_win_pct || 0}%</strong>
          </div>
          <div class="percent-card">
            <span>Nul</span>
            <strong>${a.draw_pct || 0}%</strong>
          </div>
          <div class="percent-card">
            <span>Victoire extérieur</span>
            <strong>${a.away_win_pct || 0}%</strong>
          </div>
        </div>

        <div class="analysis-block">
          <div class="info-grid">
            <div>Mi-temps / set 1 : ${match.home_half_score} - ${match.away_half_score}</div>
            <div>Gagnant mi-temps : ${escapeHtml(a.half_winner || "-")}</div>
            <div>Gagnant final : ${escapeHtml(a.winner || "-")}</div>
            <div>Score probable : ${escapeHtml(a.likely_score || "-")}</div>
            <div>BTTS : ${a.btts ? "Oui" : "Non"}</div>
            <div>Over 2.5 / total élevé : ${a.over_2_5 ? "Oui" : "Non"}</div>
            <div>Tirs / bonus : ${match.home_shots} - ${match.away_shots}</div>
            <div>Corners / stats bonus : ${match.home_corners} - ${match.away_corners}</div>
          </div>

          <div class="tag-row">
            <div class="tag">${escapeHtml(getWinnerTag(match))}</div>
            <div class="tag">Confiance : ${a.confidence || 0}%</div>
            <div class="tag">Indice offensif : ${a.attack_index || 0}</div>
          </div>

          <div class="progress">
            <div class="progress-bar" style="width:${progressWidth}%"></div>
          </div>

          <div class="tag-row">
            <div class="tag">${escapeHtml(a.summary || "-")}</div>
          </div>

          <div class="tag-row">
            <div class="tag">${escapeHtml(match.note || "Aucune note")}</div>
          </div>
        </div>

        <div class="match-actions">
          <button class="edit-btn" onclick="editMatch('${match.id}')">Modifier</button>
          <button class="delete-btn" onclick="deleteMatch('${match.id}')">Supprimer</button>
        </div>
      </div>
    `;
  }).join("");
}

function editMatch(id) {
  const match = allMatches.find(m => m.id === id);
  if (!match) return;

  editingId = id;
  formTitle.textContent = "Modifier un match";

  document.getElementById("sport").value = match.sport;
  document.getElementById("homeTeam").value = match.home_team;
  document.getElementById("awayTeam").value = match.away_team;
  document.getElementById("homeScore").value = match.home_score;
  document.getElementById("awayScore").value = match.away_score;
  document.getElementById("matchDate").value = match.match_date || "";
  document.getElementById("homeHalfScore").value = match.home_half_score;
  document.getElementById("awayHalfScore").value = match.away_half_score;
  document.getElementById("homePossession").value = match.home_possession;
  document.getElementById("awayPossession").value = match.away_possession;
  document.getElementById("homeShots").value = match.home_shots;
  document.getElementById("awayShots").value = match.away_shots;
  document.getElementById("homeCorners").value = match.home_corners;
  document.getElementById("awayCorners").value = match.away_corners;
  document.getElementById("homeForm").value = match.home_form;
  document.getElementById("awayForm").value = match.away_form;
  document.getElementById("homeHistory").value = match.home_history;
  document.getElementById("awayHistory").value = match.away_history;
  document.getElementById("imageUrl").value = match.image_url || "";
  document.getElementById("note").value = match.note || "";

  window.scrollTo({ top: 0, behavior: "smooth" });
}

async function deleteMatch(id) {
  const ok = confirm("Supprimer ce match ?");
  if (!ok) return;

  await fetch(`${API_BASE_URL}/matches/${id}`, { method: "DELETE" });
  await fetchMatches();
  if (editingId === id) resetForm();
}

function escapeHtml(text) {
  return String(text)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function escapeAttr(text) {
  return escapeHtml(text);
}

window.editMatch = editMatch;
window.deleteMatch = deleteMatch;

updatePageHeader();
resetForm();
fetchMatches();