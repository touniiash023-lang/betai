from flask import Flask, jsonify, request
from flask_cors import CORS
from uuid import uuid4
from datetime import datetime

app = Flask(__name__)
CORS(app)

matches_db = []


def safe_int(value, default=0):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def clamp(value, low, high):
    return max(low, min(high, value))


def normalize_percentages(home, draw, away):
    total = home + draw + away
    if total <= 0:
        return 33, 34, 33

    home_pct = round((home / total) * 100)
    draw_pct = round((draw / total) * 100)
    away_pct = 100 - home_pct - draw_pct

    if away_pct < 0:
      away_pct = 0
      diff = 100 - home_pct - draw_pct
      if diff > 0:
          draw_pct += diff

    return home_pct, draw_pct, away_pct


def analyze_match(match):
    sport = match.get("sport", "football")

    home_score = safe_int(match.get("home_score"))
    away_score = safe_int(match.get("away_score"))
    home_half = safe_int(match.get("home_half_score"))
    away_half = safe_int(match.get("away_half_score"))
    home_possession = clamp(safe_int(match.get("home_possession"), 50), 0, 100)
    away_possession = clamp(safe_int(match.get("away_possession"), 50), 0, 100)
    home_shots = safe_int(match.get("home_shots"))
    away_shots = safe_int(match.get("away_shots"))
    home_corners = safe_int(match.get("home_corners"))
    away_corners = safe_int(match.get("away_corners"))
    home_form = clamp(safe_int(match.get("home_form"), 50), 0, 100)
    away_form = clamp(safe_int(match.get("away_form"), 50), 0, 100)
    home_history = clamp(safe_int(match.get("home_history"), 50), 0, 100)
    away_history = clamp(safe_int(match.get("away_history"), 50), 0, 100)

    total_score = home_score + away_score
    btts = home_score > 0 and away_score > 0
    over_2_5 = total_score >= 3

    if home_half > away_half:
        half_winner = match.get("home_team", "Domicile")
    elif away_half > home_half:
        half_winner = match.get("away_team", "Extérieur")
    else:
        half_winner = "Nul"

    if home_score > away_score:
        winner = match.get("home_team", "Domicile")
    elif away_score > home_score:
        winner = match.get("away_team", "Extérieur")
    else:
        winner = "Nul"

    if sport == "football":
        score_weight = 12
        shots_weight = 3
        bonus_weight = 2
        possession_weight = 0.35
        form_weight = 0.45
        history_weight = 0.30
        draw_base = 28
    elif sport == "basketball":
        score_weight = 1.3
        shots_weight = 1.8
        bonus_weight = 0.6
        possession_weight = 0.12
        form_weight = 0.50
        history_weight = 0.24
        draw_base = 3
    elif sport == "tennis":
        score_weight = 18
        shots_weight = 2.2
        bonus_weight = 0.3
        possession_weight = 0.0
        form_weight = 0.55
        history_weight = 0.32
        draw_base = 1
    else:
        score_weight = 16
        shots_weight = 2.0
        bonus_weight = 0.3
        possession_weight = 0.0
        form_weight = 0.52
        history_weight = 0.30
        draw_base = 1

    home_power = (
        home_score * score_weight
        + home_half * (score_weight * 0.6)
        + home_shots * shots_weight
        + home_corners * bonus_weight
        + home_possession * possession_weight
        + home_form * form_weight
        + home_history * history_weight
    )

    away_power = (
        away_score * score_weight
        + away_half * (score_weight * 0.6)
        + away_shots * shots_weight
        + away_corners * bonus_weight
        + away_possession * possession_weight
        + away_form * form_weight
        + away_history * history_weight
    )

    gap = abs(home_power - away_power)

    # Plus l'écart est grand, plus la confiance monte
    confidence = clamp(round(52 + gap * 0.7), 50, 95)

    # Probabilités brutes
    home_raw = home_power + 8
    away_raw = away_power + 8

    draw_factor = draw_base
    if sport == "football":
        draw_factor += max(0, 20 - int(gap // 2))
        if abs(home_score - away_score) <= 1:
            draw_factor += 10
    else:
        draw_factor += max(0, 6 - int(gap // 8))

    home_win_pct, draw_pct, away_win_pct = normalize_percentages(
        max(1, home_raw),
        max(1, draw_factor),
        max(1, away_raw)
    )

    # Ajustement selon résultat saisi
    if home_score > away_score and home_win_pct < away_win_pct:
        home_win_pct, away_win_pct = away_win_pct, home_win_pct
    elif away_score > home_score and away_win_pct < home_win_pct:
        away_win_pct, home_win_pct = home_win_pct, away_win_pct

    # Rééquilibrage à 100
    total_pct = home_win_pct + draw_pct + away_win_pct
    if total_pct != 100:
        away_win_pct += 100 - total_pct

    attack_index = round((home_shots + away_shots + total_score + home_corners + away_corners) / 2)

    if sport in ["tennis", "table_tennis"]:
        likely_score = f"{max(home_score, away_score)}-{min(home_score, away_score)}"
    else:
        if winner == "Nul":
            likely_score = "1-1" if sport == "football" else f"{home_score}-{away_score}"
        else:
            likely_score = f"{home_score}-{away_score}"

    if winner == "Nul":
        summary = "Rencontre très équilibrée avec probabilité serrée entre les deux côtés."
    else:
        leader_side = "domicile" if winner == match.get("home_team") else "extérieur"
        if confidence >= 80:
            summary = f"Avantage net du côté {leader_side} avec supériorité statistique marquée."
        elif confidence >= 68:
            summary = f"Avantage modéré du côté {leader_side} avec meilleure dynamique globale."
        else:
            summary = f"Match relativement ouvert avec léger avantage du côté {leader_side}."

    return {
        "winner": winner,
        "half_winner": half_winner,
        "btts": btts,
        "over_2_5": over_2_5,
        "likely_score": likely_score,
        "confidence": confidence,
        "home_win_pct": home_win_pct,
        "draw_pct": draw_pct,
        "away_win_pct": away_win_pct,
        "attack_index": attack_index,
        "summary": summary,
    }


def normalize_match(data, existing_id=None, created_at=None):
    match = {
        "id": existing_id or str(uuid4()),
        "sport": data.get("sport", "football"),
        "home_team": (data.get("home_team") or "").strip(),
        "away_team": (data.get("away_team") or "").strip(),
        "home_score": safe_int(data.get("home_score")),
        "away_score": safe_int(data.get("away_score")),
        "match_date": (data.get("match_date") or "").strip(),
        "home_half_score": safe_int(data.get("home_half_score")),
        "away_half_score": safe_int(data.get("away_half_score")),
        "home_possession": clamp(safe_int(data.get("home_possession"), 50), 0, 100),
        "away_possession": clamp(safe_int(data.get("away_possession"), 50), 0, 100),
        "home_shots": safe_int(data.get("home_shots")),
        "away_shots": safe_int(data.get("away_shots")),
        "home_corners": safe_int(data.get("home_corners")),
        "away_corners": safe_int(data.get("away_corners")),
        "home_form": clamp(safe_int(data.get("home_form"), 50), 0, 100),
        "away_form": clamp(safe_int(data.get("away_form"), 50), 0, 100),
        "home_history": clamp(safe_int(data.get("home_history"), 50), 0, 100),
        "away_history": clamp(safe_int(data.get("away_history"), 50), 0, 100),
        "image_url": (data.get("image_url") or "").strip(),
        "note": (data.get("note") or "").strip(),
        "created_at": created_at or datetime.utcnow().isoformat()
    }
    match["analysis"] = analyze_match(match)
    return match


@app.route("/")
def home():
    return jsonify({
        "message": "BetAI Premium API running",
        "status": "ok"
    })


@app.route("/matches", methods=["GET"])
def get_matches():
    return jsonify(matches_db)


@app.route("/matches", methods=["POST"])
def create_match():
    data = request.get_json(force=True)
    match = normalize_match(data)
    matches_db.insert(0, match)
    return jsonify(match), 201


@app.route("/matches/<match_id>", methods=["PUT"])
def update_match(match_id):
    data = request.get_json(force=True)
    for index, existing in enumerate(matches_db):
        if existing["id"] == match_id:
            updated = normalize_match(
                data,
                existing_id=match_id,
                created_at=existing.get("created_at")
            )
            matches_db[index] = updated
            return jsonify(updated)
    return jsonify({"error": "Match introuvable"}), 404


@app.route("/matches/<match_id>", methods=["DELETE"])
def delete_match(match_id):
    global matches_db
    before = len(matches_db)
    matches_db = [m for m in matches_db if m["id"] != match_id]
    if len(matches_db) == before:
        return jsonify({"error": "Match introuvable"}), 404
    return jsonify({"success": True})


@app.route("/matches/export", methods=["GET"])
def export_matches():
    return jsonify(matches_db)


@app.route("/matches/import", methods=["POST"])
def import_matches():
    global matches_db
    data = request.get_json(force=True)

    if not isinstance(data, list):
        return jsonify({"error": "Le JSON doit être une liste de matchs"}), 400

    imported = []
    for item in data:
        if isinstance(item, dict):
            imported.append(
                normalize_match(
                    item,
                    created_at=item.get("created_at")
                )
            )

    matches_db = imported
    return jsonify({"success": True, "count": len(matches_db)})


@app.route("/seed-demo", methods=["POST"])
def seed_demo():
    global matches_db

    demo = [
        {
            "sport": "football",
            "home_team": "Real Madrid",
            "away_team": "Séville",
            "home_score": 3,
            "away_score": 1,
            "match_date": "2026-04-08",
            "home_half_score": 1,
            "away_half_score": 0,
            "home_possession": 61,
            "away_possession": 39,
            "home_shots": 8,
            "away_shots": 3,
            "home_corners": 6,
            "away_corners": 2,
            "home_form": 88,
            "away_form": 61,
            "home_history": 90,
            "away_history": 58,
            "image_url": "",
            "note": "Domination offensive du domicile avec meilleure dynamique récente."
        },
        {
            "sport": "football",
            "home_team": "PSG",
            "away_team": "Lyon",
            "home_score": 2,
            "away_score": 2,
            "match_date": "2026-04-06",
            "home_half_score": 1,
            "away_half_score": 1,
            "home_possession": 54,
            "away_possession": 46,
            "home_shots": 6,
            "away_shots": 5,
            "home_corners": 4,
            "away_corners": 3,
            "home_form": 82,
            "away_form": 76,
            "home_history": 85,
            "away_history": 71,
            "image_url": "",
            "note": "Affiche ouverte entre deux équipes capables de marquer."
        },
        {
            "sport": "basketball",
            "home_team": "Lakers",
            "away_team": "Celtics",
            "home_score": 108,
            "away_score": 101,
            "match_date": "2026-04-05",
            "home_half_score": 54,
            "away_half_score": 48,
            "home_possession": 50,
            "away_possession": 50,
            "home_shots": 24,
            "away_shots": 20,
            "home_corners": 0,
            "away_corners": 0,
            "home_form": 84,
            "away_form": 79,
            "home_history": 78,
            "away_history": 77,
            "image_url": "",
            "note": "Meilleure efficacité offensive du domicile."
        },
        {
            "sport": "tennis",
            "home_team": "Djokovic",
            "away_team": "Medvedev",
            "home_score": 2,
            "away_score": 1,
            "match_date": "2026-04-04",
            "home_half_score": 1,
            "away_half_score": 0,
            "home_possession": 50,
            "away_possession": 50,
            "home_shots": 12,
            "away_shots": 10,
            "home_corners": 0,
            "away_corners": 0,
            "home_form": 91,
            "away_form": 84,
            "home_history": 93,
            "away_history": 80,
            "image_url": "",
            "note": "Match serré mais légère maîtrise du favori."
        },
        {
            "sport": "table_tennis",
            "home_team": "Player A",
            "away_team": "Player B",
            "home_score": 3,
            "away_score": 0,
            "match_date": "2026-04-03",
            "home_half_score": 1,
            "away_half_score": 0,
            "home_possession": 50,
            "away_possession": 50,
            "home_shots": 9,
            "away_shots": 3,
            "home_corners": 0,
            "away_corners": 0,
            "home_form": 86,
            "away_form": 62,
            "home_history": 84,
            "away_history": 60,
            "image_url": "",
            "note": "Supériorité nette dans les échanges rapides."
        }
    ]

    matches_db = [normalize_match(item) for item in demo]
    return jsonify({"success": True, "count": len(matches_db)})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)