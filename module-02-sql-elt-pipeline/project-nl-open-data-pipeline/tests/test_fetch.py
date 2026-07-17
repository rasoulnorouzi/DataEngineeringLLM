"""Unit tests for the extract step: pure logic, no network, no database."""

from datetime import date

from pipeline.fetch import date_window, reshape_daily


def test_date_window_ends_yesterday():
    start, end = date_window(today=date(2026, 7, 17), days=7)
    assert end == date(2026, 7, 16)
    assert start == date(2026, 7, 10)
    assert (end - start).days == 6  # 7 days inclusive


def test_reshape_pairs_values_by_position(open_meteo_payload):
    records = reshape_daily(open_meteo_payload["daily"])

    assert len(records) == 3
    assert records[0] == {
        "obs_date": "2026-07-01",
        "temp_max": 22.4,
        "temp_min": 12.1,
        "precip_mm": 0.0,
    }


def test_reshape_keeps_null_values_for_raw_layer(open_meteo_payload):
    # Raw layer stores data as-received; nulls are filtered later, in staging SQL.
    records = reshape_daily(open_meteo_payload["daily"])
    assert records[2]["temp_max"] is None


def test_reshape_empty_input_gives_empty_list():
    empty = {
        "time": [],
        "temperature_2m_max": [],
        "temperature_2m_min": [],
        "precipitation_sum": [],
    }
    assert reshape_daily(empty) == []
