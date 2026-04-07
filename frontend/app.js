async function loadAll(){

  const res = await fetch("http://127.0.0.1:5000/api/predictions");
  const data = await res.json();

  let html = "";

  data.forEach(m => {
    html += `
      <div class="card">
        <h2>${m.match}</h2>
        Prediction: ${m.prediction}<br>
        Home Win: ${m.probabilities.home_win}%<br>
        Draw: ${m.probabilities.draw}%<br>
        Away Win: ${m.probabilities.away_win}%
      </div>
    `;
  });

  document.getElementById("result").innerHTML = html;
}