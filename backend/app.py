from flask import Flask, jsonify, request
from flask_cors import CORS
from uuid import uuid4
from datetime import datetime
import os
import requests

app = Flask(__name__)

CORS(app)

@app.after_request
def after_request(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET,POST,PUT,DELETE,OPTIONS"
    return response

matches_db = []

FOOTBALL_API_KEY = os.getenv("FOOTBALL_API_KEY", "").strip()
FOOTBALL_BASE_URL = "https://api.football-data.org/v4"
# -----------------------------
# Helpers
# -----------------------------
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
        total2 = home_pct + draw_pct
        if total2 < 100:
            draw_pct += 100 - total2

    return home_pct, draw_pct, away_pct


def get_risk_badge(confidence):
    if confidence >= 78:
        return "SAFE"
    if confidence >= 62:
        return "MEDIUM"
    return "RISKY"


def now_iso():
    return datetime.utcnow().isoformat()


# -----------------------------
# football-data.org helpers
# -----------------------------
def football_headers():
    if not FOOTBALL_API_KEY:
        return None
    return {"X-Auth-Token": FOOTBALL_API_KEY}


def football_api_get(path, params=None):
    headers = football_headers()
    if not headers:
        return None

    try:
        response = requests.get(
            f"{FOOTBALL_BASE_URL}{path}",
            headers=headers,
            params=params or {},
            timeout=20,
        )
        if response.status_code != 200:
            return None
        return response.json()
    except requests.RequestException:
        return None


def find_team_id_by_name(team_name):
    if not team_name.strip():
        return None

    data = football_api_get("/teams")
    if not data:
        return None

    teams = data.get("teams", [])
    team_name_lower = team_name.strip().lower()

    exact = None
    partial = None

    for team in teams:
        name = (team.get("name") or "").lower()
        short_name = (team.get("shortName") or "").lower()
        tla = (team.get("tla") or "").lower()

        if team_name_lower == name or team_name_lower == short_name or team_name_lower == tla:
            exact = team
            break

        if team_name_lower in name or team_name_lower in short_name:
            partial = team

    found = exact or partial
    return found.get("id") if found else None


def smart_autofill(data):
    sport = (data.get("sport") or "football").strip()
    status = (data.get("status") or "upcoming").strip()
    home_team = (data.get("home_team") or "").strip()
    away_team = (data.get("away_team") or "").strip()
    match_date = (data.get("match_date") or "").strip()

    if not home_team or not away_team:
        return {
            "error": "Nom d'équipe manquant"
        }

    if sport != "football" or not FOOTBALL_API_KEY:
        base_home = 70 + (len(home_team) % 15)
        base_away = 60 + (len(away_team) % 13)
        home_form = clamp(base_home, 40, 94)
        away_form = clamp(base_away, 35, 90)
        home_history, away_history = estimate_history_score(home_form, away_form)
        home_possession, away_possession = estimate_possession(home_form, away_form)

        if sport == "football":
            home_shots, away_shots, home_corners, away_corners = 6, 4, 5, 3
        elif sport == "basketball":
            home_shots, away_shots, home_corners, away_corners = 22, 19, 0, 0
        elif sport == "tennis":
            home_shots, away_shots, home_corners, away_corners = 10, 8, 0, 0
        else:
            home_shots, away_shots, home_corners, away_corners = 7, 6, 0, 0

        return {
            "sport": sport,
            "status": status,
            "home_team": home_team,
            "away_team": away_team,
            "match_date": match_date,
            "competition": "",
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
            "note": "Auto remplissage local utilisé."
        }

    try:
        home_team_id = find_team_id_by_name(home_team)
        away_team_id = find_team_id_by_name(away_team)

        if not home_team_id or not away_team_id:
            return {
                "sport": sport,
                "status": status,
                "home_team": home_team,
                "away_team": away_team,
                "match_date": match_date,
                "competition": "",
                "home_form": 72,
                "away_form": 63,
                "home_history": 68,
                "away_history": 59,
                "home_possession": 54,
                "away_possession": 46,
                "home_shots": 6,
                "away_shots": 4,
                "home_corners": 5,
                "away_corners": 3,
                "note": f"API active mais équipe non trouvée exactement pour {home_team} vs {away_team}. Estimation intelligente utilisée."
            }

        home_matches = fetch_team_matches(home_team_id, limit=8)
        away_matches = fetch_team_matches(away_team_id, limit=8)

        home_form = team_form_score(home_matches, home_team)
        away_form = team_form_score(away_matches, away_team)
        home_history, away_history = estimate_history_score(home_form, away_form)
        home_possession, away_possession = estimate_possession(home_form, away_form)
        home_avg_goals = average_goals_scored(home_matches, home_team)
        away_avg_goals = average_goals_scored(away_matches, away_team)
        home_shots, away_shots, home_corners, away_corners = estimate_shots_and_corners(
            sport, home_avg_goals, away_avg_goals, home_form, away_form
        )

        return {
            "sport": sport,
            "status": status,
            "home_team": home_team,
            "away_team": away_team,
            "match_date": match_date,
            "competition": "football-data.org",
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
            "note": f"Auto remplissage API pour {home_team} vs {away_team}."
        }
    except Exception as e:
        return {
            "sport": sport,
            "status": status,
            "home_team": home_team,
            "away_team": away_team,
            "match_date": match_date,
            "competition": "",
            "home_form": 70,
            "away_form": 60,
            "home_history": 66,
            "away_history": 56,
            "home_possession": 53,
            "away_possession": 47,
            "home_shots": 5,
            "away_shots": 4,
            "home_corners": 4,
            "away_corners": 3,
            "note": f"Fallback utilisé après erreur API: {str(e)}"
        }

# -----------------------------
# Analysis
# -----------------------------
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
        bonus_weight = 2
        draw_base = 28
    elif sport == "basketball":
        score_weight = 1.3
        shots_weight = 1.8
        bonus_weight = 0.2
        draw_base = 3
    else:
        score_weight = 15
        shots_weight = 2.0
        bonus_weight = 0.0
        draw_base = 1

    home_power = (
        home_score * score_weight
        + home_half * (score_weight * 0.6)
        + home_shots * shots_weight
        + home_corners * bonus_weight
        + home_possession * 0.35
        + home_form * 0.45
        + home_history * 0.30
    )
    away_power = (
        away_score * score_weight
        + away_half * (score_weight * 0.6)
        + away_shots * shots_weight
        + away_corners * bonus_weight
        + away_possession * 0.35
        + away_form * 0.45
        + away_history * 0.30
    )

    gap = abs(home_power - away_power)
    confidence = clamp(round(52 + gap * 0.7), 50, 95)

    home_raw = home_power + 8
    away_raw = away_power + 8
    draw_factor = draw_base + max(0, 18 - int(gap // 2))

    home_win_pct, draw_pct, away_win_pct = normalize_percentages(home_raw, draw_factor, away_raw)

    if sport in ["tennis", "table_tennis"]:
        likely_score = f"{max(home_score, away_score)}-{min(home_score, away_score)}"
    else:
        likely_score = f"{home_score}-{away_score}"

    attack_index = round((home_shots + away_shots + total_score + home_corners + away_corners) / 2)

    if winner == "Nul":
        summary = "Analyse post-match : rencontre équilibrée."
    else:
        side = "domicile" if winner == match.get("home_team") else "extérieur"
        summary = f"Analyse post-match : avantage confirmé du côté {side}."

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

    gap = abs(home_power - away_power)
    confidence = clamp(round(50 + gap * 1.1), 50, 92)

    draw_base = 24 if sport == "football" else 3
    draw_factor = draw_base + max(4, 18 - int(gap))
    home_win_pct, draw_pct, away_win_pct = normalize_percentages(home_power, draw_factor, away_power)

    if home_power > away_power:
        winner = match.get("home_team", "Domicile")
        half_winner = match.get("home_team", "Domicile")
    elif away_power > home_power:
        winner = match.get("away_team", "Extérieur")
        half_winner = match.get("away_team", "Extérieur")
    else:
        winner = "Nul"
        half_winner = "Nul"

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
        likely_score = "102-96" if winner == match.get("home_team") else "96-102"
        btts = True
        over_2_5 = True
    else:
        likely_score = "2-0" if winner == match.get("home_team") else "0-2"
        btts = False
        over_2_5 = False

    attack_index = round((home_shots + away_shots + home_corners + away_corners) / 2)
    risk_badge = get_risk_badge(confidence)

    if winner == "Nul":
        summary = "Pronostic pré-match équilibré."
    else:
        side = "domicile" if winner == match.get("home_team") else "extérieur"
        summary = f"Pronostic pré-match avec avantage {side}."

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
    return analyze_finished_match(match) if match.get("status") == "finished" else analyze_upcoming_match(match)


# -----------------------------
# Normalization
# -----------------------------
def normalize_match(data, existing_id=None, created_at=None):
    match = {
        "id": existing_id or str(uuid4()),
        "sport": data.get("sport", "football"),
        "status": data.get("status", "upcoming"),
        "competition": (data.get("competition") or "").strip(),
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
        "created_at": created_at or now_iso(),
    }
    match["analysis"] = analyze_match(match)
    return match


# -----------------------------
# Routes
# -----------------------------
@app.route("/")
def home():
    return jsonify({
        "message": "BetAI V5 Analytics API",
        "status": "ok",
        "football_api_enabled": bool(FOOTBALL_API_KEY)
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
            updated = normalize_match(data, existing_id=match_id, created_at=existing.get("created_at"))
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
            imported.append(normalize_match(item, created_at=item.get("created_at")))

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


@app.route("/real-matches/football", methods=["GET"])
def real_football_matches():
    limit = safe_int(request.args.get("limit"), 20)
    limit = clamp(limit, 1, 50)
    data = fetch_real_football_matches(limit=limit)

    if not data:
        return jsonify({
            "success": False,
            "error": "Impossible de récupérer les matchs réels football"
        }), 400

    return jsonify({
        "success": True,
        "count": len(data),
        "matches": data
    })


@app.route("/real-matches/football/import", methods=["POST"])
def import_real_football_matches():
    global matches_db

    limit = safe_int(request.args.get("limit"), 20)
    limit = clamp(limit, 1, 50)

    data = fetch_real_football_matches(limit=limit)
    if not data:
        return jsonify({
            "success": False,
            "error": "Impossible de récupérer les matchs réels football"
        }), 400

    normalized = [normalize_match(item) for item in data]
    matches_db = normalized + matches_db

    return jsonify({
        "success": True,
        "count": len(normalized),
        "total": len(matches_db)
    })


@app.route("/dashboard", methods=["GET"])
def dashboard():
    upcoming = [m for m in matches_db if m.get("status") == "upcoming"]
    finished = [m for m in matches_db if m.get("status") == "finished"]
    safe = [m for m in matches_db if (m.get("analysis") or {}).get("risk_badge") == "SAFE"]

    avg_conf = 0
    if matches_db:
        avg_conf = round(sum((m.get("analysis") or {}).get("confidence", 0) for m in matches_db) / len(matches_db))

    top_predictions = sorted(
        upcoming,
        key=lambda m: (m.get("analysis") or {}).get("confidence", 0),
        reverse=True,
    )[:5]

    return jsonify({
        "total_matches": len(matches_db),
        "upcoming_count": len(upcoming),
        "finished_count": len(finished),
        "safe_count": len(safe),
        "avg_confidence": avg_conf,
        "top_predictions": top_predictions,
    })


@app.route("/seed-demo", methods=["POST"])
def seed_demo():
    global matches_db
    demo = [
        {
            "sport": "football",
            "status": "upcoming",
            "competition": "LaLiga",
            "home_team": "Real Madrid",
            "away_team": "Sevilla FC",
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
            "note": "Pronostic pré-match avec avantage domicile.",
        },
        {
            "sport": "football",
            "status": "finished",
            "competition": "Ligue 1",
            "home_team": "PSG",
            "away_team": "Lyon",
            "home_score": 2,
            "away_score": 1,
            "match_date": "2026-04-06",
            "home_half_score": 1,
            "away_half_score": 0,
            "home_possession": 56,
            "away_possession": 44,
            "home_shots": 6,
            "away_shots": 4,
            "home_corners": 5,
            "away_corners": 3,
            "home_form": 84,
            "away_form": 72,
            "home_history": 80,
            "away_history": 67,
            "note": "Analyse post-match du favori.",
        },
    ]
    matches_db = [normalize_match(item) for item in demo]
    return jsonify({"success": True, "count": len(matches_db)})


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)