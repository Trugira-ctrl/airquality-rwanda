-- =====================================================
-- AIR QUALITY DATABASE QUICK REFERENCE
-- Database: airspectrum_dev
-- =====================================================

-- ========== HEALTH CHECKS ==========

-- Check current database
SELECT current_database();

-- Check table sizes and row counts
SELECT 
    schemaname as schema,
    tablename as table,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size,
    n_live_tup as rows
FROM pg_stat_user_tables
WHERE schemaname IN ('aq_core', 'thierry_sandbox')
ORDER BY schemaname, tablename;

-- Check for recent data
SELECT 
    'PurpleAir' as source,
    COUNT(*) as last_hour_readings,
    MAX(time_stamp) as latest_reading
FROM aq_core.purpleair_readings
WHERE time_stamp > NOW() - INTERVAL '1 hour'
UNION ALL
SELECT 
    'REMA' as source,
    COUNT(*) as last_hour_readings,
    MAX(reading_time) as latest_reading
FROM aq_core.rema_readings
WHERE reading_time > NOW() - INTERVAL '1 hour';

-- ========== DATA EXPLORATION ==========

-- Latest readings summary
SELECT * FROM aq_core.purpleair_latest LIMIT 10;
SELECT * FROM aq_core.rema_latest LIMIT 10;

-- Current air quality status
SELECT 
    source,
    station_id,
    name,
    pm25,
    CASE 
        WHEN pm25 <= 12 THEN 'Good'
        WHEN pm25 <= 35.4 THEN 'Moderate'
        WHEN pm25 <= 55.4 THEN 'Unhealthy for Sensitive'
        WHEN pm25 <= 150.4 THEN 'Unhealthy'
        WHEN pm25 <= 250.4 THEN 'Very Unhealthy'
        ELSE 'Hazardous'
    END as air_quality,
    reading_time
FROM aq_core.all_pm25_readings
WHERE reading_time > NOW() - INTERVAL '1 hour'
ORDER BY pm25 DESC;

-- Hourly trends for last 24 hours
SELECT 
    source,
    station_id,
    TO_CHAR(hour, 'MM/DD HH24:00') as hour,
    ROUND(avg_pm25::numeric, 1) as pm25_avg,
    ROUND(avg_pm10::numeric, 1) as pm10_avg,
    reading_count
FROM aq_core.hourly_averages
WHERE hour > NOW() - INTERVAL '24 hours'
ORDER BY source, station_id, hour DESC;

-- ========== DATA QUALITY CHECKS ==========

-- Check for missing data (gaps > 1 hour)
WITH time_gaps AS (
    SELECT 
        sensor_id,
        time_stamp,
        LAG(time_stamp) OVER (PARTITION BY sensor_id ORDER BY time_stamp) as prev_time,
        time_stamp - LAG(time_stamp) OVER (PARTITION BY sensor_id ORDER BY time_stamp) as gap
    FROM aq_core.purpleair_readings
    WHERE time_stamp > NOW() - INTERVAL '24 hours'
)
SELECT 
    sensor_id,
    prev_time as gap_start,
    time_stamp as gap_end,
    gap
FROM time_gaps
WHERE gap > INTERVAL '1 hour'
ORDER BY gap DESC;

-- Check for outliers
SELECT 
    source,
    station_id,
    name,
    pm25,
    reading_time,
    'Possible outlier - very high' as flag
FROM aq_core.all_pm25_readings
WHERE pm25 > 500
  AND reading_time > NOW() - INTERVAL '24 hours'
UNION ALL
SELECT 
    source,
    station_id,
    name,
    pm25,
    reading_time,
    'Possible error - negative value' as flag
FROM aq_core.all_pm25_readings
WHERE pm25 < 0;

-- ========== ETL OPERATIONS ==========

-- Insert with conflict handling (example)
/*
INSERT INTO aq_core.purpleair_readings (
    sensor_id, name, time_stamp, pm2_5_atm, pm10_0_atm, 
    temperature, humidity, latitude, longitude
) VALUES (
    ?, ?, ?, ?, ?, ?, ?, ?, ?
) ON CONFLICT (sensor_id, time_stamp) 
DO UPDATE SET
    pm2_5_atm = EXCLUDED.pm2_5_atm,
    pm10_0_atm = EXCLUDED.pm10_0_atm,
    temperature = EXCLUDED.temperature,
    humidity = EXCLUDED.humidity;
*/

-- Clean old data (example - be careful!)
/*
DELETE FROM thierry_sandbox.purpleair_readings 
WHERE time_stamp < NOW() - INTERVAL '30 days';
*/

-- ========== USEFUL AGGREGATIONS ==========

-- Daily statistics
SELECT 
    source,
    DATE(reading_time) as date,
    COUNT(*) as readings,
    ROUND(AVG(pm25)::numeric, 1) as avg_pm25,
    ROUND(MIN(pm25)::numeric, 1) as min_pm25,
    ROUND(MAX(pm25)::numeric, 1) as max_pm25
FROM aq_core.all_pm25_readings
WHERE reading_time > NOW() - INTERVAL '7 days'
GROUP BY source, DATE(reading_time)
ORDER BY date DESC, source;

-- Station comparison
SELECT 
    station_id,
    name,
    COUNT(*) as readings_24h,
    ROUND(AVG(pm25)::numeric, 1) as avg_pm25_24h,
    ROUND(STDDEV(pm25)::numeric, 1) as stddev_pm25
FROM aq_core.all_pm25_readings
WHERE reading_time > NOW() - INTERVAL '24 hours'
GROUP BY station_id, name
ORDER BY avg_pm25_24h DESC;

-- ========== MAINTENANCE ==========

-- Update statistics
ANALYZE aq_core.purpleair_readings;
ANALYZE aq_core.rema_readings;

-- Check index usage
SELECT 
    schemaname,
    tablename,
    indexname,
    idx_scan as index_scans,
    idx_tup_read as tuples_read,
    idx_tup_fetch as tuples_fetched
FROM pg_stat_user_indexes
WHERE schemaname IN ('aq_core', 'thierry_sandbox')
ORDER BY idx_scan DESC;