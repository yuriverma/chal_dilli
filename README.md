---
title: Chal Dilli API
emoji: 🚇
colorFrom: indigo
colorTo: pink
sdk: docker
app_port: 7860
pinned: false
---

# Chal Dilli

A Delhi travel assistant. Ask it how to get somewhere and it answers with a
real route: an actual shortest path over the DMRC and DTC timetables, with the
fare, the interchanges, and which station gate to walk out of.

The frontmatter above is Hugging Face Space config — it is only read when this
repo is pushed to a Space, and is ignored everywhere else.

## What it actually does

| Feature | Implementation |
|---|---|
| Metro routing | Dijkstra over the DMRC GTFS feed, with fare estimation, interchange detection and an Airport Express penalty |
| Station gates | Which gate or lift to use, from 257 records parsed out of a DMRC PDF |
| Bus routing | Dijkstra over a DTC GTFS feed, including multi-leg transfers |
| Food | Haversine radius search over a restaurant dataset, split into a "safe pick" (rating) and a "local favourite" (review volume) |
| Follow-ups | `backend/conversation_state.py` — see below |
| Events | Parse.bot over BookMyShow / Unstop (needs an API key; degrades to 503 without one) |

There is no language model anywhere in this. Intent is keyword-routed and the
answers come from the routing engines, which means a fare is either correct or
absent — never invented.

## Follow-up questions

`/chat` accepts an optional `conversation_id`. Send it back on each message and
elliptical follow-ups resolve against what the conversation already
established:

```
you:  dwarka se cp kaise jaun
bot:  Dwarka → Rajiv Chowk, ~51 min, ₹45, exit at Gate 2 …

you:  and from there to saket
bot:  ("there" -> Rajiv Chowk)  Rajiv Chowk → Saket …

you:  and by bus?
bot:  (bus: Rajiv Chowk to Saket)  …

you:  food near there
bot:  ("there" -> Saket)  …
```

The rewrite is reported back in `resolved_context` rather than applied
silently, so a wrong guess is visible. Omit `conversation_id` and every turn is
independent, exactly as before.

State is in-process and expires after two hours. That is why the server runs a
single worker — see the note in the `Dockerfile`.

## Running it locally

Backend:

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r backend/requirements.txt
playwright install chromium          # only needed for the events endpoints
uvicorn backend.api_server:app --reload --port 8000
```

It boots in about six seconds. `/chat` answers immediately; the metro-status
scrape finishes in the background, so `data_freshness` is `null` for the first
couple of seconds, which is expected.

Frontend:

```bash
cd frontend/chal-delhi
npm install
cp .env.example .env.local          # point VITE_BRAIN_API_URL at the backend
npm run dev
```

## Deploying

The backend goes to a **Hugging Face Space** and the frontend to **Netlify**.
Both are free, and unlike a free Render instance a Space does not idle down
between visitors.

**Backend.** Create a Space with SDK `docker` and the free CPU hardware, then
push this repo to it. The `Dockerfile` already targets Spaces — it sets
`PORT=7860`, which is what Spaces expects — and the frontmatter at the top of
this README is the Space's config.

```bash
git remote add space https://huggingface.co/spaces/<user>/<space-name>
git push space main
```

Every file in the repo is under 10MB, so this is a plain git push with no LFS
setup. That is why `data/GTFS/bus_edges.csv` exists instead of the 76MB feed it
is derived from.

Set `ALLOWED_ORIGINS` to the frontend origin in the Space's settings once the
frontend is up. `ADMIN_TOKEN` and `PARSEBOT_API_KEY` are optional — see the
table below for what happens without them.

**Frontend.** Point Netlify at this repo; `netlify.toml` already has the right
base directory and SPA redirect. Set one build variable:

```
VITE_BRAIN_API_URL = https://<user>-<space-name>.hf.space
```

Leave `VITE_AUTH_API_URL` unset. `render.yaml` is kept as a working fallback if
you would rather use Render.

## Configuration

Everything external is an environment variable; nothing is hardcoded. Copy
`.env.example` and `frontend/chal-delhi/.env.example` and fill in what you
need. Every one of them is optional:

| Variable | Effect when unset |
|---|---|
| `PARSEBOT_API_KEY` | The two event endpoints return 503; the rest works |
| `ALLOWED_ORIGINS` | CORS allows all origins, without credentials |
| `ADMIN_TOKEN` | `POST /update-data` 404s instead of being world-callable |
| `VITE_AUTH_API_URL` | Login is skipped and the app opens straight into the chat |

The auth service the login pages talk to is **not in this repository** and no
longer runs. Leaving `VITE_AUTH_API_URL` empty is the supported configuration.

## Endpoints

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/chat` | The assistant. Accepts `query`, optional `conversation_id` |
| `GET` | `/health` | Liveness |
| `GET` | `/init-status` | Whether the routing engines have finished loading |
| `GET` | `/metro-status`, `/metro-routes` | Line status and the line list |
| `GET` | `/delhi-info`, `/data-summary` | Dataset counts and freshness |
| `POST` | `/update-data` | Force a re-scrape. Requires `X-Admin-Token` |
| `POST` | `/api/parse-events-from-url` | Events via Playwright + Parse.bot |
| `POST` | `/api/parse-technical-events` | Hackathons via Parse.bot |

## Tests

```bash
python -m unittest discover -s tests
```

46 tests, no network, no API keys. `requirements-dev.txt` adds `pytest` if you
prefer `pytest tests`, but nothing requires it.

## Data

`data/` holds the metro GTFS feed, the derived bus graph, the gate table and
the restaurant set. These are point-in-time snapshots: only metro *status* is
scraped live, so fares and station lists drift as the network changes.

Two files are generated rather than downloaded, and both have a script:

- **`data/GTFS/bus_edges.csv`** — the DTC bus graph, 6,187 stop-to-stop edges.
  The raw feed expresses this as 2.25 million `stop_times` rows (one per stop
  per departure) of which the router reads three columns and discards the
  timetable entirely. Committing the derived graph instead of the 76MB feed
  cuts bus-router load from 4.5s to 0.03s and its peak memory from ~296MB to
  ~22MB. Rebuild it after a feed refresh with:

  ```bash
  python scripts/build_bus_graph.py data/GTFS
  ```

  That needs the full feed, which is deliberately not committed — download a
  current one from the DTC/OTD open data portal first. If `stop_times.csv` is
  present the router will fall back to deriving the graph itself, so a fresh
  feed works without running the script.

- **`data/dmrc_gates.csv`** — station gate and lift guidance, from
  `backend/dmrc_gates_parser.py` against the DMRC PDF. Needs `pdfplumber`,
  commented out of the requirements because nothing imports it at request time.
