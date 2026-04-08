from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from uuid import uuid4
from datetime import datetime
import os

from analyzer import analyze_match
from image_parser import save_uploaded_image, ensure_upload_folder
from storage import load_matches, save_matches

app = Flask(__name__)

CORS(
    app,
    resources={
        r"/*": {
            "origins": [
                "https://betai-pro.netlify.app",
                "http://localhost:3000",
                "http://127.0.0.1:3000"
            ]
        }
    }
)

UPLOAD_FOLDER = "uploads"
ensure_upload_folder()

matches_db = load_matches()


@app.after_request
def after_request(response):
    response.headers["Access-Control-Allow-Origin"] = "https://betai-pro.netlify.app"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type,Authorization"
    response.headers["Access-Control-Allow-Methods"] = "GET,POST,PUT,DELETE,OPTIONS"
    return response


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
        "note": f"Auto remplissage intelligent V6 pour {home_team} vs {away_team}."
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
    match["analysis"] = analyze_match(match)
    return match


@app.route("/")
def home():
    return jsonify({
        "message": "BetAI V6 Hybrid API",
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
    match = normalize_match(data)
    return jsonify({
        "success": True,
        "match": match
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
            "status": "upcoming",
            "competition": "LaLiga",
            "home_team": "Real Madrid",
            "away_team": "Sevilla FC",
            "home_score": 0,
            "away_score": 0,
            "match_date": "2026-04-12",
            "home_half_score": 0,
            "away_half_score": 0,
            "home_possession": 56,
            "away_possession": 44,
            "home_shots": 7,
            "away_shots": 3,
            "home_corners": 6,
            "away_corners": 2,
            "home_form": 88,
            "away_form": 61,
            "home_history": 84,
            "away_history": 58,
            "note": "Démo football."
        },
        {
            "sport": "basketball",
            "status": "upcoming",
            "competition": "NBA",
            "home_team": "Lakers",
            "away_team": "Celtics",
            "home_score": 0,
            "away_score": 0,
            "match_date": "2026-04-15",
            "home_shots": 22,
            "away_shots": 20,
            "home_form": 79,
            "away_form": 74,
            "home_history": 75,
            "away_history": 72,
            "note": "Démo basket."
        },
        {
            "sport": "tennis",
            "status": "upcoming",
            "competition": "ATP",
            "home_team": "Player A",
            "away_team": "Player B",
            "home_score": 0,
            "away_score": 0,
            "match_date": "2026-04-17",
            "home_form": 82,
            "away_form": 71,
            "home_history": 76,
            "away_history": 66,
            "note": "Démo tennis."
        },
        {
            "sport": "table_tennis",
            "status": "upcoming",
            "competition": "TT Elite",
            "home_team": "Pong A",
            "away_team": "Pong B",
            "home_score": 0,
            "away_score": 0,
            "match_date": "2026-04-18",
            "home_form": 80,
            "away_form": 68,
            "home_history": 75,
            "away_history": 64,
            "note": "Démo tennis de table."
        }
    ]

    matches_db = [normalize_match(item) for item in demo]
    save_matches(matches_db)

    return jsonify({"success": True, "count": len(matches_db)})


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)