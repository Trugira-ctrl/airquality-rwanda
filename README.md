# Air Quality Rwanda ETL

This repository contains a small ETL pipeline for collecting air quality readings from PurpleAir sensors and loading them into a PostgreSQL database. A placeholder is included for future integration with REMA (Rwanda Environment Management Authority) stations.

## Project layout

- `etl/` – extraction and transformation helpers as well as the main runner
- `config.py` – configuration loader using environment variables or a `PA_sensors.json` file
- `db_utils.py` – helper functions for connecting to PostgreSQL and upserting data
- `airquality-db-documentation.md` – detailed database schema notes
- `crontab.example` – sample cron entry for scheduling the pipeline

## Requirements

Install dependencies into a virtual environment using `pip`:

```bash
pip install -r requirements.txt
```

Python 3.9 or newer is recommended.

## Configuration

Create a `.env` file with your connection details and API keys. The most important settings are:

- `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD` – PostgreSQL credentials
- `DB_SCHEMA` – target schema for the ETL (e.g. `thierry_sandbox`)
- `PURPLEAIR_API_KEY` – API key for the PurpleAir service
- `PURPLEAIR_PRIVATE_SENSORS` – comma separated `sensor_id:read_key` pairs or supply a `PA_sensors.json` file

Additional options such as `LOG_LEVEL` and `REQUEST_TIMEOUT` can also be specified. See `config.py` for the full list.

## Running the ETL

Activate your environment and run:

```bash
python etl/main.py
```

The script fetches data from PurpleAir, applies basic validation via `etl/data_quality.py` and writes the results to your configured database. A log file is created in the `logs/` directory for each run.

## Scheduling with cron

To execute the ETL every 30 minutes, add the following line to your crontab:

```cron
*/30 * * * * cd /path/to/airquality-rwanda && /usr/bin/env python etl/main.py >> logs/cron.log 2>&1
```

## Database documentation

See `airquality-db-documentation.md` for schema details, table descriptions and useful SQL queries.
