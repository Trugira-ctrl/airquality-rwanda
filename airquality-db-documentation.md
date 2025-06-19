# Air Quality Database Documentation

## Overview

This database stores air quality monitoring data from two sources:
- **PurpleAir**: Community-based air quality sensors
- **REMA**: Rwanda Environment Management Authority stations

**Database**: `airspectrum_dev` (PostgreSQL 17)  
**Created**: June 2025

## Database Architecture

### Schemas

| Schema | Purpose | Usage |
|--------|---------|--------|
| `aq_core` | Production-ready schema | Clean, validated data ready for analysis |
| `thierry_sandbox` | Development/testing schema | Safe environment for ETL development and experiments |

### Tables Structure

#### 1. PurpleAir Tables

**Tables**: 
- `aq_core.purpleair_readings`
- `thierry_sandbox.purpleair_readings`

**Structure**:
```sql
Column          | Type                        | Constraints
----------------|-----------------------------|--------------------------
sensor_id       | TEXT                        | NOT NULL, Part of PK
name            | TEXT                        | 
latitude        | NUMERIC                     | CHECK (-90 to 90)
longitude       | NUMERIC                     | CHECK (-180 to 180)
time_stamp      | TIMESTAMPTZ                 | NOT NULL, Part of PK
humidity        | NUMERIC                     | CHECK (0 to 100)
temperature     | NUMERIC                     | Celsius
pressure        | NUMERIC                     | Atmospheric pressure
pm1_0_cf_1      | NUMERIC                     | CHECK (>= 0)
pm1_0_atm       | NUMERIC                     | CHECK (>= 0)
pm2_5_cf_1      | NUMERIC                     | CHECK (>= 0)
pm2_5_atm       | NUMERIC                     | CHECK (>= 0)
pm10_0_cf_1     | NUMERIC                     | CHECK (>= 0)
pm10_0_atm      | NUMERIC                     | CHECK (>= 0)
raw_payload     | JSONB                       | Complete API response
inserted_at     | TIMESTAMPTZ                 | DEFAULT NOW()

Primary Key: (sensor_id, time_stamp)
```

**PM Reading Types**:
- `cf_1`: "Standard" particles (CF=1) - direct sensor measurement
- `atm`: "Atmospheric" - adjusted for ambient conditions (typically used for AQI)

#### 2. REMA Tables

**Tables**:
- `aq_core.rema_readings`
- `thierry_sandbox.rema_readings`

**Structure**:
```sql
Column          | Type                        | Constraints
----------------|-----------------------------|--------------------------
ramp_id         | TEXT                        | NOT NULL
site_code       | TEXT                        | NOT NULL, Part of PK
name            | TEXT                        | Station name
time            | TEXT                        | Original time format
reading_time    | TIMESTAMPTZ                 | NOT NULL, Part of PK
updated         | TEXT                        | Last update time
pm25            | NUMERIC                     | CHECK (>= 0)
pm10            | NUMERIC                     | CHECK (>= 0)
co              | NUMERIC                     | Carbon monoxide (ppm)
co2             | NUMERIC                     | CHECK (>= 0)
no2             | NUMERIC                     | Nitrogen dioxide (ppb)
o3              | NUMERIC                     | Ozone (ppb)
so2             | NUMERIC                     | Sulfur dioxide (ppb)
aqi             | INTEGER                     | CHECK (>= 0)
dp              | TEXT                        | Dominant pollutant
color           | TEXT                        | AQI color category
trend           | INTEGER                     | -1, 0, or 1
display         | BOOLEAN                     | Show on dashboard
batt            | NUMERIC                     | Battery voltage
chrg            | NUMERIC                     | Charging status
raw_payload     | JSONB                       | Complete API response
inserted_at     | TIMESTAMPTZ                 | DEFAULT NOW()

Primary Key: (site_code, reading_time)
```

### Indexes

#### PurpleAir Indexes (both schemas):
- `idx_[schema]_purpleair_time`: On `time_stamp DESC` for time-based queries
- `idx_[schema]_purpleair_sensor`: On `sensor_id` for sensor lookups
- `idx_[schema]_purpleair_location`: On `(latitude, longitude)` for spatial queries

#### REMA Indexes (both schemas):
- `idx_[schema]_rema_time`: On `reading_time DESC` for time-based queries
- `idx_[schema]_rema_site`: On `site_code` for station lookups
- `idx_[schema]_rema_aqi`: On `aqi` for air quality threshold queries

### Views

All views are in the `aq_core` schema:

#### 1. `purpleair_latest`
Shows the most recent reading from each PurpleAir sensor.

**Columns**: sensor_id, name, time_stamp, readable_time, pm2_5_atm, pm10_0_atm, temperature, humidity, latitude, longitude

#### 2. `rema_latest`
Shows the most recent reading from each REMA station.

**Columns**: site_code, name, reading_time, readable_time, pm25, pm10, aqi, dominant_pollutant, aqi_color, trend, co, no2, o3, so2

#### 3. `all_pm25_readings`
Combines PM2.5 data from both sources for unified analysis.

**Columns**: source, station_id, name, reading_time, pm25, latitude, longitude

#### 4. `hourly_averages`
Provides hourly averaged values for trend analysis.

**Columns**: source, station_id, hour, avg_pm25, avg_pm10, avg_temperature, avg_humidity, reading_count

## Usage Examples

### Inserting Data

```sql
-- PurpleAir data insert
INSERT INTO thierry_sandbox.purpleair_readings (
    sensor_id, name, latitude, longitude, time_stamp,
    humidity, temperature, pm2_5_atm, pm10_0_atm
) VALUES (
    '12345', 'Kigali Central', -1.9441, 30.0619, '2025-06-16 14:00:00+00',
    65.5, 23.2, 25.3, 35.2
);

-- REMA data insert
INSERT INTO thierry_sandbox.rema_readings (
    ramp_id, site_code, name, reading_time,
    pm25, pm10, aqi, dp, color
) VALUES (
    '1063', 'MK001', 'Mont Kigali', '2025-06-16 14:00:00+00',
    41.88, 49.27, 115, 'PM2.5', 'orange'
);
```

### Querying Data

```sql
-- Get latest readings across all stations
SELECT * FROM aq_core.all_pm25_readings 
WHERE reading_time > NOW() - INTERVAL '1 hour'
ORDER BY pm25 DESC;

-- Get hourly trends for a specific station
SELECT * FROM aq_core.hourly_averages
WHERE station_id = 'MK001'
  AND hour > NOW() - INTERVAL '24 hours'
ORDER BY hour;

-- Find stations exceeding WHO guidelines (25 μg/m³ for PM2.5)
SELECT source, station_id, name, pm25, reading_time
FROM aq_core.all_pm25_readings
WHERE pm25 > 25
  AND reading_time > NOW() - INTERVAL '1 hour';
```

## Maintenance

### Data Retention
- Consider implementing a retention policy (e.g., detailed data for 1 year, hourly averages for 5 years)
- Archive old data to reduce table size

### Vacuum and Analyze
```sql
-- Run periodically to maintain performance
VACUUM ANALYZE aq_core.purpleair_readings;
VACUUM ANALYZE aq_core.rema_readings;
```

### Monitoring Table Sizes
```sql
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size,
    n_live_tup as row_count
FROM pg_stat_user_tables
WHERE schemaname IN ('aq_core', 'thierry_sandbox')
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

## ETL Workflow

1. **Development**: Test all ETL scripts using `thierry_sandbox` schema
2. **Validation**: Verify data quality and transformations
3. **Staging**: Run ETL against `aq_core` schema in dev environment
4. **Production**: Deploy tested ETL to production AWS RDS

## Security Considerations

- Never store API keys in the database
- Use environment variables for credentials
- Implement row-level security if needed for multi-tenant access
- Regular backups of `aq_core` schema

## Troubleshooting

### Common Issues

1. **Duplicate key violations**
   - Check for existing records with same (sensor_id, time_stamp) or (site_code, reading_time)
   - Use `ON CONFLICT DO NOTHING` or `DO UPDATE` in INSERT statements

2. **Check constraint violations**
   - Validate data ranges before insertion
   - PM values should be >= 0
   - Humidity should be 0-100
   - Coordinates should be valid

3. **Performance issues**
   - Ensure indexes exist and are being used
   - Run `EXPLAIN ANALYZE` on slow queries
   - Consider partitioning tables by month if data volume is high

## Next Steps

1. Set up ETL pipelines for both data sources
2. Implement data quality checks
3. Create monitoring dashboards
4. Set up automated backups
5. Plan for production deployment to AWS RDS