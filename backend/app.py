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


def get_risk_badge(confidence):
    if confidence >= 78:
        return "SAFE"
    if confidence >= 62:
        return "MEDIUM"
    return "RISKY"


def analyze_finished_match(match):
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
        corners_weight = 2
        possession_weight = 0.35
        form_weight = 0.45
        history_weight = 0.30
        draw_base = 28
    elif sport == "basketball":
        score_weight = 1.3
        shots_weight = 1.8
        corners_weight = 0.2
        possession_weight = 0.12
        form_weight = 0.50
        history_weight = 0.24
        draw_base = 3
    elif sport == "tennis":
        score_weight = 18
        shots_weight = 2.2
        corners_weight = 0.0
        possession_weight = 0.0
        form_weight = 0.55
        history_weight = 0.32
        draw_base = 1
    else:
        score_weight = 16
        shots_weight = 2.0
        corners_weight = 0.0
        possession_weight = 0.0
        form_weight = 0.52
        history_weight = 0.30
        draw_base = 1

    home_power = (
        home_score * score_weight
        + home_half * (score_weight * 0.6)
        + home_shots * shots_weight
        + home_corners * corners_weight
        + home_possession * possession_weight
        + home_form * form_weight
        + home_history * history_weight
    )

    away_power = (
        away_score * score_weight
        + away_half * (score_weight * 0.6)
        + away_shots * shots_weight
        + away_corners * corners_weight
        + away_possession * possession_weight
        + away_form * form_weight
        + away_history * history_weight
    )

    gap = abs(home_power - away_power)
    confidence = clamp(round(52 + gap * 0.7), 50, 95)

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

    if home_score > away_score and home_win_pct < away_win_pct:
        home_win_pct, away_win_pct = away_win_pct, home_win_pct
    elif away_score > home_score and away_win_pct < home_win_pct:
        away_win_pct, home_win_pct = home_win_pct, away_win_pct

    total_pct = home_win_pct + draw_pct + away_win_pct
    if total_pct != 100:
        away_win_pct += 100 - total_pct

    attack_index = round((home_shots + away_shots + total_score + home_corners + away_corners) / 2)

    if sport in ["tennis", "table_tennis"]:
        likely_score = f"{max(home_score, away_score)}-{min(home_score, away_score)}"
    else:
        likely_score = f"{home_score}-{away_score}"

    if winner == "Nul":
        summary = "Match terminé très équilibré avec domination limitée des deux côtés."
    else:
        leader_side = "domicile" if winner == match.get("home_team") else "extérieur"
        if confidence >= 80:
            summary = f"Analyse post-match : nette supériorité du côté {leader_side}."
        elif confidence >= 68:
            summary = f"Analyse post-match : avantage modéré du côté {leader_side}."
        else:
            summary = f"Analyse post-match : rencontre ouverte avec léger avantage du côté {leader_side}."

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
        "risk_badge": get_risk_badge(confidence),
        "summary": summary,
    }


def analyze_upcoming_match(match):
    sport = match.get("sport", "football")

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

    if sport == "football":
        draw_base = 24
        home_power = (
            home_form * 0.30 +
            home_history * 0.24 +
            home_possession * 0.15 +
            home_shots * 2.2 +
            home_corners * 1.2 +
            6
        )
        away_power = (
            away_form * 0.30 +
            away_history * 0.24 +
            away_possession * 0.15 +
            away_shots * 2.2 +
            away_corners * 1.2
        )
    elif sport == "basketball":
        draw_base = 2
        home_power = (
            home_form * 0.35 +
            home_history * 0.22 +
            home_possession * 0.08 +
            home_shots * 2.5 +
            4
        )
        away_power = (
            away_form * 0.35 +
            away_history * 0.22 +
            away_possession * 0.08 +
            away_shots * 2.5
        )
    elif sport == "tennis":
        draw_base = 1
        home_power = (
            home_form * 0.40 +
            home_history * 0.28 +
            home_shots * 1.5 +
            3
        )
        away_power = (
            away_form * 0.40 +
            away_history * 0.28 +
            away_shots * 1.5
        )
    else:
        draw_base = 1
        home_power = (
            home_form * 0.38 +
            home_history * 0.27 +
            home_shots * 1.4 +
            3
        )
        away_power = (
            away_form * 0.38 +
            away_history * 0.27 +
            away_shots * 1.4
        )

    gap = abs(home_power - away_power)
    confidence = clamp(round(50 + gap * 1.1), 50, 92)

    if sport == "football":
        draw_factor = draw_base + max(8, 22 - int(gap))
    else:
        draw_factor = draw_base + max(1, 6 - int(gap // 4))

    home_win_pct, draw_pct, away_win_pct = normalize_percentages(
        max(1, home_power),
        max(1, draw_factor),
        max(1, away_power)
    )

    if home_power > away_power:
        winner = match.get("home_team", "Domicile")
        half_winner = match.get("home_team", "Domicile")
    elif away_power > home_power:
        winner = match.get("away_team", "Extérieur")
        half_winner = match.get("away_team", "Extérieur")
    else:
        winner = "Nul"
        half_winner = "Nul"

    attack_index = round((home_shots + away_shots + home_corners + away_corners) / 2)

    if sport == "football":
        if winner == "Nul":
            likely_score = "1-1"
        elif winner == match.get("home_team"):
            likely_score = "2-1" if confidence < 75 else "2-0"
        else:
            likely_score = "1-2" if confidence < 75 else "0-2"
        btts = likely_score in ["1-1", "2-1", "1-2", "2-2"]
        over_2_5 = likely_score in ["2-1", "1-2", "2-2", "3-1", "1-3"]
    elif sport == "basketball":
        if winner == match.get("home_team"):
            likely_score = "102-94"
        elif winner == match.get("away_team"):
            likely_score = "94-102"
        else:
            likely_score = "98-98"
        btts = True
        over_2_5 = True
    elif sport == "tennis":
        if winner == "Nul":
            likely_score = "1-1"
        elif winner == match.get("home_team"):
            likely_score = "2-1" if confidence < 78 else "2-0"
        else:
            likely_score = "1-2" if confidence < 78 else "0-2"
        btts = False
        over_2_5 = False
    else:
        if winner == "Nul":
            likely_score = "2-2"
        elif winner == match.get("home_team"):
            likely_score = "3-1"
        else:
            likely_score = "1-3"
        btts = False
        over_2_5 = False

    risk_badge = get_risk_badge(confidence)

    if winner == "Nul":
        summary = "Pronostic pré-match équilibré avec risque partagé entre les deux côtés."
    else:
        leader_side = "domicile" if winner == match.get("home_team") else "extérieur"
        if risk_badge == "SAFE":
            summary = f"Pronostic pré-match solide avec avantage net du côté {leader_side}."
        elif risk_badge == "MEDIUM":
            summary = f"Pronostic pré-match correct avec avantage modéré du côté {leader_side}."
        else:
            summary = f"Pronostic pré-match plus risqué avec léger avantage du côté {leader_side}."

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
        "risk_badge": risk_badge,
        "summary": summary,
    }


def analyze_match(match):
    status = match.get("status", "upcoming")
    if status == "finished":
        return analyze_finished_match(match)
    return analyze_upcoming_match(match)


def normalize_match(data, existing_id=None, created_at=None):
    match = {
        "id": existing_id or str(uuid4()),
        "sport": data.get("sport", "football"),
        "status": data.get("status", "upcoming"),
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


def smart_autofill(data):
    sport = (data.get("sport") or "football").strip()
    status = (data.get("status") or "upcoming").strip()
    home_team = (data.get("home_team") or "").strip()
    away_team = (data.get("away_team") or "").strip()
    match_date = (data.get("match_date") or "").strip()

    base_home_strength = 70 + (len(home_team) % 18)
    base_away_strength = 58 + (len(away_team) % 16)

    if any(name in home_team.lower() for name in ["real", "city", "psg", "barcelona", "lakers", "djokovic"]):
        base_home_strength += 10
    if any(name in away_team.lower() for name in ["real", "city", "psg", "barcelona", "celtics", "medvedev"]):
        base_away_strength += 8

    home_form = clamp(base_home_strength, 45, 95)
    away_form = clamp(base_away_strength, 40, 92)

    home_history = clamp(home_form - 4, 40, 95)
    away_history = clamp(away_form - 5, 35, 92)

    strength_gap = home_form - away_form

    if sport == "football":
        home_possession = clamp(52 + strength_gap // 2, 38, 67)
        away_possession = 100 - home_possession
        home_shots = clamp(5 + strength_gap // 6, 3, 10)
        away_shots = clamp(4 - strength_gap // 9, 2, 8)
        home_corners = clamp(4 + strength_gap // 7, 2, 9)
        away_corners = clamp(3 - strength_gap // 12, 1, 7)
    elif sport == "basketball":
        home_possession = 50
        away_possession = 50
        home_shots = clamp(18 + strength_gap // 3, 14, 32)
        away_shots = clamp(17 - strength_gap // 4, 12, 30)
        home_corners = 0
        away_corners = 0
    elif sport == "tennis":
        home_possession = 50
        away_possession = 50
        home_shots = clamp(9 + strength_gap // 5, 6, 15)
        away_shots = clamp(8 - strength_gap // 8, 5, 13)
        home_corners = 0
        away_corners = 0
    else:
        home_possession = 50
        away_possession = 50
        home_shots = clamp(7 + strength_gap // 6, 4, 12)
        away_shots = clamp(6 - strength_gap // 8, 3, 10)
        home_corners = 0
        away_corners = 0

    note = (
        f"Remplissage automatique intelligent : {home_team} affiche une forme estimée de {home_form}/100 "
        f"contre {away_form}/100 pour {away_team}. Les statistiques ont été estimées à partir d'un profil "
        f"pré-match pour un usage d'analyse {'post-match' if status == 'finished' else 'pré-match'}."
    )

    return {
        "sport": sport,
        "status": status,
        "home_team": home_team,
        "away_team": away_team,
        "match_date": match_date,
        "home_form": home_form,
        "away_form": away_form,
        "home_history": home_history,
        "away_history": away_history,
        "home_possession": home_possession,
        "away_possession": away_possession,
        "home_shots": home_shots,
        "away_shots": away_shots,
        "home_corners": home_corners,
        "away_corners": away_corners,
        "note": note
    }


@app.route("/")
def home():
    return jsonify({
        "message": "BetAI Premium V3 API running",
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


@app.route("/autofill-match", methods=["POST"])
def autofill_match():
    data = request.get_json(force=True)

    home_team = (data.get("home_team") or "").strip()
    away_team = (data.get("away_team") or "").strip()

    if not home_team or not away_team:
        return jsonify({"error": "Teams missing"}), 400

    return jsonify(smart_autofill(data))


@app.route("/seed-demo", methods=["POST"])
def seed_demo():
    global matches_db

    demo = [
        {
            "sport": "football",
            "status": "upcoming",
            "home_team": "Real Madrid",
            "away_team": "Séville",
            "home_score": 0,
            "away_score": 0,
            "match_date": "2026-04-12",
            "home_half_score": 0,
            "away_half_score": 0,
            "home_possession": 60,
            "away_possession": 40,
            "home_shots": 7,
            "away_shots": 3,
            "home_corners": 6,
            "away_corners": 2,
            "home_form": 88,
            "away_form": 61,
            "home_history": 90,
            "away_history": 58,
            "image_url": "",
            "note": "Pronostic pré-match avec avantage domicile."
        },
        {
            "sport": "football",
            "status": "finished",
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
            "status": "upcoming",
            "home_team": "Lakers",
            "away_team": "Celtics",
            "home_score": 0,
            "away_score": 0,
            "match_date": "2026-04-11",
            "home_half_score": 0,
            "away_half_score": 0,
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
            "note": "Léger avantage statistique domicile."
        },
        {
            "sport": "tennis",
            "status": "upcoming",
            "home_team": "Djokovic",
            "away_team": "Medvedev",
            "home_score": 0,
            "away_score": 0,
            "match_date": "2026-04-10",
            "home_half_score": 0,
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
            "note": "Confrontation de haut niveau, avantage léger au favori."
        }
    ]

    matches_db = [normalize_match(item) for item in demo]
    return jsonify({"success": True, "count": len(matches_db)})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)