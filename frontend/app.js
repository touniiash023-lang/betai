const storageKey = "betai_sport_analytics_v1";

let currentSport = "football";
let editingId = null;

const initialData = {
  football: [],
  basket: [],
  tennis: [],
  tt: []
};

let db = loadStorage();

const menuItems = document.querySelectorAll(".menu-item");
const pageTitle = document.getElementById("pageTitle");
const matchList = document.getElementById("matchList");
const searchInput = document.getElementById("searchInput");

const homeTeam = document.getElementById("homeTeam");
const awayTeam = document.getElementById("awayTeam");
const finalScore = document.getElementById("finalScore");
const halfScore = document.getElementById("halfScore");
const shots = document.getElementById("shots");
const corners = document.getElementById("corners");
const notes = document.getElementById("notes");
const supplierLink = document.getElementById("supplierLink");
const matchImage = document.getElementById("matchImage");

const saveBtn = document.getElementById("saveBtn");
const clearBtn = document.getElementById("clearBtn");
const loadDemoBtn = document.getElementById("loadDemoBtn");
const exportBtn = document.getElementById("exportBtn");
const importJson = document.getElementById("importJson");

const statTotal = document.getElementById("statTotal");
const statAvg = document.getElementById("statAvg");
const statBtts = document.getElementById("statBtts");
const statStrong = document.getElementById("statStrong");

menuItems.forEach(btn => {
  btn.addEventListener("click", () => {
    menuItems.forEach(x => x.classList.remove("active"));
    btn.classList.add("active");
    currentSport = btn.dataset.sport;
    editingId = null;
    updateTitle();
    clearForm();
    render();
  });
});

saveBtn.addEventListener("click", saveMatch);
clearBtn.addEventListener("click", clearForm);
loadDemoBtn.addEventListener("click", loadDemoData);
exportBtn.addEventListener("click", exportCurrentSport);
searchInput.addEventListener("input", render);

importJson.addEventListener("change", handleImport);

function updateTitle() {
  const map = {
    football: "Football réel",
    basket: "Basket",
    tennis: "Tennis",
    tt: "Tennis de table"
  };
  pageTitle.textContent = map[currentSport];
}

function loadStorage() {
  const raw = localStorage.getItem(storageKey);
  if (!raw) return structuredClone(initialData);
  try {
    return JSON.parse(raw);
  } catch {
    return structuredClone(initialData);
  }
}

function saveStorage() {
  localStorage.setItem(storageKey, JSON.stringify(db));
}

function clearForm() {
  editingId = null;
  homeTeam.value = "";
  awayTeam.value = "";
  finalScore.value = "";
  halfScore.value = "";
  shots.value = "";
  corners.value = "";
  notes.value = "";
  supplierLink.value = "";
  matchImage.value = "";
  saveBtn.textContent = "Enregistrer";
}

function parseScore(scoreText) {
  if (!scoreText.includes("-")) return [0, 0];
  const parts = scoreText.split("-").map(x => parseInt(x.trim(), 10));
  return [parts[0] || 0, parts[1] || 0];
}

function buildAnalysis(item) {
  const [home, away] = parseScore(item.finalScore);
  const [halfHome, halfAway] = parseScore(item.halfScore);

  if (currentSport === "football") {
    const totalGoals = home + away;
    const btts = home > 0 && away > 0 ? "Oui" : "Non";
    const firstHalfWinner = halfHome > halfAway ? item.homeTeam : halfAway > halfHome ? item.awayTeam : "Nul";
    const finalWinner = home > away ? item.homeTeam : away > home ? item.awayTeam : "Nul";
    const confidence = Math.min(95, 50 + Math.abs(home - away) * 12 + (totalGoals >= 3 ? 6 : 0));

    return {
      line1: `Score final : ${item.finalScore}`,
      line2: `Mi-temps : ${item.halfScore}`,
      line3: `Les deux équipes marquent : ${btts}`,
      line4: `Nombre total de buts : ${totalGoals}`,
      line5: `Vainqueur 1re mi-temps : ${firstHalfWinner}`,
      line6: `Buts 1re mi-temps : ${halfHome + halfAway}`,
      line7: `Vainqueur final : ${finalWinner}`,
      confidence
    };
  }

  if (currentSport === "basket") {
    const total = home + away;
    const finalWinner = home > away ? item.homeTeam : away > home ? item.awayTeam : "Égalité";
    const confidence = Math.min(95, 52 + Math.abs(home - away) * 2);

    return {
      line1: `Score final : ${item.finalScore}`,
      line2: `Score à la pause : ${item.halfScore}`,
      line3: `Total points : ${total}`,
      line4: `Écart de points : ${Math.abs(home - away)}`,
      line5: `Leader à la pause : ${halfHome > halfAway ? item.homeTeam : halfAway > halfHome ? item.awayTeam : "Égalité"}`,
      line6: `Points 1re période : ${halfHome + halfAway}`,
      line7: `Vainqueur final : ${finalWinner}`,
      confidence
    };
  }

  if (currentSport === "tennis" || currentSport === "tt") {
    const setsHome = home;
    const setsAway = away;
    const winner = setsHome > setsAway ? item.homeTeam : setsAway > setsHome ? item.awayTeam : "Égalité";
    const confidence = Math.min(95, 55 + Math.abs(setsHome - setsAway) * 10);

    return {
      line1: `Score sets/manches : ${item.finalScore}`,
      line2: `1er set/manche : ${item.halfScore}`,
      line3: `Vainqueur 1er set : ${halfHome > halfAway ? item.homeTeam : halfAway > halfHome ? item.awayTeam : "Égalité"}`,
      line4: `Sets/manches totaux : ${setsHome + setsAway}`,
      line5: `Vainqueur final : ${winner}`,
      line6: `Stat optionnelle : ${item.shots || "N/A"}`,
      line7: `Autre stat : ${item.corners || "N/A"}`,
      confidence
    };
  }

  return {
    line1: `Score : ${item.finalScore}`,
    line2: `Mi-temps : ${item.halfScore}`,
    line3: "",
    line4: "",
    line5: "",
    line6: "",
    line7: "",
    confidence: 50
  };
}

function saveMatch() {
  const item = {
    id: editingId || crypto.randomUUID(),
    homeTeam: homeTeam.value.trim(),
    awayTeam: awayTeam.value.trim(),
    finalScore: finalScore.value.trim(),
    halfScore: halfScore.value.trim(),
    shots: shots.value.trim(),
    corners: corners.value.trim(),
    notes: notes.value.trim(),
    supplierLink: supplierLink.value.trim(),
    imageUrl: ""
  };

  if (!item.homeTeam || !item.awayTeam || !item.finalScore) {
    alert("Remplis au moins équipe domicile, équipe extérieure et score final.");
    return;
  }

  const file = matchImage.files[0];

  if (file) {
    const reader = new FileReader();
    reader.onload = () => {
      item.imageUrl = reader.result;
      upsertItem(item);
    };
    reader.readAsDataURL(file);
  } else {
    if (editingId) {
      const old = db[currentSport].find(x => x.id === editingId);
      item.imageUrl = old?.imageUrl || "";
    }
    upsertItem(item);
  }
}

function upsertItem(item) {
  const list = db[currentSport];
  const index = list.findIndex(x => x.id === item.id);

  if (index >= 0) list[index] = item;
  else list.unshift(item);

  saveStorage();
  clearForm();
  render();
}

function editMatch(id) {
  const item = db[currentSport].find(x => x.id === id);
  if (!item) return;

  editingId = id;
  homeTeam.value = item.homeTeam;
  awayTeam.value = item.awayTeam;
  finalScore.value = item.finalScore;
  halfScore.value = item.halfScore;
  shots.value = item.shots || "";
  corners.value = item.corners || "";
  notes.value = item.notes || "";
  supplierLink.value = item.supplierLink || "";
  saveBtn.textContent = "Mettre à jour";
  window.scrollTo({ top: 0, behavior: "smooth" });
}

function deleteMatch(id) {
  db[currentSport] = db[currentSport].filter(x => x.id !== id);
  saveStorage();
  render();
}

function render() {
  const query = searchInput.value.trim().toLowerCase();
  const items = db[currentSport].filter(item => {
    const text = `${item.homeTeam} ${item.awayTeam} ${item.finalScore} ${item.notes}`.toLowerCase();
    return text.includes(query);
  });

  if (!items.length) {
    matchList.innerHTML = `<div class="empty">Aucun match disponible pour ce sport.</div>`;
    updateStats([]);
    return;
  }

  matchList.innerHTML = items.map(item => {
    const a = buildAnalysis(item);

    return `
      <div class="match-card">
        <img class="match-thumb" src="${item.imageUrl || "https://via.placeholder.com/90?text=Match"}" alt="capture match">
        <div class="match-main">
          <h3>${escapeHtml(item.homeTeam)} vs ${escapeHtml(item.awayTeam)}</h3>
          <p>${a.line1}</p>
          <p>${a.line2}</p>
          <p>${a.line3}</p>
          <p>${a.line4}</p>
          <p>${a.line5}</p>
          <p>${a.line6}</p>
          <p>${a.line7}</p>
          ${item.notes ? `<p>${escapeHtml(item.notes)}</p>` : ""}
          <div>
            <span class="tag">Indice analytique ${a.confidence}%</span>
            ${item.shots ? `<span class="tag">Stat 1: ${escapeHtml(item.shots)}</span>` : ""}
            ${item.corners ? `<span class="tag">Stat 2: ${escapeHtml(item.corners)}</span>` : ""}
          </div>
          ${item.supplierLink ? `<p><a href="${escapeAttr(item.supplierLink)}" target="_blank">Voir la source</a></p>` : ""}
        </div>
        <div class="match-price">
          <div class="analysis">Analyse</div>
          <p>${a.confidence}%</p>
          <button class="secondary-btn" onclick="editMatch('${item.id}')">Modifier</button>
          <button class="primary-btn" style="margin-top:8px;background:#ef4444;" onclick="deleteMatch('${item.id}')">Supprimer</button>
        </div>
      </div>
    `;
  }).join("");

  updateStats(items);
}

function updateStats(items) {
  statTotal.textContent = items.length;

  if (!items.length) {
    statAvg.textContent = 0;
    statBtts.textContent = 0;
    statStrong.textContent = 0;
    return;
  }

  let totalScore = 0;
  let bttsCount = 0;
  let strong = 0;

  items.forEach(item => {
    const [a, b] = parseScore(item.finalScore);
    totalScore += a + b;

    if (currentSport === "football" && a > 0 && b > 0) bttsCount++;

    const conf = buildAnalysis(item).confidence;
    if (conf >= 70) strong++;
  });

  statAvg.textContent = (totalScore / items.length).toFixed(1);
  statBtts.textContent = currentSport === "football" ? bttsCount : "-";
  statStrong.textContent = strong;
}

function loadDemoData() {
  db = {
    ...db,
    football: [
      {
        id: crypto.randomUUID(),
        homeTeam: "Real Madrid",
        awayTeam: "Sevilla",
        finalScore: "3-1",
        halfScore: "1-0",
        shots: "8 tirs cadrés",
        corners: "6 corners",
        notes: "Match offensif avec domination domicile.",
        supplierLink: "",
        imageUrl: ""
      },
      {
        id: crypto.randomUUID(),
        homeTeam: "PSG",
        awayTeam: "Lyon",
        finalScore: "2-2",
        halfScore: "1-1",
        shots: "7 tirs cadrés",
        corners: "5 corners",
        notes: "BTTS confirmé.",
        supplierLink: "",
        imageUrl: ""
      }
    ],
    basket: [
      {
        id: crypto.randomUUID(),
        homeTeam: "Lakers",
        awayTeam: "Celtics",
        finalScore: "112-104",
        halfScore: "58-50",
        shots: "3pts: 14",
        corners: "Rebonds: 42",
        notes: "Bonne gestion du 4e quart-temps.",
        supplierLink: "",
        imageUrl: ""
      }
    ],
    tennis: [
      {
        id: crypto.randomUUID(),
        homeTeam: "Djokovic",
        awayTeam: "Medvedev",
        finalScore: "2-1",
        halfScore: "6-4",
        shots: "Aces: 9",
        corners: "Breaks: 3",
        notes: "Renversement après le 1er set.",
        supplierLink: "",
        imageUrl: ""
      }
    ],
    tt: [
      {
        id: crypto.randomUUID(),
        homeTeam: "Player A",
        awayTeam: "Player B",
        finalScore: "3-1",
        halfScore: "11-8",
        shots: "Services gagnants: 5",
        corners: "Erreurs directes: 7",
        notes: "Contrôle du rythme.",
        supplierLink: "",
        imageUrl: ""
      }
    ]
  };

  saveStorage();
  render();
}

function exportCurrentSport() {
  const blob = new Blob([JSON.stringify(db[currentSport], null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `${currentSport}-matches.json`;
  a.click();
  URL.revokeObjectURL(url);
}

function handleImport(event) {
  const file = event.target.files[0];
  if (!file) return;

  const reader = new FileReader();
  reader.onload = () => {
    try {
      const imported = JSON.parse(reader.result);
      if (!Array.isArray(imported)) {
        alert("Le fichier doit contenir une liste JSON.");
        return;
      }

      db[currentSport] = imported.map(item => ({
        id: item.id || crypto.randomUUID(),
        homeTeam: item.homeTeam || "",
        awayTeam: item.awayTeam || "",
        finalScore: item.finalScore || "0-0",
        halfScore: item.halfScore || "0-0",
        shots: item.shots || "",
        corners: item.corners || "",
        notes: item.notes || "",
        supplierLink: item.supplierLink || "",
        imageUrl: item.imageUrl || ""
      }));

      saveStorage();
      render();
      alert("Import réussi.");
    } catch {
      alert("Fichier JSON invalide.");
    }
  };
  reader.readAsText(file);
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

updateTitle();
render();

window.editMatch = editMatch;
window.deleteMatch = deleteMatch;