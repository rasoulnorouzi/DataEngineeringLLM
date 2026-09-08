-- Minimal warehouse fixture for CI and for anyone who wants to run the API
-- without first running the whole Module 2 pipeline.
--
-- It creates the same two objects the pipeline produces, with a handful of
-- rows, so the integration tests have real SQL to execute.

CREATE SCHEMA IF NOT EXISTS staging;
CREATE SCHEMA IF NOT EXISTS marts;

DROP TABLE IF EXISTS staging.weather_clean;
CREATE TABLE staging.weather_clean (
    city        TEXT    NOT NULL,
    obs_date    DATE    NOT NULL,
    temp_max_c  NUMERIC,
    temp_min_c  NUMERIC,
    precip_mm   NUMERIC,
    PRIMARY KEY (city, obs_date)
);

INSERT INTO staging.weather_clean (city, obs_date, temp_max_c, temp_min_c, precip_mm) VALUES
('De Bilt',   '2026-08-31', 22.1, 12.4, 0.0),
('De Bilt',   '2026-09-01', 21.4, 12.1, 0.0),
('De Bilt',   '2026-09-02', 19.8, 11.3, 4.2),
('De Bilt',   '2026-09-03', 18.2, 10.9, 7.5),
('Amsterdam', '2026-08-31', 21.0, 13.4, 0.2),
('Amsterdam', '2026-09-01', 20.1, 13.0, 1.1),
('Amsterdam', '2026-09-02', 18.9, 12.2, 3.0),
('Rotterdam', '2026-09-01', 20.6, 12.8, 0.9),
('Rotterdam', '2026-09-02', 19.1, 11.9, 2.4);

CREATE INDEX idx_weather_clean_city_date ON staging.weather_clean (city, obs_date);

DROP TABLE IF EXISTS marts.weather_weekly;
CREATE TABLE marts.weather_weekly AS
WITH weekly AS (
    SELECT
        city,
        date_trunc('week', obs_date)::date  AS week_start,
        round(avg(temp_max_c), 1)           AS avg_temp_max_c,
        round(avg(temp_min_c), 1)           AS avg_temp_min_c,
        round(sum(precip_mm), 1)            AS total_precip_mm,
        count(*)                            AS days_observed
    FROM staging.weather_clean
    GROUP BY city, date_trunc('week', obs_date)
)
SELECT
    city,
    week_start,
    avg_temp_max_c,
    avg_temp_min_c,
    total_precip_mm,
    days_observed,
    round(
        avg_temp_max_c - LAG(avg_temp_max_c) OVER (PARTITION BY city ORDER BY week_start),
        1
    ) AS temp_change_vs_prev_week_c
FROM weekly
ORDER BY city, week_start;
