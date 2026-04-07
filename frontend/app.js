const API_URL = "https://betai-backend-dovc.onrender.com/api/predictions";

const pageTitle = document.getElementById("pageTitle");
const panelTitle = document.getElementById("panelTitle");
const result = document.getElementById("result");
const apiStatus = document.getElementById("apiStatus");

const statMatches = document.getElementById("statMatches");
const statStrong = document.getElementById("statStrong");
const statTop = document.getElementById("statTop");

const menuItems = document.querySelectorAll(".menu-item");

menuItems.forEach((btn) => {
  btn.addEventListener("click", () => {
    menuItems.forEach((item) => item.classList.remove("active"));
    btn.classList.add("active");

    const page = btn.dataset.page;
    changePage(page);
  });
});

function changePage(page) {
  if (page === "dashboard" || page === "football") {
    pageTitle.textContent = page === "dashboard" ? "Tableau de bord" : "Football";
    panelTitle.textContent = "Prédictions Football";
    loadFootballPredictions();
    return;
  }

  if (page === "aviator") {
    pageTitle.textContent = "Aviator";
    panelTitle.textContent = "Signal Aviator";
    result.innerHTML = `
      <div class="prediction-card">
        <h3>🎯 Aviator</h3>
        <div class="prediction-row">
          Cashout conseillé : <strong>1.72x</strong><br>
          Niveau de risque : <strong>Modéré</strong><br>
          Confiance : <strong>78%</strong><br>
          <span class="badge">Signal stable</span>
        </div>
      </div>
    `;
    updateStats(1, 1, "Aviator");
    apiStatus.textContent = "Module interne chargé";
    return;
  }

  if (page === "mines") {
    pageTitle.textContent = "Mines";
    panelTitle.textContent = "Stratégie Mines";
    result.innerHTML = `
      <div class="prediction-card">
        <h3>💣 Mines</h3>
        <div class="prediction-row">
          Stratégie : <strong>3 cases sûres</strong><br>
          Approche : <strong>Prudente</strong><br>
          Confiance : <strong>74%</strong><br>
          <span class="badge">Faible risque</span>
        </div>
      </div>
    `;
    updateStats(1, 1, "Mines");
    apiStatus.textContent = "Module interne chargé";
    return;
  }

  if (page === "virtual") {
    pageTitle.textContent = "Virtual";
    panelTitle.textContent = "Analyse Virtual";
    result.innerHTML = `
      <div class="prediction-card">
        <h3>🎮 Virtual</h3>
        <div class="prediction-row">
          Tendance : <strong>Hausse</strong><br>
          Signal : <strong>Over 1.5</strong><br>
          Confiance : <strong>81%</strong><br>
          <span class="badge">Bon timing</span>
        </div>
      </div>
    `;
    updateStats(1, 1, "Virtual");
    apiStatus.textContent = "Module interne chargé";
    return;
  }

  if (page === "settings") {
    pageTitle.textContent = "Paramètres";
    panelTitle.textContent = "Configuration";
    result.innerHTML = `
      <div class="prediction-card">
        <h3>⚙️ Paramètres</h3>
        <div class="prediction-row">
          API : <strong>Connectée</strong><br>
          Version : <strong>BetAI Pro v1</strong><br>
          Hébergement : <strong>Netlify + Render</strong><br>
          <span class="badge">Système actif</span>
        </div>
      </div>
    `;
    updateStats(1, 0, "BetAI Pro");
    apiStatus.textContent = "Configuration disponible";
  }
}

async function loadFootballPredictions() {
  result.innerHTML = `<div class="empty-state">Chargement des prédictions...</div>`;
  apiStatus.textContent = "Connexion en cours...";

  try {
    const res = await fetch(API_URL);
    const data = await res.json();

    let html = "";
    let strongCount = 0;
    let topPrediction = "-";

    data.forEach((m, index) => {
      const probs = m.probabilities;
      const maxProb = Math.max(probs.home_win, probs.draw, probs.away_win);

      if (maxProb >= 70) strongCount++;

      if (index === 0) {
        topPrediction = m.prediction;
      }

      html += `
        <div class="prediction-card">
          <h3>${m.match}</h3>
          <div class="prediction-row">
            Prediction : <strong>${formatPrediction(m.prediction)}</strong><br>
            Home Win : <strong>${probs.home_win}%</strong><br>
            Draw : <strong>${probs.draw}%</strong><br>
            Away Win : <strong>${probs.away_win}%</strong><br>
            <span class="badge">Confiance max : ${maxProb}%</span>
          </div>
        </div>
      `;
    });

    result.innerHTML = html;
    apiStatus.textContent = "API connectée et active";
    updateStats(data.length, strongCount, formatPrediction(topPrediction));
  } catch (error) {
    result.innerHTML = `<div class="empty-state">Erreur de chargement des données.</div>`;
    apiStatus.textContent = "Erreur de connexion API";
    updateStats(0, 0, "-");
    console.error(error);
  }
}

function updateStats(matches, strong, top) {
  statMatches.textContent = matches;
  statStrong.textContent = strong;
  statTop.textContent = top;
}

function formatPrediction(prediction) {
  if (prediction === "home_win") return "Victoire domicile";
  if (prediction === "away_win") return "Victoire extérieur";
  if (prediction === "draw") return "Match nul";
  return prediction;
}

loadFootballPredictions();