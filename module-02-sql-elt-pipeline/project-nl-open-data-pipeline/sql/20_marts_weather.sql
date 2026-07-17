-- Marts layer: answer-shaped tables for consumers (dashboards, notebooks,
-- and - from Module 3 on - the insight-api service).
-- Rebuilt from staging on every run.

CREATE SCHEMA IF NOT EXISTS marts;

DROP TABLE IF EXISTS marts.weather_weekly;

CREATE TABLE marts.weather_weekly AS
WITH weekly AS (
    -- Day 3 skills: GROUP BY over a derived week column
    SELECT
        city,
        date_trunc('week', obs_date)::date        AS week_start,
        round(avg(temp_max_c), 1)                 AS avg_temp_max_c,
        round(avg(temp_min_c), 1)                 AS avg_temp_min_c,
        round(sum(precip_mm), 1)                  AS total_precip_mm,
        count(*)                                  AS days_observed
    FROM staging.weather_clean
    GROUP BY city, date_trunc('week', obs_date)
)
-- Day 4 skills: LAG for week-over-week change
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
