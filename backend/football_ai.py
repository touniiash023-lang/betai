def football_prediction(stats):

    attack = stats["goals_for"] * 0.4
    defense = stats["goals_against"] * 0.3
    form = stats["form"] * 0.2
    xg = stats["xg"] * 0.1

    score = attack + form + xg - defense

    home = max(min(50 + score * 10, 85), 15)
    draw = 100 - home - 20
    away = 100 - home - draw

    return {
        "1X2": {"home": int(home), "draw": int(draw), "away": int(away)},
        "over25": int((stats["goals_for"] + stats["goals_against"]) * 20),
        "btts": int(min(stats["goals_for"], stats["goals_against"]) * 35),
        "score": f"{round(stats['goals_for'])}-{round(stats['goals_against'])}",
        "confidence": "HIGH" if home > 65 else "MEDIUM"
    }