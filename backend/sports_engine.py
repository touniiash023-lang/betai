from typing import Dict


def clamp(value, low, high):
    return max(low, min(high, value))


def normalize_2way(home_raw, away_raw):
    total = home_raw + away_raw
    if total <= 0:
        return 50, 50

    home_pct = round((home_raw / total) * 100)
    away_pct = 100 - home_pct
    return home_pct, away_pct


def normalize_3way(home_raw, draw_raw, away_raw):
    total = home_raw + draw_raw + away_raw
    if total <= 0:
        return 33, 34, 33

    home_pct = round((home_raw / total) * 100)
    draw_pct = round((draw_raw / total) * 100)
    away_pct = 100 - home_pct - draw_pct
    return home_pct, draw_pct, away_pct


def risk_badge(confidence):
    if confidence >= 78:
        return "SAFE"
    if confidence >= 62:
        return "MEDIUM"
    return "RISKY"


def analyze_football(match: Dict):
    home_form = int(match.get("home_form", 50))
    away_form = int(match.get("away_form", 50))
    home_history = int(match.get("home_history", 50))
    away_history = int(match.get("away_history", 50))
    home_possession = int(match.get("home_possession", 50))
    away_possession = int(match.get("away_possession", 50))
    home_shots = int(match.get("home_shots", 0))
    away_shots = int(match.get("away_shots", 0))
    home_corners = int(match.get("home_corners", 0))
    away_corners = int(match.get("away_corners", 0))

    home_power = (
        home_form * 0.30 +
        home_history * 0.22 +
        home_possession * 0.14 +
        home_shots * 2.0 +
        home_corners * 1.0 +
        6
    )
    away_power = (
        away_form * 0.30 +
        away_history * 0.22 +
        away_possession * 0.14 +
        away_shots * 2.0 +
        away_corners * 1.0
    )

    gap = abs(home_power - away_power)
    confidence = clamp(round(50 + gap * 1.1), 50, 93)

    draw_raw = 24 + max(4, 18 - int(gap))
    home_pct, draw_pct, away_pct = normalize_3way(home_power, draw_raw, away_power)

    if home_power > away_power:
        winner = match.get("home_team", "Domicile")
        likely_score = "2-1" if confidence < 75 else "2-0"
    elif away_power > home_power:
        winner = match.get("away_team", "Extérieur")
        likely_score = "1-2" if confidence < 75 else "0-2"
    else:
        winner = "Nul"
        likely_score = "1-1"

    btts = likely_score in ["1-1", "2-1", "1-2", "2-2"]
    over_2_5 = likely_score in ["2-1", "1-2", "2-2", "3-1", "1-3"]

    return {
        "winner": winner,
        "half_winner": winner if winner != "Nul" else "Nul",
        "home_win_pct": home_pct,
        "draw_pct": draw_pct,
        "away_win_pct": away_pct,
        "likely_score": likely_score,
        "btts": btts,
        "over_2_5": over_2_5,
        "confidence": confidence,
        "risk_badge": risk_badge(confidence),
        "attack_index": round((home_shots + away_shots + home_corners + away_corners) / 2),
        "summary": f"Analyse football : avantage {'domicile' if winner == match.get('home_team') else 'extérieur' if winner == match.get('away_team') else 'équilibré'}."
    }


def analyze_basketball(match: Dict):
    home_form = int(match.get("home_form", 50))
    away_form = int(match.get("away_form", 50))
    home_history = int(match.get("home_history", 50))
    away_history = int(match.get("away_history", 50))
    home_shots = int(match.get("home_shots", 0))
    away_shots = int(match.get("away_shots", 0))

    home_power = home_form * 0.34 + home_history * 0.22 + home_shots * 1.8 + 4
    away_power = away_form * 0.34 + away_history * 0.22 + away_shots * 1.8

    gap = abs(home_power - away_power)
    confidence = clamp(round(52 + gap * 1.05), 50, 94)
    home_pct, away_pct = normalize_2way(home_power, away_power)

    winner = match.get("home_team") if home_power >= away_power else match.get("away_team")
    likely_score = "102-96" if winner == match.get("home_team") else "96-102"

    return {
        "winner": winner,
        "half_winner": winner,
        "home_win_pct": home_pct,
        "draw_pct": 0,
        "away_win_pct": away_pct,
        "likely_score": likely_score,
        "btts": True,
        "over_2_5": True,
        "confidence": confidence,
        "risk_badge": risk_badge(confidence),
        "attack_index": round((home_shots + away_shots) / 2),
        "summary": "Analyse basketball : projection de vainqueur et total points."
    }


def analyze_tennis(match: Dict):
    home_form = int(match.get("home_form", 50))
    away_form = int(match.get("away_form", 50))
    home_history = int(match.get("home_history", 50))
    away_history = int(match.get("away_history", 50))
    home_score = int(match.get("home_score", 0))
    away_score = int(match.get("away_score", 0))

    home_power = home_form * 0.42 + home_history * 0.30 + home_score * 6 + 3
    away_power = away_form * 0.42 + away_history * 0.30 + away_score * 6

    gap = abs(home_power - away_power)
    confidence = clamp(round(53 + gap * 0.95), 50, 95)
    home_pct, away_pct = normalize_2way(home_power, away_power)

    winner = match.get("home_team") if home_power >= away_power else match.get("away_team")
    likely_score = "2-0" if confidence >= 72 else "2-1"

    return {
        "winner": winner,
        "half_winner": winner,
        "home_win_pct": home_pct,
        "draw_pct": 0,
        "away_win_pct": away_pct,
        "likely_score": likely_score,
        "btts": False,
        "over_2_5": False,
        "confidence": confidence,
        "risk_badge": risk_badge(confidence),
        "attack_index": round((home_form + away_form) / 20),
        "summary": "Analyse tennis : projection du vainqueur et du score en sets."
    }


def analyze_table_tennis(match: Dict):
    home_form = int(match.get("home_form", 50))
    away_form = int(match.get("away_form", 50))
    home_history = int(match.get("home_history", 50))
    away_history = int(match.get("away_history", 50))
    home_score = int(match.get("home_score", 0))
    away_score = int(match.get("away_score", 0))

    home_power = home_form * 0.45 + home_history * 0.32 + home_score * 5 + 2
    away_power = away_form * 0.45 + away_history * 0.32 + away_score * 5

    gap = abs(home_power - away_power)
    confidence = clamp(round(54 + gap * 0.9), 50, 95)
    home_pct, away_pct = normalize_2way(home_power, away_power)

    winner = match.get("home_team") if home_power >= away_power else match.get("away_team")
    likely_score = "3-1" if confidence >= 74 else "3-2"

    return {
        "winner": winner,
        "half_winner": winner,
        "home_win_pct": home_pct,
        "draw_pct": 0,
        "away_win_pct": away_pct,
        "likely_score": likely_score,
        "btts": False,
        "over_2_5": False,
        "confidence": confidence,
        "risk_badge": risk_badge(confidence),
        "attack_index": round((home_form + away_form) / 18),
        "summary": "Analyse tennis de table : projection du vainqueur et du score en sets."
    }