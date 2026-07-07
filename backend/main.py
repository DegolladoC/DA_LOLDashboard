from contextlib import asynccontextmanager
from datetime import datetime, timezone

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

import aggregate
import cache
import riot_client


@asynccontextmanager
async def lifespan(app: FastAPI):
    cache.init_db()
    yield


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["GET"],
    allow_headers=["*"],
)


@app.get("/api/player/{game_name}/{tag_line}")
async def get_player(game_name: str, tag_line: str):
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            account = await riot_client.get_account_by_riot_id(client, game_name, tag_line)
            summoner = await riot_client.get_summoner_by_puuid(client, account["puuid"])

        matches = await riot_client.get_recent_matches(account["puuid"], count=10)
    except httpx.HTTPStatusError as exc:
        status = exc.response.status_code
        if status in (401, 403):
            raise HTTPException(
                status_code=502,
                detail="La Riot API key parece inválida o caducada (caduca cada 24h). Regenérala en developer.riotgames.com.",
            )
        if status == 404:
            raise HTTPException(status_code=404, detail="Riot ID no encontrado")
        raise HTTPException(status_code=502, detail=f"Riot API respondió {status}")

    summary = aggregate.summarize_matches(matches, account["puuid"])

    revision_date = datetime.fromtimestamp(
        summoner["revisionDate"] / 1000, tz=timezone.utc
    ).isoformat()

    return {
        "riotId": f"{account['gameName']}#{account['tagLine']}",
        "puuid": account["puuid"],
        "profileIconId": summoner["profileIconId"],
        "summonerLevel": summoner["summonerLevel"],
        "lastUpdated": revision_date,
        "summary": summary,
    }
