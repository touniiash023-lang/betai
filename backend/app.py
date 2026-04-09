from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from uuid import uuid4
from datetime import datetime
import os

from analyzer import analyze_match_with_history
from image_parser import save_uploaded_image, ensure_upload_folder
from storage import load_matches, save_matches
from history_engine import get_entity_history, get_h2h_history, get_recent_history
from profile_engine import build_profile_for_sport

app = Flask(__name__)

CORS(app)

UPLOAD_FOLDER = "uploads"
ensure_upload_folder()

matches_db = load_matches()


def safe_int(value, default=0):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def clamp(value, low, high):
    return max(low, min(high, value))


def now_iso():
    return datetime.utcnow().isoformat()


def smart_autofill(data):
    sport = (data.get("sport") or "football").strip()
    home_team = (data.get("home_team") or "").strip()
    away_team = (data.get("away_team") or "").strip()
    match_date = (data.get("match_date") or "").strip()
    status = (data.get("status") or "upcoming").strip()

    base_home = 70 + (len(home_team) % 15)
    base_away = 60 + (len(away_team) % 13)

    home_form = clamp(base_home, 40, 94)
    away_form = clamp(base_away, 35, 90)
    hist_home = get_recent_history(matches_db, sport, home_team, limit=10)
    hist_away = get_recent_history(matches_db, sport, away_team, limit=10)

    if hist_home:
        home_profile = build_profile_for_sport(sport, hist_home, home_team)
        home_form = home_profile.get("form_score", home_form)
    if hist_away:
        away_profile = build_profile_for_sport(sport, hist_away, away_team)
        away_form = away_profile.get("form_score", away_form)

    home_history = clamp(home_form - 4, 30, 95)
    away_history = clamp(away_form - 4, 30, 92)

    if sport == "football":
        home_possession, away_possession = 54, 46
        home_shots, away_shots = 6, 4
        home_corners, away_corners = 5, 3
    elif sport == "basketball":
        home_possession, away_possession = 50, 50
        home_shots, away_shots = 22, 19
        home_corners, away_corners = 0, 0
    elif sport == "tennis":
        home_possession, away_possession = 50, 50
        home_shots, away_shots = 10, 8
        home_corners, away_corners = 0, 0
    else:
        home_possession, away_possession = 50, 50
        home_shots, away_shots = 8, 7
        home_corners, away_corners = 0, 0

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
        "note": f"Auto remplissage V7 avec prise en compte de l'historique disponible."
    }


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

    analysis_bundle = analyze_match_with_history(match, matches_db)
    match["analysis"] = analysis_bundle["analysis"]
    return match


@app.route("/")
def home():
    return jsonify({
        "message": "BetAI V7 History API",
        "status": "ok"
    })


@app.route("/uploads/<path:filename>")
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)


@app.route("/matches", methods=["GET"])
def get_matches():
    return jsonify(matches_db)


@app.route("/matches", methods=["POST"])
def create_match():
    global matches_db
    data = request.get_json(force=True)
    match = normalize_match(data)
    matches_db.insert(0, match)
    save_matches(matches_db)
    return jsonify(match), 201


@app.route("/matches/<match_id>", methods=["PUT"])
def update_match(match_id):
    global matches_db
    data = request.get_json(force=True)

    for index, existing in enumerate(matches_db):
        if existing["id"] == match_id:
            updated = normalize_match(data, existing_id=match_id, created_at=existing.get("created_at"))
            matches_db[index] = updated
            save_matches(matches_db)
            return jsonify(updated)

    return jsonify({"error": "Match introuvable"}), 404


@app.route("/matches/<match_id>", methods=["DELETE"])
def delete_match(match_id):
    global matches_db
    before = len(matches_db)
    matches_db = [m for m in matches_db if m["id"] != match_id]

    if len(matches_db) == before:
        return jsonify({"error": "Match introuvable"}), 404

    save_matches(matches_db)
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
    save_matches(matches_db)
    return jsonify({"success": True, "count": len(matches_db)})


@app.route("/matches/autofill", methods=["POST"])
def autofill_match():
    data = request.get_json(force=True)
    home_team = (data.get("home_team") or "").strip()
    away_team = (data.get("away_team") or "").strip()

    if not home_team or not away_team:
        return jsonify({"error": "Équipes / joueurs manquants"}), 400

    return jsonify(smart_autofill(data))


@app.route("/matches/analyze", methods=["POST"])
def analyze_custom_match():
    data = request.get_json(force=True)
    temp_match = normalize_match(data)
    return jsonify({
        "success": True,
        "match": temp_match
    })


@app.route("/matches/import-image", methods=["POST"])
def import_image():
    file = request.files.get("image")
    saved, error = save_uploaded_image(file)

    if error:
        return jsonify({"error": error}), 400

    return jsonify({
        "success": True,
        "image": saved
    })


@app.route("/history/entity", methods=["GET"])
def entity_history():
    sport = request.args.get("sport", "")
    name = request.args.get("name", "")

    if not sport or not name:
        return jsonify({"error": "sport et name requis"}), 400

    history = get_entity_history(matches_db, sport, name)
    return jsonify({
        "sport": sport,
        "name": name,
        "count": len(history),
        "matches": history
    })


@app.route("/history/h2h", methods=["GET"])
def history_h2h():
    sport = request.args.get("sport", "")
    a = request.args.get("a", "")
    b = request.args.get("b", "")

    if not sport or not a or not b:
        return jsonify({"error": "sport, a et b requis"}), 400

    history = get_h2h_history(matches_db, sport, a, b, limit=20)
    return jsonify({
        "sport": sport,
        "a": a,
        "b": b,
        "count": len(history),
        "matches": history
    })


@app.route("/profiles/entity", methods=["GET"])
def entity_profile():
    sport = request.args.get("sport", "")
    name = request.args.get("name", "")

    if not sport or not name:
        return jsonify({"error": "sport et name requis"}), 400

    history = get_recent_history(matches_db, sport, name, limit=20)
    profile = build_profile_for_sport(sport, history, name)

    return jsonify({
        "sport": sport,
        "name": name,
        "profile": profile
    })


@app.route("/predict-with-history", methods=["POST"])
def predict_with_history():
    data = request.get_json(force=True)

    home_team = (data.get("home_team") or "").strip()
    away_team = (data.get("away_team") or "").strip()
    sport = (data.get("sport") or "").strip()

    if not sport or not home_team or not away_team:
        return jsonify({"error": "sport, home_team et away_team requis"}), 400

    match = {
        "id": str(uuid4()),
        "sport": sport,
        "status": "upcoming",
        "competition": (data.get("competition") or "").strip(),
        "home_team": home_team,
        "away_team": away_team,
        "home_score": 0,
        "away_score": 0,
        "match_date": (data.get("match_date") or "").strip(),
        "home_half_score": 0,
        "away_half_score": 0,
        "home_possession": safe_int(data.get("home_possession"), 50),
        "away_possession": safe_int(data.get("away_possession"), 50),
        "home_shots": safe_int(data.get("home_shots"), 0),
        "away_shots": safe_int(data.get("away_shots"), 0),
        "home_corners": safe_int(data.get("home_corners"), 0),
        "away_corners": safe_int(data.get("away_corners"), 0),
        "home_form": safe_int(data.get("home_form"), 50),
        "away_form": safe_int(data.get("away_form"), 50),
        "home_history": safe_int(data.get("home_history"), 50),
        "away_history": safe_int(data.get("away_history"), 50),
        "image_url": (data.get("image_url") or "").strip(),
        "note": (data.get("note") or "").strip(),
        "created_at": now_iso(),
    }

    bundle = analyze_match_with_history(match, matches_db)

    return jsonify({
        "success": True,
        "match": match,
        "analysis": bundle["analysis"],
        "home_profile": bundle["home_profile"],
        "away_profile": bundle["away_profile"],
        "h2h_count": bundle["h2h_count"]
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
        matches_db,
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
            "status": "finished",
            "competition": "Ligue 1",
            "home_team": "PSG",
            "away_team": "Lyon",
            "home_score": 2,
            "away_score": 1,
            "match_date": "2026-04-01",
            "home_half_score": 1,
            "away_half_score": 0,
            "home_possession": 57,
            "away_possession": 43,
            "home_shots": 7,
            "away_shots": 4,
            "home_corners": 6,
            "away_corners": 3,
            "note": "Historique PSG"
        },
        {
            "sport": "football",
            "status": "finished",
            "competition": "Premier League",
            "home_team": "Liverpool",
            "away_team": "Chelsea",
            "home_score": 3,
            "away_score": 1,
            "match_date": "2026-04-02",
            "home_half_score": 2,
            "away_half_score": 0,
            "home_possession": 59,
            "away_possession": 41,
            "home_shots": 8,
            "away_shots": 4,
            "home_corners": 5,
            "away_corners": 2,
            "note": "Historique Liverpool"
        },
        {
            "sport": "football",
            "status": "upcoming",
            "competition": "Champions League",
            "home_team": "PSG",
            "away_team": "Liverpool",
            "home_score": 0,
            "away_score": 0,
            "match_date": "2026-04-20",
            "note": "Match futur"
        },
        {
            "sport": "tennis",
            "status": "finished",
            "competition": "ATP",
            "home_team": "Player A",
            "away_team": "Player C",
            "home_score": 2,
            "away_score": 0,
            "match_date": "2026-04-03",
            "note": "Historique tennis"
        },
        {
            "sport": "tennis",
            "status": "finished",
            "competition": "ATP",
            "home_team": "Player B",
            "away_team": "Player D",
            "home_score": 2,
            "away_score": 1,
            "match_date": "2026-04-04",
            "note": "Historique tennis"
        },
        {
            "sport": "basketball",
            "status": "finished",
            "competition": "NBA",
            "home_team": "Lakers",
            "away_team": "Bulls",
            "home_score": 108,
            "away_score": 99,
            "match_date": "2026-04-05",
            "note": "Historique basket"
        },
        {
            "sport": "basketball",
            "status": "finished",
            "competition": "NBA",
            "home_team": "Celtics",
            "away_team": "Heat",
            "home_score": 111,
            "away_score": 103,
            "match_date": "2026-04-06",
            "note": "Historique basket"
        },
        {
            "sport": "table_tennis",
            "status": "finished",
            "competition": "TT Cup",
            "home_team": "Pong A",
            "away_team": "Pong C",
            "home_score": 3,
            "away_score": 1,
            "match_date": "2026-04-07",
            "note": "Historique tennis de table"
        }
    ]

    matches_db = []
    for item in demo:
        normalized = normalize_match(item)
        matches_db.append(normalized)

    save_matches(matches_db)
    return jsonify({"success": True, "count": len(matches_db)})


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)