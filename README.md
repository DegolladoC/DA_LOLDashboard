# Proyecto 9 — Dashboard de Datos de League of Legends

Panel web que consume la **Riot Games API**, analiza el historial de partidas de un jugador y
muestra estadísticas en gráficas que se actualizan solas: winrate, KDA, CS/min, pool de campeones,
daño, tendencia de las últimas partidas, y (opcional) detección de si el jugador está en partida
en vivo.

Conecta directo con tu experiencia en plataformas web y te sirve incluso como base de un dashboard
de métricas para SNAPP más adelante.

---

## Objetivo

Ingresar un Riot ID (`Nombre#TAG`), traer sus últimas N partidas, agregarlas y visualizar la
evolución del rendimiento. "Tiempo real" = polling periódico que detecta partidas nuevas y, si
está en juego, muestra la partida activa.

## ⚠️ Lo primero: la API key

1. Entra a **https://developer.riotgames.com** y haz login con tu cuenta de Riot.
2. Se te genera una **Development API Key** automáticamente.
3. **Caduca cada 24 horas** — hay que regenerarla a diario mientras desarrollas.
4. Para algo público/permanente necesitas una *Production Key* (requiere solicitud y revisión).
5. **Nunca** pongas la key en el frontend ni la subas a GitHub. Va en el backend, en `.env`.

## Región (importante, estás en México)

LoL usa **dos tipos de ruteo**:

- **Plataforma** (para SUMMONER-V4 y datos de invocador): México/LATAM Norte = **`la1`**.
  (LATAM Sur = `la2`.)
- **Regional** (para ACCOUNT-V5 y MATCH-V5): las Américas = **`americas`**.

Endpoints base:
- Plataforma: `https://la1.api.riotgames.com`
- Regional:   `https://americas.api.riotgames.com`

## Endpoints que vas a usar

| Servicio | Uso | Ruteo |
|----------|-----|-------|
| **ACCOUNT-V1** | `Nombre#TAG` → `puuid` | regional (`americas`) |
| **SUMMONER-V4** | `puuid` → perfil (nivel, icono, id) | plataforma (`la1`) |
| **MATCH-V5** | lista de match IDs + detalle de cada partida | regional (`americas`) |
| **LEAGUE-V4** | rango/liga (ranked) | plataforma (`la1`) |
| **SPECTATOR-V5** | ¿está en partida ahora? (opcional, tiempo real) | plataforma (`la1`) |
| **Data Dragon** | assets estáticos: nombres/íconos de campeones | CDN, sin key |

Autenticación: header `X-Riot-Token: <TU_API_KEY>` en cada llamada (Data Dragon no la necesita).

## Rate limits (dev key)

- Aproximadamente **20 req/s** y **100 req cada 2 min** (los reales vienen en los headers
  `X-App-Rate-Limit` / `X-App-Rate-Limit-Count`; son dinámicos, respétalos).
- Cada partida detallada = 1 request. Traer 20 partidas = ~22 requests. **Pagina** (5–10 a la vez).
- Implementa **caché** en el backend: las partidas terminadas nunca cambian, guárdalas.
- Ante un **429**, haz *backoff* (espera y reintenta), no machaques.

## Stack

| Capa | Tecnología | Por qué |
|------|-----------|---------|
| Backend (proxy) | FastAPI (Python) o Express (Node) | Esconde la key, cachea, maneja rate limits |
| Frontend | React + Vite + TypeScript | Tu terreno conocido |
| Gráficas | Recharts | Rápido de armar, se ve bien |
| Caché | Archivo/JSON o SQLite al inicio; Redis si escala | Evitar quemar el rate limit |

> El backend es obligatorio: es lo que protege tu API key y controla el rate limit. El frontend
> nunca habla con Riot directo.

## Arranque rápido

**Backend (FastAPI):**
```bash
mkdir backend && cd backend
python -m venv venv && source venv/bin/activate
pip install fastapi uvicorn httpx python-dotenv
echo "RIOT_API_KEY=RGAPI-tu-key-aqui" > .env
uvicorn main:app --reload
```

**Frontend:**
```bash
npm create vite@latest frontend -- --template react-ts
cd frontend && npm install && npm install recharts
npm run dev
```

## Métricas a visualizar

- **Resumen:** winrate, KDA promedio, CS/min, oro/min, duración media.
- **Tendencia:** KDA o victoria/derrota por partida (últimas 20) — línea o barras.
- **Pool de campeones:** partidas y winrate por campeón — barras o tabla con íconos (Data Dragon).
- **Distribución de roles/lanes** — pie o barras.
- **Daño / visión / objetivos** — comparativas por partida.
- **En vivo (opcional):** si SPECTATOR-V5 responde, mostrar campeones de la partida activa.

## Plan de la semana (este proyecto)

- **Día 1** — Registrar app, obtener key, probar en Postman/curl el flujo
  `ACCOUNT-V1 → SUMMONER-V4 → MATCH-V5`. Montar backend proxy mínimo con 1 endpoint.
- **Día 2** — Backend: endpoint que devuelve N partidas agregadas + caché básico. Frontend: input
  de Riot ID + tabla cruda de partidas.
- **Día 3** — Gráficas de resumen y tendencia con Recharts. Integrar íconos de campeones (Data Dragon).
- **Día 4** — Polling para partidas nuevas, manejo de 429/backoff, pulido visual, (opcional) SPECTATOR.

## Notas y trampas comunes

- Un **Riot ID** hoy es `gameName#tagLine` (ej. `Hide on bush#KR1`). El viejo "summoner name" ya no
  es la llave de entrada; empieza SIEMPRE por ACCOUNT-V1 para sacar el `puuid`.
- MATCH-V5 devuelve **match IDs** primero; luego pides el detalle de cada uno por separado.
- Los campeones vienen como IDs/keys numéricos en algunos campos: mapéalos con Data Dragon.
- Respeta los Términos de Servicio de la Riot API (uso no comercial con dev key, no revender datos).
