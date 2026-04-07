const API_URL = "https://betai-backend-dovc.onrender.com";

const sportSelect = document.getElementById("sport");
const homeInput = document.getElementById("home");
const awayInput = document.getElementById("away");
const analyzeBtn = document.getElementById("analyzeBtn");
const loadDemoBtn = document.getElementById("loadDemoBtn");
const resultEmpty = document.getElementById("resultEmpty");
const resultCard = document.getElementById("resultCard");
const pageTitle = document.getElementById("pageTitle");
const navBtns = document.querySelectorAll(".nav-btn");

navBtns.forEach(btn => {
  btn.addEventListener("click", () => {
    navBtns.forEach(b => b.classList.remove("active"));
    btn.classList.add("active");
    const sport = btn.dataset.sport;
    sportSelect.value = sport;
    pageTitle.textContent = btn.textContent;
  });
});

function renderResult(data) {
  resultEmpty.classList.add("hidden");
  resultCard.classList.remove("hidden");
  resultCard.className = "result-card";

  resultCard.innerHTML = `
    <h2>${data.match}</h2>
    <p><strong>Gagnant probable :</strong> ${data.winner}</p>

    <div class="stats-grid">
      <div class="stat-box">
        <div class="stat-title">1</div>
        <div class="stat-value">${data.home_win}%</div>
      </div>
      <div class="stat-box">
        <div class="stat-title">X</div>
        <div class="stat-value">${data.draw}%</div>
      </div>
      <div class="stat-box">
        <div class="stat-title">2</div>
        <div class="stat-value">${data.away_win}%</div>
      </div>
      <div class="stat-box">
        <div class="stat-title">Confiance</div>
        <div class="stat-value">${data.confidence}%</div>
      </div>
    </div>

    <div class="badges">
      <span class="badge">BTTS Oui: ${data.btts_yes}%</span>
      <span class="badge">BTTS Non: ${data.btts_no}%</span>
      <span class="badge">Over 2.5: ${data.over_2_5}%</span>
      <span class="badge">Under 2.5: ${data.under_2_5}%</span>
    </div>

    <div><strong>Buts probables :</strong> ${data.home_goals_expected} - ${data.away_goals_expected}</div>
    <div><strong>Score probable :</strong> ${data.score_prediction}</div>

    <div>
      <h4>Historique récent</h4>
      <ul class="history-list">
        ${(data.recent_history || []).map(item => <li>${item.team}: ${item.result} (${item.score})</li>).join("")}
      </ul>
    </div>
  `;
}

analyzeBtn.addEventListener("click", async () => {
  const sport = sportSelect.value;
  const home = homeInput.value.trim();
  const away = awayInput.value.trim();

  if (!home || !away) {
    alert("Remplis les deux équipes.");
    return;
  }

  try {
    const res = await fetch(${API_URL}/predict, {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ sport, home, away })
    });

    const data = await res.json();

    if (!res.ok) {
      alert(data.error || "Erreur serveur");
      return;
    }

    renderResult(data);
  } catch (e) {
    alert("Impossible de contacter le backend.");
  }
});

loadDemoBtn.addEventListener("click", async () => {
  try {
    const res = await fetch(${API_URL}/demo);
    const data = await res.json();
    renderResult(data.football);
  } catch (e) {
    alert("Impossible de charger la démo.");
  }
});