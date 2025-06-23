# Air Quality Rwanda ETL

This repository contains a simple ETL pipeline for downloading air quality data from PurpleAir and loading it into a PostgreSQL database.

## Setup

1. Install Python dependencies:

```bash
pip install -r requirements.txt
```

2. Configure environment variables. The script expects a PurpleAir API key and a list of private sensor IDs with their read keys. These can be set in an `.env` file or directly in the environment:

```bash
export PURPLEAIR_API_KEY=<your purpleair api key>
export PURPLEAIR_PRIVATE_SENSORS="sensor_id:read_key,sensor_id:read_key"
```

See `PA_sensors.json` for an example of how sensors and read keys can be stored.

3. Run the ETL process:

```bash
python etl/main.py
```

The script will fetch data from PurpleAir and write it to the configured PostgreSQL schema.
