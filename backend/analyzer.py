from history_engine import get_recent_history, get_h2h_history
from profile_engine import build_profile_for_sport
from sports_engine import (
    predict_football_from_profiles,
    predict_virtual_football_from_profiles,
    predict_basketball_from_profiles,
    predict_tennis_from_profiles,
)


def analyze_match_with_history(match, all_matches):
    sport = (match.get("sport") or "football").strip()
    home_team = (match.get("home_team") or "").strip()
    away_team = (match.get("away_team") or "").strip()

    home_history = get_recent_history(all_matches, sport, home_team, limit=12)
    away_history = get_recent_history(all_matches, sport, away_team, limit=12)
    h2h = get_h2h_history(all_matches, sport, home_team, away_team, limit=8)

    home_profile = build_profile_for_sport(sport, home_history, home_team)
    away_profile = build_profile_for_sport(sport, away_history, away_team)

    if sport == "football":
        analysis = predict_football_from_profiles(home_profile, away_profile, h2h, match)
    elif sport == "virtual_football":
        analysis = predict_virtual_football_from_profiles(home_profile, away_profile, h2h, match)
    elif sport == "basketball":
        analysis = predict_basketball_from_profiles(home_profile, away_profile, h2h, match)
    elif sport == "tennis":
        analysis = predict_tennis_from_profiles(home_profile, away_profile, h2h, match, tt_mode=False)
    elif sport == "table_tennis":
        analysis = predict_tennis_from_profiles(home_profile, away_profile, h2h, match, tt_mode=True)
    else:
        analysis = predict_football_from_profiles(home_profile, away_profile, h2h, match)

    return {
        "analysis": analysis,
        "home_profile": home_profile,
        "away_profile": away_profile,
        "h2h_count": len(h2h),
    }

   