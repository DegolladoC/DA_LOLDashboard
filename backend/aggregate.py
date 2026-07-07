def summarize_matches(matches: list[dict], puuid: str) -> dict:
    if not matches:
        return {
            "total_games": 0,
            "wins": 0,
            "losses": 0,
            "winrate": 0.0,
            "avg_kda": 0.0,
            "avg_cs_per_min": 0.0,
            "avg_game_duration_min": 0.0,
        }

    wins = 0
    total_kills = total_deaths = total_assists = 0
    total_cs = 0
    total_duration_sec = 0

    for match in matches:
        participant = next(p for p in match["info"]["participants"] if p["puuid"] == puuid)
        if participant["win"]:
            wins += 1
        total_kills += participant["kills"]
        total_deaths += participant["deaths"]
        total_assists += participant["assists"]
        total_cs += participant["totalMinionsKilled"] + participant["neutralMinionsKilled"]
        total_duration_sec += match["info"]["gameDuration"]

    total_games = len(matches)
    total_duration_min = total_duration_sec / 60

    return {
        "total_games": total_games,
        "wins": wins,
        "losses": total_games - wins,
        "winrate": round(wins / total_games * 100, 1),
        "avg_kda": round((total_kills + total_assists) / max(total_deaths, 1), 2),
        "avg_cs_per_min": round(total_cs / total_duration_min, 2),
        "avg_game_duration_min": round(total_duration_min / total_games, 1),
    }
