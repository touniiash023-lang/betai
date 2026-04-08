import os
import requests
from typing import Dict, List, Optional

FOOTBALL_API_KEY = os.getenv("FOOTBALL_API_KEY", "").strip()
FOOTBALL_BASE_URL = "https://api.football-data.org/v4"

REQUEST_TIMEOUT = 20


def football_headers() -> Dict[str, str]:
    if not FOOTBALL_API_KEY:
        raise RuntimeError("FOOTBALL_API_KEY manquante")
    return {"X-Auth-Token": FOOTBALL_API_KEY}


def football_api_get(path: str, params: Optional[Dict] = None) -> Optional[Dict]:
    """
    Appel générique vers football-data.org
    """
    try:
        response = requests.get(
            f"{FOOTBALL_BASE_URL}{path}",
            headers=football_headers(),
            params=params or {},
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        return response.json()
    except requests.RequestException:
        return None


def get_live_or_scheduled_matches(limit: int = 20) -> List[Dict]:
    """
    Récupère les matchs du jour.
    """
    data = football_api_get("/matches")
    if not data:
        return []

    matches = []
    for match in data.get("matches", [])[:limit]:
        matches.append({
            "source": "football-data.org",
            "sport": "football",
            "match_id": match.get("id"),
            "competition": (match.get("competition") or {}).get("name", ""),
            "home_team": (match.get("homeTeam") or {}).get("name", ""),
            "away_team": (match.get("awayTeam") or {}).get("name", ""),
            "match_date": match.get("utcDate", ""),
            "status": match.get("status", ""),
            "home_score": ((match.get("score") or {}).get("fullTime") or {}).get("home"),
            "away_score": ((match.get("score") or {}).get("fullTime") or {}).get("away"),
        })
    return matches


def search_team(team_name: str) -> Optional[Dict]:
    """
    Cherche une équipe par nom exact ou partiel.
    """
    if not team_name.strip():
        return None

    data = football_api_get("/teams", params={"limit": 500})
    if not data:
        return None

    target = team_name.strip().lower()
    exact = None
    partial = None

    for team in data.get("teams", []):
        name = (team.get("name") or "").lower()
        short_name = (team.get("shortName") or "").lower()
        tla = (team.get("tla") or "").lower()

        if target in {name, short_name, tla}:
            exact = team
            break

        if target in name or target in short_name:
            partial = team

    return exact or partial


def get_team_matches(team_name: str, limit: int = 8) -> List[Dict]:
    """
    Récupère les derniers matchs terminés d'une équipe.
    """
    team = search_team(team_name)
    if not team:
        return []

    team_id = team.get("id")
    if not team_id:
        return []

    data = football_api_get(
        f"/teams/{team_id}/matches",
        params={"status": "FINISHED", "limit": limit}
    )
    if not data:
        return []

    return data.get("matches", [])


def compute_form_from_matches(matches: List[Dict], team_name: str) -> int:
    """
    Retourne une forme entre 0 et 100 à partir des 5 derniers matchs.
    """
    if not matches:
        return 50

    points = 0
    max_points = 0
    target = team_name.strip().lower()

    for match in matches[:5]:
        home_name = ((match.get("homeTeam") or {}).get("name") or "").lower()
        away_name = ((match.get("awayTeam") or {}).get("name") or "").lower()

        full_time = (match.get("score") or {}).get("fullTime") or {}
        home_score = full_time.get("home")
        away_score = full_time.get("away")

        if home_score is None or away_score is None:
            continue

        if target == home_name:
            if home_score > away_score:
                points += 3
            elif home_score == away_score:
                points += 1
            max_points += 3

        elif target == away_name:
            if away_score > home_score:
                points += 3
            elif away_score == home_score:
                points += 1
            max_points += 3

    if max_points == 0:
        return 50

    return round((points / max_points) * 100)


def compute_avg_goals(matches: List[Dict], team_name: str) -> float:
    """
    Moyenne de buts marqués sur les derniers matchs.
    """
    if not matches:
        return 1.0

    target = team_name.strip().lower()
    goals = []

    for match in matches[:5]:
        home_name = ((match.get("homeTeam") or {}).get("name") or "").lower()
        away_name = ((match.get("awayTeam") or {}).get("name") or "").lower()

        full_time = (match.get("score") or {}).get("fullTime") or {}
        home_score = full_time.get("home")
        away_score = full_time.get("away")

        if home_score is None or away_score is None:
            continue

        if target == home_name:
            goals.append(home_score)
        elif target == away_name:
            goals.append(away_score)

    if not goals:
        return 1.0

    return round(sum(goals) / len(goals), 2)


def get_autofill_data(home_team: str, away_team: str, match_date: str = "") -> Dict:
    """
    Prépare les données pour votre bouton Auto remplir.
    """
    home_matches = get_team_matches(home_team, limit=8)
    away_matches = get_team_matches(away_team, limit=8)

    home_form = compute_form_from_matches(home_matches, home_team)
    away_form = compute_form_from_matches(away_matches, away_team)

    home_avg_goals = compute_avg_goals(home_matches, home_team)
    away_avg_goals = compute_avg_goals(away_matches, away_team)

    home_history = max(30, min(95, home_form - 4))
    away_history = max(30, min(92, away_form - 4))

    home_possession = max(38, min(67, 50 + round((home_form - away_form) / 2.5)))
    away_possession = 100 - home_possession

    home_shots = max(3, min(10, round(4 + home_avg_goals * 2 + (home_form - away_form) / 12)))
    away_shots = max(2, min(8, round(3 + away_avg_goals * 2 - (home_form - away_form) / 18)))

    home_corners = max(2, min(9, round(3 + home_avg_goals * 1.5 + (home_form - away_form) / 20)))
    away_corners = max(1, min(7, round(2 + away_avg_goals * 1.3 - (home_form - away_form) / 25)))

    return {
        "sport": "football",
        "competition": "football-data.org",
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
        "note": (
            f"Auto remplissage API football : {home_team} forme {home_form}/100, "
            f"{away_team} forme {away_form}/100."
        ),
    }


if __name__ == "__main__":
    try:
        matches = get_live_or_scheduled_matches(limit=10)
        print(matches)
    except Exception as e:
        print({"error": str(e)})



