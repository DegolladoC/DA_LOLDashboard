# CLAUDE.md — Dashboard de Datos de League of Legends

Instrucciones para Claude al trabajar en este repo.

## Contexto del proyecto

Dashboard web que consume la Riot Games API para analizar el historial de partidas de un jugador
de LoL y visualizar su rendimiento con gráficas que se actualizan por polling. Backend proxy
(protege la API key + cachea + maneja rate limits) + frontend React. Usuario: DDegollado, en
México (región LAN), con experiencia sólida en web dev; podría reusar esto como base de métricas
para su negocio SNAPP.

## Reglas críticas de la Riot API

- **La API key JAMÁS va en el frontend ni en el repo.** Vive en `backend/.env` como `RIOT_API_KEY`,
  ignorada por git. El frontend habla solo con nuestro backend, nunca con Riot directo.
- Autenticación: header `X-Riot-Token: <key>` en cada request a Riot (Data Dragon no la usa).
- Dev key **caduca cada 24 h**; el usuario la regenera manualmente. Si empiezan a salir 401/403,
  la causa más probable es key expirada — avisarle, no "arreglar" el código.
- **Ruteo doble** (no confundir):
  - Plataforma (SUMMONER-V4, LEAGUE-V4, SPECTATOR-V5): `la1` para México/LATAM Norte.
  - Regional (ACCOUNT-V1, MATCH-V5): `americas`.
- Flujo de entrada SIEMPRE: `ACCOUNT-V1 (Nombre#TAG → puuid)` → luego `SUMMONER-V4` y/o `MATCH-V5`
  con ese `puuid`. No existe atajo desde "summoner name"; el Riot ID es `gameName#tagLine`.
- MATCH-V5 da primero una lista de **match IDs**; el detalle de cada partida es una request aparte.

## Rate limiting (obligatorio manejarlo)

- Dev key: ~20 req/s y ~100 req/2min (los valores reales llegan en headers `X-App-Rate-Limit*`;
  son dinámicos). Leer esos headers y respetarlos.
- **Cachear todo lo inmutable:** una partida terminada nunca cambia → guardar su detalle y no
  volver a pedirlo. Caché en **SQLite** (`backend/cache.db`, tabla `matches` por `match_id`);
  Redis solo si de verdad escala. Elección deliberada (no solo "para empezar simple"): el usuario
  la está usando como proyecto de aprendizaje de SQL, así que el desarrollo de `cache.py` va
  guiado paso a paso con él en vez de generarse de un jalón — ver sección "Proceso de desarrollo".
- **Paginar:** traer 5–10 partidas por lote, no 50 de golpe.
- Ante **429**: exponential backoff con jitter y reintento; nunca reintentar en bucle inmediato.
- No hacer las requests de detalle en un `for` secuencial sin límite: agrupar con control de
  concurrencia (semáforo) respetando el rate limit.

## Arquitectura

```
backend/
  main.py            # FastAPI: expone endpoints propios al frontend
  riot_client.py     # cliente httpx hacia Riot: routing, headers, backoff
  cache.py           # caché de partidas en SQLite (tabla matches, por match_id)
  cache.db           # base SQLite (git-ignored, se regenera sola)
  aggregate.py       # transforma partidas crudas -> métricas (winrate, KDA, CS/min...)
  .env               # RIOT_API_KEY (git-ignored)
frontend/
  src/
    api.ts           # llamadas a NUESTRO backend (nunca a Riot)
    components/       # Summary, TrendChart, ChampionPool, LiveGame...
    ddragon.ts       # resolución de assets de campeón (Data Dragon)
```

El frontend consume endpoints propios tipo `/api/player/{name}/{tag}` que ya devuelven datos
agregados y listos para graficar. Toda la lógica de Riot y agregación vive en el backend.

## Convenciones

- Backend: Python 3.10+, FastAPI, `httpx` async. Frontend: React + TS + Recharts.
- Mensajes de UI en español; código en inglés.
- Normalizar IDs pronto: `puuid` es la llave canónica del jugador.
- Convertir timestamps de Riot (ms epoch) a fechas legibles en el backend, no en el frontend.
- Data Dragon: fijar una versión de parche y construir URLs de íconos de campeón a partir del
  `championName`/`championId` del match.

## Comandos

```bash
# backend
cd backend && source venv/bin/activate
uvicorn main:app --reload

# actualizar la RIOT_API_KEY cada 24h (la pide oculta, la valida contra Riot antes de guardarla)
make setkey   # atajo (Makefile en la raíz); por debajo corre: cd backend && ./venv/bin/python3 set_api_key.py

# frontend
cd frontend && npm run dev
```

## Endpoints propios sugeridos (backend → frontend)

- `GET /api/player/{name}/{tag}` → perfil + resumen agregado.
- `GET /api/player/{name}/{tag}/matches?start=0&count=5` → partidas paginadas (agregadas).
- `GET /api/player/{name}/{tag}/live` → SPECTATOR-V5 si aplica, si no 204.

## Proceso de desarrollo — `cache.py` / SQL

Esta es la primera vez que el usuario implementa SQLite/SQL en un proyecto real; lo eligió aquí
a propósito para aprenderlo. Por eso, al tocar `cache.py` o cualquier schema/query SQL:

- No generar el archivo completo de un jalón. Proponer el schema primero y explicar el porqué
  (ej. por qué `match_id` es la llave primaria, por qué cachear el JSON crudo de la partida).
- Escribir las queries de una en una, explicando qué hace cada una antes de escribirla.
- Dejar que el usuario corra/pruebe cada pieza antes de seguir con la siguiente.
- El resto del backend (`riot_client.py`, `aggregate.py`, `main.py`) sí se puede construir a ritmo
  normal, salvo que el usuario pida lo mismo ahí.

## Qué NO hacer

- No exponer la API key al cliente, no ponerla en URLs/query strings, no commitearla.
- No confundir ruteo plataforma (`la1`) con regional (`americas`); es el error #1 (da 404).
- No traer todo el historial de golpe: pagina y cachea.
- No inventar endpoints ni estructura de respuesta de Riot; si hay duda del esquema exacto de un
  campo, verificar contra la doc oficial (developer.riotgames.com) antes de asumir.
- No usar la data para fines comerciales con una dev key; respetar los ToS de Riot.
