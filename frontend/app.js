const API_BASE_URL = "https://betai-backend-dovc.onrender.com";

let allMatches = [];
let currentSport = "football";
let editingId = null;

const pageTitle = document.getElementById("pageTitle");
const pageSubtitle = document.getElementById("pageSubtitle");
const matchesList = document.getElementById("matchesList");
const topPredictions = document.getElementById("topPredictions");
const searchInput = document.getElementById("searchInput");
const sortSelect = document.getElementById("sortSelect");
const statusFilter = document.getElementById("statusFilter");
const matchForm = document.getElementById("matchForm");
const cancelEditBtn = document.getElementById("cancelEditBtn");
const formTitle = document.getElementById("formTitle");
const loadDemoBtn = document.getElementById("loadDemoBtn");
const exportBtn = document.getElementById("exportBtn");
const importFile = document.getElementById("importFile");
const autofillBtn = document.getElementById("autofillBtn");

const totalMatchesEl = document.getElementById("totalMatches");
const avgConfidenceEl = document.getElementById("avgConfidence");
const safeCountEl = document.getElementById("safeCount");
const upcomingCountEl = document.getElementById("upcomingCount");

const sportNames = {
  football: "Football",
  basketball: "Basket",
  tennis: "Tennis",
  table_tennis: "Tennis de table"
};

document.querySelectorAll(".nav-btn").forEach((btn) => {
  btn.addEventListener("click", () => {
    document.querySelectorAll(".nav-btn").forEach((b) => b.classList.remove("active"));
    btn.classList.add("active");
    currentSport = btn.dataset.sport;
    updatePageHeader();
    document.getElementById("sport").value = currentSport;
    render();
  });
});

searchInput.addEventListener("input", render);
sortSelect.addEventListener("change", render);
statusFilter.addEventListener("change", render);
cancelEditBtn.addEventListener("click", resetForm);

loadDemoBtn.addEventListener("click", async () => {
  try {
    await fetch(`${API_BASE_URL}/seed-demo`, { method: "POST" });
    await refreshAll();
  } catch (error) {
    alert("Impossible de charger la démo.");
  }
});

exportBtn.addEventListener("click", async () => {
  try {
    const res = await fetch(`${API_BASE_URL}/matches/export`);
    const data = await res.json();

    const blob = new Blob([JSON.stringify(data, null, 2)], {
      type: "application/json"
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "matches_export.json";
    a.click();
    URL.revokeObjectURL(url);
  } catch (error) {
    alert("Impossible d'exporter le JSON.");
  }
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

    if (!res.ok) {
      throw new Error("Import failed");
    }

    await refreshAll();
    alert("Import JSON réussi");
  } catch (error) {
    alert("Fichier JSON invalide");
  }

  event.target.value = "";
});

autofillBtn.addEventListener("click", async () => {
  const payload = {
    sport: document.getElementById("sport").value,
    status: document.getElementById("status").value,
    home_team: document.getElementById("homeTeam").value.trim(),
    away_team: document.getElementById("awayTeam").value.trim(),
    match_date: document.getElementById("matchDate").value || ""
  };

  if (!payload.home_team || !payload.away_team) {
    alert("Entrez d'abord les deux équipes / joueurs.");
    return;
  }

  try {
    const res = await fetch(`${API_BASE_URL}/autofill-match`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });

    const data = await res.json();

    if (!res.ok) {
      alert(data.error || "Erreur backend sur auto remplissage.");
      return;
    }

    document.getElementById("competition").value = data.competition || "";
    document.getElementById("matchDate").value = data.match_date || "";
    document.getElementById("homePossession").value = data.home_possession ?? 50;
    document.getElementById("awayPossession").value = data.away_possession ?? 50;
    document.getElementById("homeShots").value = data.home_shots ?? 0;
    document.getElementById("awayShots").value = data.away_shots ?? 0;
    document.getElementById("homeCorners").value = data.home_corners ?? 0;
    document.getElementById("awayCorners").value = data.away_corners ?? 0;
    document.getElementById("homeForm").value = data.home_form ?? 50;
    document.getElementById("awayForm").value = data.away_form ?? 50;
    document.getElementById("homeHistory").value = data.home_history ?? 50;
    document.getElementById("awayHistory").value = data.away_history ?? 50;
    document.getElementById("note").value = data.note || "";

    if (payload.status === "upcoming") {
      document.getElementById("homeScore").value = 0;
      document.getElementById("awayScore").value = 0;
      document.getElementById("homeHalfScore").value = 0;
      document.getElementById("awayHalfScore").value = 0;
    }

    alert("Champs remplis automatiquement.");
  } catch (error) {
    alert("Impossible de récupérer les statistiques automatiques : " + error.message);
  }
});

matchForm.addEventListener("submit", async (e) => {
  e.preventDefault();

  const payload = {
    sport: document.getElementById("sport").value,
    status: document.getElementById("status").value,
    competition: document.getElementById("competition").value.trim(),
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

  const url = editingId
    ? `${API_BASE_URL}/matches/${editingId}`
    : `${API_BASE_URL}/matches`;

  const method = editingId ? "PUT" : "POST";

  try {
    const res = await fetch(url, {
      method,
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });

    if (!res.ok) {
      throw new Error("Save failed");
    }

    await refreshAll();
    resetForm();
  } catch (error) {
    alert("Erreur lors de l'enregistrement");
  }
});

function updatePageHeader() {
  pageTitle.textContent = sportNames[currentSport];
  pageSubtitle.textContent = "Analyse sportive avancée et auto remplissage API";
}

function resetForm() {
  editingId = null;
  formTitle.textContent = "Ajouter un match";
  matchForm.reset();

  document.getElementById("sport").value = currentSport;
  document.getElementById("status").value = "upcoming";
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
}

async function fetchDashboard() {
  const res = await fetch(`${API_BASE_URL}/dashboard`);
  const data = await res.json();

  totalMatchesEl.textContent = data.total_matches || 0;
  avgConfidenceEl.textContent = `${data.avg_confidence || 0}%`;
  safeCountEl.textContent = data.safe_count || 0;
  upcomingCountEl.textContent = data.upcoming_count || 0;

  topPredictions.innerHTML =
    (data.top_predictions || []).map((match) => `
      <div class="top-mini-card">
        <h4>${escapeHtml(match.home_team)} vs ${escapeHtml(match.away_team)}</h4>
        <p>${escapeHtml(match.match_date || "Date non précisée")}</p>
        <p>Confiance: ${(match.analysis || {}).confidence || 0}%</p>
        <p>Favori: ${escapeHtml((match.analysis || {}).winner || "-")}</p>
      </div>
    `).join("") || `<div class="empty-state">Aucune analyse disponible.</div>`;
}

async function refreshAll() {
  await fetchMatches();
  await fetchDashboard();
  render();
}

function getFilteredMatches() {
  const q = searchInput.value.trim().toLowerCase();
  const sf = statusFilter.value;

  let filtered = allMatches.filter((match) => {
    const text = `${match.home_team} ${match.away_team} ${match.competition || ""} ${match.note || ""}`.toLowerCase();
    const sameSport = match.sport === currentSport;
    const statusOk = sf === "all" || match.status === sf;
    return sameSport && statusOk && (!q || text.includes(q));
  });

  const sortValue = sortSelect.value;

  if (sortValue === "confidence") {
    filtered.sort((a, b) => (b.analysis?.confidence || 0) - (a.analysis?.confidence || 0));
  } else if (sortValue === "homeWin") {
    filtered.sort((a, b) => (b.analysis?.home_win_pct || 0) - (a.analysis?.home_win_pct || 0));
  } else if (sortValue === "awayWin") {
    filtered.sort((a, b) => (b.analysis?.away_win_pct || 0) - (a.analysis?.away_win_pct || 0));
  } else {
    filtered.sort((a, b) => new Date(b.created_at || 0) - new Date(a.created_at || 0));
  }

  return filtered;
}

function riskClass(risk) {
  if (risk === "SAFE") return "chip safe";
  if (risk === "MEDIUM") return "chip medium";
  return "chip risky";
}

function render() {
  const matches = getFilteredMatches();

  if (!matches.length) {
    matchesList.innerHTML = `<div class="empty-state">Aucun match disponible pour ce filtre.</div>`;
    return;
  }

  matchesList.innerHTML = matches.map((match) => {
    const a = match.analysis || {};

    const img = match.image_url
      ? `<img class="match-image" src="${escapeAttr(match.image_url)}" alt="match" />`
      : `<div class="match-image"></div>`;

    const competitionChip = match.competition
      ? `<span class="chip">${escapeHtml(match.competition)}</span>`
      : "";

    const drawCard = match.sport === "football"
      ? `<div class="percent-card"><span>Nul</span><strong>${a.draw_pct || 0}%</strong></div>`
      : "";

    const footballMarkets = match.sport === "football"
      ? `
        <div>BTTS : ${a.btts ? "Oui" : "Non"}</div>
        <div>Over 2.5 : ${a.over_2_5 ? "Oui" : "Non"}</div>
      `
      : "";

    return `
      <div class="match-card">
        <div class="match-top">
          <div>
            <div class="chips">
              <span class="chip">${escapeHtml(sportNames[match.sport] || match.sport)}</span>
              <span class="chip">${escapeHtml(match.status === "finished" ? "Terminé" : "À venir")}</span>
              <span class="${riskClass(a.risk_badge)}">${escapeHtml(a.risk_badge || "RISKY")}</span>
              ${competitionChip}
            </div>

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
          <div class="percent-card"><span>Victoire domicile</span><strong>${a.home_win_pct || 0}%</strong></div>
          ${drawCard}
          <div class="percent-card"><span>Victoire extérieur</span><strong>${a.away_win_pct || 0}%</strong></div>
        </div>

        <div class="analysis-block">
          <div class="info-grid">
            <div>Gagnant final : ${escapeHtml(a.winner || "-")}</div>
            <div>Gagnant mi-temps / set 1 : ${escapeHtml(a.half_winner || "-")}</div>
            <div>Score probable : ${escapeHtml(a.likely_score || "-")}</div>
            <div>Confiance : ${a.confidence || 0}%</div>
            ${footballMarkets}
            <div>Forme : ${match.home_form} - ${match.away_form}</div>
            <div>Historique : ${match.home_history} - ${match.away_history}</div>
            <div>Possession : ${match.home_possession}% - ${match.away_possession}%</div>
            <div>Tirs / stats : ${match.home_shots} - ${match.away_shots}</div>
          </div>

          <div class="tag-row">
            <div class="tag">Indice offensif : ${a.attack_index || 0}</div>
            <div class="tag">Mode : ${match.status === "finished" ? "Post-match" : "Pré-match"}</div>
          </div>

          <div class="progress">
            <div class="progress-bar" style="width:${Math.max(5, Math.min(100, a.confidence || 0))}%"></div>
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
  const match = allMatches.find((m) => m.id === id);
  if (!match) return;

  editingId = id;
  formTitle.textContent = "Modifier un match";

  document.getElementById("sport").value = match.sport;
  document.getElementById("status").value = match.status;
  document.getElementById("competition").value = match.competition || "";
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

  try {
    await fetch(`${API_BASE_URL}/matches/${id}`, { method: "DELETE" });
    await refreshAll();

    if (editingId === id) {
      resetForm();
    }
  } catch (error) {
    alert("Erreur lors de la suppression.");
  }
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
refreshAll();