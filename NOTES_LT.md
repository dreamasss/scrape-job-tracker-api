# Project notes LT — Scrape Job Tracker API

Šitos pastabos skirtos greitai prisiminti, kaip veikia projektas po pertraukos.

Projektas: `Scrape Job Tracker API`

Live API:

```text
https://scrape-job-tracker-api.onrender.com
```

Swagger:

```text
https://scrape-job-tracker-api.onrender.com/docs
```

Health DB:

```text
https://scrape-job-tracker-api.onrender.com/health/db
```

---

## Bendras projekto tikslas

Šitas projektas yra web scraping backend API.

Paprasta idėja:

```text
Useris paduoda URL.
Backend parsisiunčia puslapio HTML.
Backend iš HTML ištraukia paprastus duomenis.
Rezultatas gali būti grąžintas iš karto arba išsaugotas DB kaip scrape job.
```

Ištraukiami duomenys:

```text
title
h1
meta_description
links_count
```

Projektas mokina ne tik Python syntax, bet realų backend workflow:

```text
FastAPI
Pydantic schemas
SQLAlchemy models
SQLite lokaliai
PostgreSQL per Docker/Render
Alembic migrations
Dockerfile
Docker Compose
Render deploy
GitHub Actions CI
Ruff
pytest
smoke test
Makefile
```

Svarbu: tai dar nėra advanced scraperis. Jis nenaudoja Playwright, Redis ar anti-bot logikos. Dabar tai MVP backend projektas.

---

## Sesija 1 — API struktūra ir endpointai

Pagrindiniai endpointai:

```text
GET /
GET /health
GET /health/db
POST /scrape/preview
POST /jobs
GET /jobs
GET /jobs/{job_id}
```

### `GET /`

Root endpointas grąžina bazinę informaciją apie API.

Response panašus:

```json
{
  "name": "Scrape Job Tracker API",
  "version": "0.2.0",
  "status": "ok",
  "docs": "/docs",
  "health": "/health"
}
```

Ką jis parodo?

```text
FastAPI app paleistas.
Render pasiekia tavo servisą.
Root route veikia.
```

### `GET /health`

Tikrina, ar pats API gyvas.

Response:

```json
{
  "status": "ok"
}
```

### `GET /health/db`

Tikrina ne tik API, bet ir DB connection.

Response:

```json
{
  "status": "ok",
  "database": "ok"
}
```

Šitas endpointas svarbus deploy/cloud aplinkoje, nes API gali būti gyvas, bet DB neveikti.

### `POST /scrape/preview`

Šitas endpointas parsisiunčia puslapį ir iškart grąžina ištrauktus duomenis.

Svarbu: jis **neišsaugo** rezultato į DB.

Request:

```json
{
  "url": "https://example.com"
}
```

Response:

```json
{
  "url": "https://example.com/",
  "title": "Example Domain",
  "h1": "Example Domain",
  "meta_description": null,
  "links_count": 1
}
```

### `POST /jobs`

Šitas endpointas daro panašų scrape, bet rezultatą išsaugo DB kaip `ScrapeJob`.

Flow:

```text
gauna URL
sukuria job su status=pending
fetchina HTML
parsina HTML
jei pavyko -> status=success
jei nepavyko -> status=failed ir error_message
išsaugo DB
grąžina job
```

### `GET /jobs`

Grąžina scrape jobs sąrašą su pagination metadata.

Response forma:

```json
{
  "total": 2,
  "limit": 50,
  "offset": 0,
  "items": []
}
```

Galimi query parametrai:

```text
limit
offset
status
```

Pavyzdžiai:

```text
GET /jobs?limit=10&offset=0
GET /jobs?status=success
GET /jobs?status=failed
```

### `GET /jobs/{job_id}`

Grąžina vieną job pagal ID.

Jei job neegzistuoja:

```json
{
  "detail": "Scrape job not found"
}
```

---

## Sesija 2 — Scrape preview flow

Scrape preview yra paprasčiausias scraping flow.

Kodo kelias:

```text
POST /scrape/preview
-> app/routers/scrape.py
-> scrape_preview()
-> fetch_html()
-> parse_html()
-> grąžina JSON response
```

### `app/routers/scrape.py`

Šitas routeris priima URL per Pydantic schema:

```text
ScrapePreviewRequest
```

URL tipas yra `HttpUrl`, todėl FastAPI/Pydantic automatiškai tikrina, ar URL atrodo kaip validus URL.

Jei URL blogas, API grąžina validation error.

### `fetch_html()`

Failas:

```text
app/services/fetcher.py
```

Šita funkcija naudoja `httpx.AsyncClient`.

Ji daro:

```text
GET request į userio URL
follow_redirects=True
timeout iš config
User-Agent iš config
response.raise_for_status()
return response.text
```

Jei puslapis grąžina 404/500 arba connection failina, `httpx` išmeta klaidą.

### `parse_html()`

Failas:

```text
app/services/parser.py
```

Šita funkcija naudoja BeautifulSoup.

Ji ištraukia:

```text
<title>
pirmą <h1>
<meta name="description">
visų <a> tagų kiekį
```

Trumpai:

```text
fetcher = parsisiunčia HTML
parser = ištraukia duomenis iš HTML
router = priima requestą ir grąžina response
```

Svarbi mintis: `fetcher` ir `parser` atskirti, nes taip lengviau testuoti ir plėsti projektą.

---

## Sesija 3 — Parseris

Parserio tikslas: iš HTML stringo padaryti struktūruotą dict.

Input:

```text
HTML tekstas
```

Output:

```python
{
    "title": "...",
    "h1": "...",
    "meta_description": "...",
    "links_count": 0,
}
```

### Kodėl yra `clean_text()`

`clean_text()` sutvarko tekstą:

```text
jei None -> grąžina None
jei tekstas su tarpais -> strip()
jei po strip lieka tuščia -> None
```

Tai padeda negauti tuščių stringų kaip validžių reikšmių.

Pvz:

```text
"   Example   " -> "Example"
"    " -> None
None -> None
```

### Kodėl parseris neturi HTTP logikos

Parseris neturi fetchinti puslapio. Jis gauna HTML ir parsina.

Tai gerai, nes:

```text
lengva testuoti su fake HTML
nereikia interneto testuose
viena funkcija daro vieną darbą
```

---

## Sesija 4 — Jobs ir database

`POST /jobs` yra svarbiausias projekto flow, nes jis išsaugo rezultatą DB.

Modelis:

```text
ScrapeJob
```

Failas:

```text
app/models.py
```

Laukai:

```text
id
url
status
title
h1
meta_description
links_count
error_message
created_at
```

### Statusai

Galimi job statusai:

```text
pending
success
failed
```

Flow:

```text
1. Sukuriamas ScrapeJob su status="pending".
2. Job išsaugomas DB, kad gautų ID.
3. Backend bando fetchinti HTML.
4. Jei fetch pavyko, HTML parsintas ir job status tampa "success".
5. Jei fetch nepavyko, status tampa "failed".
6. Klaida išsaugoma į error_message.
7. Job grąžinamas response.
```

Svarbu: dabar job vykdomas iš karto requesto metu, ne background queue.

Tai reiškia:

```text
POST /jobs laukia, kol puslapis bus parsisiųstas ir išparsintas.
```

Ateityje galima pridėti Redis/RQ, kad job būtų vykdomas backgrounde.

---

## Sesija 5 — SQLAlchemy ir DB session

Failas:

```text
app/database.py
```

Čia sukuriami:

```text
DATABASE_URL
engine
SessionLocal
Base
get_db()
```

### `DATABASE_URL`

Lokaliai default:

```text
sqlite:///./scrape_jobs.db
```

Docker/Render naudoja environment variable:

```text
DATABASE_URL
```

### Render PostgreSQL URL problema

Render dažnai duoda URL formatu:

```text
postgresql://...
```

Bet projekte naudojamas `psycopg`, todėl SQLAlchemy turi naudoti:

```text
postgresql+psycopg://...
```

Tam yra funkcija:

```text
normalize_database_url()
```

Ji pakeičia:

```text
postgresql:// -> postgresql+psycopg://
```

Jei to nebūtų, Render deploy metu būtų klaida:

```text
ModuleNotFoundError: No module named 'psycopg2'
```

### `get_db()`

`get_db()` yra FastAPI dependency.

Ji:

```text
sukuria DB session
atiduoda ją endpointui
po requesto uždaro session
```

Endpointuose DB pasiekiama per:

```python
db: DBSession
```

---

## Sesija 6 — Schemos

Failas:

```text
app/schemas.py
```

Pagrindinės schemos:

```text
ScrapeJobCreate
ScrapeJobRead
ScrapeJobListResponse
```

### `ScrapeJobCreate`

Naudojama kuriant job:

```python
url: HttpUrl
```

`HttpUrl` validuoja URL.

### `ScrapeJobRead`

Naudojama grąžinti vieną job.

Ji turi:

```text
id
url
status
title
h1
meta_description
links_count
error_message
created_at
```

Joje yra:

```python
model_config = ConfigDict(from_attributes=True)
```

Tai leidžia Pydantic schemai skaityti SQLAlchemy modelio objektą.

Trumpai:

```text
SQLAlchemy modelis = DB objektas
Pydantic schema = API request/response forma
```

### `ScrapeJobListResponse`

Naudojama `/jobs` list endpointui.

Forma:

```text
total
limit
offset
items
```

`items` yra `list[ScrapeJobRead]`.

---

## Sesija 7 — Pagination ir status filter

`GET /jobs` palaiko:

```text
limit
offset
status
```

### `limit`

Kiek jobų grąžinti.

Default:

```text
50
```

Validation:

```text
ge=1
le=100
```

Tai reiškia:

```text
minimum 1
maximum 100
```

### `offset`

Kiek jobų praleisti.

Default:

```text
0
```

Validation:

```text
ge=0
```

### `status`

Filtruoja pagal job statusą.

Galimi:

```text
pending
success
failed
```

Jei status blogas:

```json
{
  "detail": "Invalid job status"
}
```

### Kodėl `total` skaičiuojamas atskirai

`total` turi parodyti, kiek iš viso įrašų atitinka filtrą, dar prieš `limit` ir `offset`.

Pvz:

```text
DB yra 100 success jobų.
Request: /jobs?status=success&limit=10&offset=0
Response:
total = 100
items = 10
```

Tai padeda frontendui daryti puslapiavimą.

---

## Sesija 8 — Docker ir Postgres

Dockerfile pasako, kaip sukurti API image.

Docker Compose paleidžia du servisus:

```text
api
db
```

### `db`

Naudoja:

```text
postgres:16
```

Turi env:

```text
POSTGRES_DB
POSTGRES_USER
POSTGRES_PASSWORD
```

Turi healthcheck:

```text
pg_isready
```

### `api`

Buildinamas iš tavo Dockerfile.

Naudoja env:

```text
DATABASE_URL
FETCH_TIMEOUT_SECONDS
USER_AGENT
```

Priklauso nuo DB:

```text
depends_on:
  db:
    condition: service_healthy
```

Tai reiškia, kad API startuoja tik tada, kai DB jau healthy.

### Docker start command

Docker/Render start komanda:

```text
alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
```

Tai reiškia:

```text
pirma paleidžia migracijas
tada paleidžia FastAPI serverį
```

`${PORT:-8000}` reiškia:

```text
jei PORT env yra -> naudoti jį
jei nėra -> naudoti 8000
```

Render duoda `PORT`, todėl production veikia. Lokaliai Docker naudoja 8000.

---

## Sesija 9 — Alembic migrations

Alembic yra DB migracijų įrankis SQLAlchemy projektams.

Kodėl reikalingas Alembic?

```text
Kad DB struktūros pakeitimai būtų valdomi versijomis.
Kad lentelės nebūtų kuriamos tiesiog app startup metu.
Kad production DB būtų atnaujinama kontroliuojamai.
```

Anksčiau app turėjo:

```python
Base.metadata.create_all(bind=engine)
```

Tai išimta iš `app/main.py`.

Dabar lenteles kuria:

```bash
alembic upgrade head
```

### `alembic/env.py`

Svarbios dalys:

```text
import app.models
target_metadata = Base.metadata
config.set_main_option("sqlalchemy.url", DATABASE_URL)
```

`import app.models` reikalingas tam, kad Alembic matytų tavo SQLAlchemy modelius.

`target_metadata = Base.metadata` pasako Alembic, kokią DB struktūrą lyginti.

### Migration file

Migration yra faile:

```text
alembic/versions/...create_scrape_jobs_table.py
```

Svarbu, kad migration turi:

```text
op.create_table("scrape_jobs")
op.drop_table("scrape_jobs")
```

Jei migration turi tik `pass`, ji yra tuščia ir bloga.

Kodėl buvo tuščia migracija?

```text
Nes lokali SQLite DB jau turėjo scrape_jobs lentelę.
Alembic palygino modelį su DB ir nematė skirtumo.
```

Fixas buvo:

```text
ištrinti tuščią migration
ištrinti lokalų scrape_jobs.db
generuoti migraciją iš švarios DB
```

---

## Sesija 10 — Config per environment variables

Failas:

```text
app/config.py
```

Config valdo:

```text
FETCH_TIMEOUT_SECONDS
USER_AGENT
```

Default reikšmės:

```text
FETCH_TIMEOUT_SECONDS=10
USER_AGENT=ScrapeJobTrackerBot/0.1
```

Kodėl geriau config, o ne hardcode?

```text
Lokaliai gali turėti vienas reikšmes.
Production gali turėti kitas reikšmes.
Nereikia keisti kodo dėl paprastų nustatymų.
```

### `get_fetch_timeout_seconds()`

Jei env nėra, grąžina default.

Jei env yra validus skaičius, naudoja jį.

Jei env blogas, pvz:

```text
bad-value
-1
```

grįžta prie default.

### `get_user_agent()`

Jei env yra, naudoja env.

Jei nėra, naudoja:

```text
ScrapeJobTrackerBot/0.1
```

---

## Sesija 11 — GitHub Actions CI ir Ruff

CI failas:

```text
.github/workflows/ci.yml
```

CI paleidžiamas:

```text
push į main
pull_request į main
```

CI daro:

```text
checkout code
setup Python 3.12
install dependencies
ruff check .
ruff format --check .
python -m pytest -q
```

Kodėl tai svarbu?

```text
Kiekvienas push automatiškai patikrinamas.
Jei testai arba formatas sugenda, GitHub Actions parodo klaidą.
Portfolio atrodo rimčiau.
```

### Ruff

Ruff tikrina:

```text
lint klaidas
import order
unused imports
kai kuriuos best practices
```

Ruff format tikrina:

```text
ar kodas suformatuotas pagal Ruff formatterį
```

Dažna situacija:

```text
ruff check praeina
ruff format --check sako, kad failas būtų reformatted
```

Tada fixas:

```bash
ruff format .
```

---

## Sesija 12 — Makefile

Makefile leidžia turėti trumpas komandas.

Svarbios komandos:

```bash
make check
make test
make run
make migrate
make smoke
make docker-up
make docker-down
make docker-logs
```

### `make check`

Paleidžia:

```text
ruff check .
ruff format --check .
python -m pytest -q
```

Tai pagrindinė komanda prieš commit.

### `make run`

Paleidžia lokalų FastAPI serverį:

```text
uvicorn app.main:app --reload
```

### `make migrate`

Paleidžia:

```text
alembic upgrade head
```

### `make smoke`

Paleidžia:

```text
python scripts/smoke_test.py
```

Svarbu: `make smoke` reikia paleisti tada, kai API jau veikia.

---

## Sesija 13 — Smoke test

Failas:

```text
scripts/smoke_test.py
```

Smoke testas tikrina realų veikiantį API per HTTP.

Default BASE_URL:

```text
http://localhost:8000
```

Live API galima testuoti taip:

```bash
BASE_URL=https://scrape-job-tracker-api.onrender.com make smoke
```

Smoke testas tikrina:

```text
GET /
GET /health
GET /health/db
POST /scrape/preview
POST /jobs
GET /jobs
GET /jobs/{job_id}
```

Jei bet kuris requestas failina, smoke testas sustoja ir parodo klaidą.

Skirtumas tarp pytest ir smoke:

```text
pytest testai tikrina konkrečią logiką, dažnai su fake/mocked fetch_html.
smoke testas tikrina realiai paleistą app per HTTP.
```

Smoke testas nėra skirtas visiems edge cases. Jis atsako į klausimą:

```text
Ar visa sistema apskritai gyva?
```

---

## Sesija 14 — Render deploy

Render paima kodą iš GitHub repo ir paleidžia jį internete.

Live URL:

```text
https://scrape-job-tracker-api.onrender.com
```

Render setup:

```text
Web Service
Runtime: Docker
GitHub repo: dreamasss/scrape-job-tracker-api
Branch: main
Health Check Path: /health/db
```

Environment variables Render pusėje:

```text
DATABASE_URL
FETCH_TIMEOUT_SECONDS
USER_AGENT
```

### Render DB

Render Postgres duoda DATABASE_URL.

Svarbu naudoti Internal Database URL, kai web service ir DB yra tame pačiame Render account/region.

### Deploy klaida su psycopg2

Buvo klaida:

```text
ModuleNotFoundError: No module named 'psycopg2'
```

Priežastis:

```text
Render DB URL buvo postgresql://...
SQLAlchemy pagal nutylėjimą bandė naudoti psycopg2.
Bet projekte įdiegtas psycopg.
```

Fixas:

```text
normalize_database_url()
```

pakeičia:

```text
postgresql:// -> postgresql+psycopg://
```

### Render routing klaida

Buvo situacija, kai:

```text
/health/db veikė
/health, /docs ir / grąžino 404 su x-render-routing: no-server
```

Tai nebuvo Python klaida. Tai buvo Render routing/settings problema.

Po pataisymo visi endpointai grąžino 200:

```text
/          -> 200
/health    -> 200
/docs      -> 200
/health/db -> 200
```

---

## Sesija 15 — Testų overview

Dabar projekte yra apie:

```text
21 passed
```

Testų grupės:

```text
health tests
parser tests
config tests
jobs tests
```

### Health testai

Tikrina:

```text
GET /health
GET /health/db
GET /
```

Pagautų bugą, jei API nebeatsakytų arba DB health endpointas neveiktų.

### Parser testai

Tikrina, ar `parse_html()`:

```text
ištraukia title
ištraukia h1
ištraukia meta description
suskaičiuoja linkus
tvarkingai elgiasi, kai laukų nėra
```

Pagautų bugą, jei HTML parsing logika sugestų.

### Config testai

Tikrina:

```text
default timeout
env timeout
blogą timeout reikšmę
neigiamą timeout
default user-agent
env user-agent
```

Pagautų bugą, jei production config neveiktų arba blogos env reikšmės nulaužtų app.

### Jobs testai

Tikrina:

```text
create job success
create job failed fetch
list jobs
get job by ID
unknown job 404
limit/offset pagination
status=success filter
status=failed filter
invalid status 400
invalid limit 422
```

Svarbu: jobs testai nenaudoja tikro interneto. Jie mockina `fetch_html`.

Tai reiškia:

```text
testai greiti
testai stabilūs
testai nepriklauso nuo example.com ar tinklo
```

---

## Sesija 16 — Testų supratimas

### Testas: `test_create_scrape_job_success`

Ką testuoja?

Patikrina, ar `POST /jobs` su valid URL sukuria job, sėkmingai išparsina fake HTML ir grąžina `status=success`.

Kokį bugą pagautų?

Pagautų, jei job nebūtų išsaugomas DB, jei parserio rezultatai nebūtų įrašyti į job laukus arba jei statusas neliktų `success`.

Kas būtų, jei testas dingtų?

Galėtume nepastebėti, kad pagrindinis projekto flow nebeveikia.

---

### Testas: `test_create_scrape_job_failed_fetch`

Ką testuoja?

Patikrina, ar `POST /jobs` tvarkingai apdoroja fetch klaidą.

Kokį bugą pagautų?

Pagautų, jei requestas nulūžtų su 500 vietoj to, kad job būtų išsaugotas su `status=failed`.

Kas būtų, jei testas dingtų?

Galėtume nepastebėti, kad blogas URL arba connection problema nulaužia API.

---

### Testas: `test_list_scrape_jobs`

Ką testuoja?

Patikrina, ar `/jobs` grąžina išsaugotus jobus naujausius pirmiau ir su metadata.

Kokį bugą pagautų?

Pagautų, jei list endpointas negrąžintų jobų, grąžintų bloga tvarka arba response nebeturėtų `total`, `limit`, `offset`, `items`.

Kas būtų, jei testas dingtų?

Frontendui arba API vartotojui būtų sunku dirbti su jobų sąrašu.

---

### Testas: `test_get_scrape_job_by_id`

Ką testuoja?

Patikrina, ar galima gauti konkretų job pagal ID.

Kokį bugą pagautų?

Pagautų, jei `/jobs/{job_id}` endpointas nerastų egzistuojančio job arba grąžintų blogą objektą.

Kas būtų, jei testas dingtų?

Galėtume nepastebėti, kad detail endpointas neveikia, nors list endpointas vis dar veikia.

---

### Testas: `test_get_scrape_job_returns_404_for_unknown_id`

Ką testuoja?

Patikrina, kad neegzistuojantis job grąžina 404.

Kokį bugą pagautų?

Pagautų, jei API grąžintų 500 arba tuščią objektą vietoj aiškios 404 klaidos.

Kas būtų, jei testas dingtų?

API error handling būtų silpnesnis ir mažiau nuspėjamas.

---

### Testas: `test_list_scrape_jobs_uses_limit_and_offset`

Ką testuoja?

Patikrina, ar `/jobs?limit=1&offset=1` tikrai grąžina tik vieną įrašą ir praleidžia naujausią.

Kokį bugą pagautų?

Pagautų, jei backend ignoruotų `limit` arba `offset`.

Kas būtų, jei testas dingtų?

API su daug jobų galėtų grąžinti per daug duomenų ir pagination neveiktų.

---

### Testas: `test_list_scrape_jobs_filters_by_success_status`

Ką testuoja?

Patikrina, ar `/jobs?status=success` grąžina tik sėkmingus jobus.

Kokį bugą pagautų?

Pagautų, jei status filter būtų ignoruojamas.

Kas būtų, jei testas dingtų?

Vartotojas negalėtų patikimai atsifiltruoti sėkmingų jobų.

---

### Testas: `test_list_scrape_jobs_filters_by_failed_status`

Ką testuoja?

Patikrina, ar `/jobs?status=failed` grąžina tik nepavykusius jobus.

Kokį bugą pagautų?

Pagautų, jei failed jobai būtų maišomi su success jobais arba filtras neveiktų.

Kas būtų, jei testas dingtų?

Būtų sunkiau debuginti scrape klaidas.

---

### Testas: `test_list_scrape_jobs_rejects_invalid_status`

Ką testuoja?

Patikrina, kad blogas status, pvz. `unknown`, grąžina 400.

Kokį bugą pagautų?

Pagautų, jei API priimtų bet kokį status stringą ir elgtųsi nenuspėjamai.

Kas būtų, jei testas dingtų?

API validacija būtų silpnesnė.

---

### Testas: `test_list_scrape_jobs_rejects_invalid_limit`

Ką testuoja?

Patikrina, kad `limit=0` grąžina 422 validation error.

Kokį bugą pagautų?

Pagautų, jei pagination validacija dingtų.

Kas būtų, jei testas dingtų?

API galėtų priimti blogus pagination parametrus.

---

## Sesija 17 — Ką galiu sakyti per interview

Trumpas projekto paaiškinimas angliškai:

```text
This is a FastAPI web scraping backend API. A user can submit a URL, the API fetches the HTML, parses basic page metadata such as title, H1, meta description and link count, and stores the result as a scrape job in the database. The project uses SQLAlchemy, Alembic migrations, Docker Compose with PostgreSQL, GitHub Actions CI, Ruff, pytest, and is deployed on Render.
```

Lietuviškai:

```text
Tai FastAPI web scraping backend API. Useris paduoda URL, API parsisiunčia HTML, ištraukia pagrindinius duomenis kaip title, h1, meta description ir linkų kiekį, tada išsaugo rezultatą kaip scrape job DB. Projektas naudoja SQLAlchemy, Alembic, Docker Compose su PostgreSQL, GitHub Actions CI, Ruff, pytest ir yra deployintas Render.
```

### Jeigu klausia, kodėl skiri preview ir jobs

Angliškai:

```text
The preview endpoint returns parsed data immediately without saving it. The jobs endpoint stores the scrape result in the database and tracks status, so it is closer to a real production workflow.
```

Lietuviškai:

```text
Preview endpointas tik greitai parodo rezultatą ir nieko nesaugo. Jobs endpointas išsaugo rezultatą DB ir turi statusą, todėl labiau panašu į realų production flow.
```

### Jeigu klausia, kodėl mockini `fetch_html` testuose

Angliškai:

```text
External websites are unreliable in tests. They can be slow, blocked, or unavailable. By mocking `fetch_html`, tests stay fast, deterministic, and focused on my API logic.
```

Lietuviškai:

```text
Tikri web puslapiai testuose nėra patikimi: gali būti lėti, užblokuoti arba neveikti. Mockinant `fetch_html`, testai lieka greiti, stabilūs ir tikrina mano API logiką.
```

### Jeigu klausia, kam Alembic

Angliškai:

```text
Alembic manages database schema changes with versioned migrations. Instead of creating tables automatically on app startup, migrations make database changes explicit, repeatable, and safer for production.
```

Lietuviškai:

```text
Alembic valdo DB struktūros pakeitimus per versijuotas migracijas. Vietoj to, kad app startup metu automatiškai kurtų lenteles, migracijos padaro DB pakeitimus aiškius ir saugesnius production aplinkai.
```

### Jeigu klausia, ką dar pridėtum

Angliškai:

```text
Next I would add background jobs with Redis/RQ, better error handling, request retry logic, rate limiting, and later Playwright support for JavaScript-heavy pages.
```

Lietuviškai:

```text
Toliau pridėčiau background jobs su Redis/RQ, geresnį error handling, retry logiką, rate limiting ir vėliau Playwright JavaScript-heavy puslapiams.
```

---

## Trumpa santrauka

```text
Scrape Job Tracker API = FastAPI backend, kuris fetchina URL, parsina HTML ir saugo scrape jobs DB.
```

Pagrindiniai komponentai:

```text
main.py = FastAPI app ir health endpoints
scrape.py = preview scraping endpoint
jobs.py = saved scrape jobs endpointai
fetcher.py = HTTP request į URL
parser.py = HTML parsing su BeautifulSoup
database.py = SQLAlchemy engine/session/Base
models.py = ScrapeJob DB modelis
schemas.py = Pydantic request/response schemas
config.py = env config timeout/user-agent
alembic/ = DB migrations
scripts/smoke_test.py = realaus API smoke testas
.github/workflows/ci.yml = GitHub Actions CI
Dockerfile/docker-compose.yml = containerized app + Postgres
Makefile = shortcut komandos
```

Svarbiausia suprasti:

```text
POST /scrape/preview = scrape be DB
POST /jobs = scrape + išsaugojimas DB
GET /jobs = sąrašas su pagination ir status filter
Alembic = DB schema migrations
Docker Compose = API + Postgres lokaliai
Render = live deploy
Smoke test = realiai paleisto API patikra
Pytest = konkrečios logikos testai
```

---

## Update — Background scrape jobs

`POST /jobs` dabar sukuria scrape job su `status=pending` ir iškart grąžina `201 Created`.

Scraping vyksta FastAPI `BackgroundTasks` fone.

Flow:

```text
POST /jobs
-> sukuria job DB su status=pending
-> iškart grąžina response
-> background task fetchina/paršina URL
-> job tampa success arba failed
-> rezultatą galima tikrinti per GET /jobs/{job_id}
```

Kodėl tai geriau:

```text
API greičiau atsako į POST requestą.
Job turi aiškų status lifecycle.
Projektas labiau primena realų production job processing flow.
```

---

## Update — Production v2

Senas Render servisas `scrape-job-tracker-api` užstrigo su deploy problema, todėl sukurtas naujas Render Web Service:

```text
https://scrape-job-tracker-api-v2.onrender.com
```

Patikrinta live:

```text
GET /health/db -> ok
make smoke -> Smoke test passed
GET /jobs/stats -> veikia
GET /jobs?sort_by=id&sort_order=asc&url_contains=example -> veikia
DELETE /jobs/{job_id} -> veikia
URL safety localhost test -> veikia
```

Dabartinis projekto statusas:

```text
44 passed
Live API veikia per scrape-job-tracker-api-v2
PostgreSQL DB veikia
Background jobs veikia
Stats, retry, delete, sorting, url_contains ir URL safety veikia
```

Trumpas apibūdinimas:

```text
Tai FastAPI web scraping backend API. Vartotojas paduoda URL, API sukuria scrape jobą, backgrounde parsisiunčia ir išparsina puslapį, išsaugo rezultatą PostgreSQL DB ir leidžia jobus listinti, filtruoti, rūšiuoti, retryinti, trinti bei matyti statistiką.
```

---

## Update — Admin API Key

Pridėta admin API key apsauga pavojingesniems endpointams:

```text
POST /jobs/{job_id}/retry
DELETE /jobs/{job_id}
```

Jei `ADMIN_API_KEY` env var nustatytas, šiems endpointams reikia headerio:

```text
X-API-Key: tavo-secret-key
```

Kodėl tai naudinga:

```text
Live demo gali būti viešas, bet bet kas negalės trinti ar retryinti jobų be rakto.
```

Dabartinis testų rezultatas:

```text
49 passed
```
