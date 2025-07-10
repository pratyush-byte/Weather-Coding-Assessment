# Weather Coding Challenge – Quick Guide

## 🛠 1 · Set‑up (one‑time)

1. **Create & activate** a virtual‑environment
   python3 -m venv venv && source venv/bin/activate  # Windows: venv\Scripts\activate
2. **Install libraries** (all problems)
   Initial_checks_install.py

## My solution and approach including with step by step instructions to run the code
## Problem 1 – Schema

3. **Create the empty tables**
## Due to storage issue in GIT i have deleted the weather.db file, so please run this file
```bash
   python create_db.py       # produces weather.db with 3 empty tables
```                   


| Table                  | What it stores                   | Primary Key          |
| ---------------------- | -------------------------------- | -------------------- |
| `station`              | Every weather‑station ID         | `id`                 |
| `weather_daily`        | *station × day* raw observations | `(station_id, date)` |
| `weather_yearly_stats` | *station × year* aggregates      | `(station_id, year)` |

*Integers keep raw units: tenth‑°C & tenth‑mm; `‑9999` → `NULL`.*

---

## Problem 2 – Ingestion

### ✱ Significance

Turn thousands of flat‑files into relational rows **safely** (no duplicates) and **quickly** (bulk inserts, batching).

### 🚀 Key Features

| Aspect                | Detail                                                                  |
| --------------------- | ----------------------------------------------------------------------- |
| **Script**            | `ingest.py`                                                             |
| **Idempotent**        | `ON CONFLICT DO NOTHING` (composite PK) — reruns never duplicate rows.  |
| **Duplicate Metrics** | Every batch logs *new* vs. *dup*; per‑file totals in `logs/ingest.log`. |
| **Batching**          | SQLite ≤ 180 rows/flush (under 999‑param limit).                        |
| **Logging**           | Console **and** file `logs/ingest.log`.                                 |

### ▶︎ Run

```bash
python ingest.py      
```

Sample output

```
USC00110072 …  10 957 new · 0 dup
USC00110073 …       0 new · 10 957 dup
Done: 10 957 890 new · 10 957 dup
```

---

## Problem 3 – Data Analysis

### ✱ Significance

Condense millions of daily rows into **one row per station × year**, ready for fast API queries.  A diff log detects data drift instantly.

### 🚀 Key Features

| Aspect          | Detail                                                 |
| --------------- | ------------------------------------------------------ |
| **Script**      | `Data_analysis.py`                                 |
| **Model**       | Table `weather_yearly_stats` (PK `(station_id, year)`) |
| **SQLite‑only** | One aggregate `GROUP BY` query — no temp tables.       |
| **Idempotent**  | Table is rebuilt every run.                            |
| **Diff Log**    | NEW / CHG rows written to `logs/data_analysis.log`.    |

### ▶︎ Run

```bash
python Data_analysis.py
```

Example tail of log

```
NEW   USC00110072 1985  Tmax=12.3  Tmin=-1.5  Precip=67.4
▲ Yearly aggregation finished: 4 820 added · 0 changed · 0 removed · 0 unchanged (4.5 s)
```

---

## Problem 4 – REST API

### ✱ Significance

Serve cleaned weather data to any client via JSON with **filtering, pagination & live docs**.

### 🚀 Key Features

| Aspect             | Detail                                                                      |
| ------------------ | --------------------------------------------------------------------------- |
| **App**            | `app_flask.py` (Flask + Flask‑RESTX)                                        |
| **Endpoints**      | `/api/weather` · `/api/weather/stats`                                       |
| **Filters**        | `station_id`, `date` (range) on daily; `station_id`, `year` on yearly stats |
| **Pagination**     | `page` & `page_size` query params; 404 if page‑out‑of‑range                 |
| **Docs (Swagger)** | OpenAPI UI at `/docs` (auto‑generated)                                      |

### ▶︎ Run

```bash
export FLASK_APP=app_flask.py     # Windows: set FLASK_APP=app_flask.py
flask run                          # starts http://127.0.0.1:5000/
# OR RUN
python app_flask.py
```

*Open* [http://127.0.0.1:5000/docs](http://127.0.0.1:5000/docs) for Swagger, or test with Postman:

```
GET http://127.0.0.1:5000/api/weather?page=1&page_size=5&station_id=USC00110072
```

---

## 🔎 Verify Everything

```
python check_counts.py            # rows & samples from all three tables
pytest -q                         # runs unit tests (ingestion only)
```

## EXTRA CREDIT  Deployment

I don’t have hands-on production cloud experience yet, but from my studies and research this is the approach I would take. I’d first containerize the whole project with Docker, ensuring the code and dependencies run identically everywhere. I’d push that image to AWS Elastic Beanstalk, which can launch and manage an EC2 instance, pull the image, and keep the Flask API live behind an autoscaling load balancer. For storage I’d provision a managed Amazon RDS PostgreSQL database during the same Beanstalk setup, then drop the generated connection string into my environment variables. Finally, I’d automate the nightly ingest.py run using Elastic Beanstalk’s built-in cron.yaml (or a lightweight AWS Lambda trigger if more flexibility is needed). This stack gives me a fully managed deployment—API, database, and scheduled ingestion—while letting me focus on code rather than server maintenance.
