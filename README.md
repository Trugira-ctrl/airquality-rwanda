# Air Quality Rwanda ETL

This project collects PurpleAir sensor data and stores it in a PostgreSQL database.

## Running the ETL

Activate your environment and run:

```bash
python etl/main.py
```

Configuration is handled via environment variables in the `.env` file. See `config.py` for details.

## Scheduling with Cron

To run the ETL every 30 minutes you can add the following entry to your crontab:

```cron
*/30 * * * * cd /path/to/airquality-rwanda && /usr/bin/env python etl/main.py >> logs/cron.log 2>&1
```

This executes the ETL twice an hour and writes output to `logs/cron.log`.
