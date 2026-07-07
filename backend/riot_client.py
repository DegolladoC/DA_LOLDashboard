import asyncio
import os
import random
from urllib.parse import quote

import httpx
from dotenv import load_dotenv

import cache

load_dotenv()

RIOT_API_KEY = os.getenv("RIOT_API_KEY")
HEADERS = {"X-Riot-Token": RIOT_API_KEY}

PLATFORM_BASE = "https://la1.api.riotgames.com"
REGIONAL_BASE = "https://americas.api.riotgames.com"

MAX_RETRIES = 5
MATCH_DETAIL_CONCURRENCY = 5


async def _request(client: httpx.AsyncClient, url: str) -> dict:
    for attempt in range(MAX_RETRIES):
        response = await client.get(url, headers=HEADERS)
        if response.status_code == 429:
            retry_after = float(response.headers.get("Retry-After", 1))
            wait = retry_after + random.uniform(0, 1)
            await asyncio.sleep(wait)
            continue
        response.raise_for_status()
        return response.json()
    raise RuntimeError(f"Rate limit persistente tras {MAX_RETRIES} intentos: {url}")


async def get_account_by_riot_id(client: httpx.AsyncClient, game_name: str, tag_line: str) -> dict:
    url = f"{REGIONAL_BASE}/riot/account/v1/accounts/by-riot-id/{quote(game_name)}/{quote(tag_line)}"
    return await _request(client, url)


async def get_summoner_by_puuid(client: httpx.AsyncClient, puuid: str) -> dict:
    url = f"{PLATFORM_BASE}/lol/summoner/v4/summoners/by-puuid/{puuid}"
    return await _request(client, url)


async def get_match_ids(client: httpx.AsyncClient, puuid: str, count: int = 10) -> list[str]:
    url = f"{REGIONAL_BASE}/lol/match/v5/matches/by-puuid/{puuid}/ids?start=0&count={count}"
    return await _request(client, url)


async def get_match_detail(
    client: httpx.AsyncClient, match_id: str, puuid: str, semaphore: asyncio.Semaphore
) -> dict:
    cached = cache.get_cached_match(match_id)
    if cached is not None:
        return cached

    async with semaphore:
        url = f"{REGIONAL_BASE}/lol/match/v5/matches/{match_id}"
        data = await _request(client, url)

    cache.save_match(match_id, puuid, data)
    return data


async def get_recent_matches(puuid: str, count: int = 10) -> list[dict]:
    async with httpx.AsyncClient(timeout=10.0) as client:
        match_ids = await get_match_ids(client, puuid, count)
        semaphore = asyncio.Semaphore(MATCH_DETAIL_CONCURRENCY)
        tasks = [get_match_detail(client, match_id, puuid, semaphore) for match_id in match_ids]
        return await asyncio.gather(*tasks)
