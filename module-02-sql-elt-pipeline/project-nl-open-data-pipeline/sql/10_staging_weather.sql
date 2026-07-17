-- Staging layer: typed, cleaned rows built from the raw evidence locker.
-- Rebuilt from scratch on every run (idempotent by construction).

CREATE SCHEMA IF NOT EXISTS staging;

DROP TABLE IF EXISTS staging.weather_clean;

CREATE TABLE staging.weather_clean AS
SELECT
    city,
    obs_date,
    (payload ->> 'temp_max')::numeric   AS temp_max_c,
    (payload ->> 'temp_min')::numeric   AS temp_min_c,
    (payload ->> 'precip_mm')::numeric  AS precip_mm
FROM raw.weather_daily
-- Data quality gate: the archive sometimes lags a day; drop incomplete rows.
WHERE payload ->> 'temp_max' IS NOT NULL;

-- Downstream marts filter and join on these; index after load (Day 5!).
CREATE INDEX idx_weather_clean_city_date ON staging.weather_clean (city, obs_date);
