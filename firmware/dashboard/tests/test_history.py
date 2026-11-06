import asyncio
import csv
import importlib
from unittest.mock import patch

import pytest


@pytest.fixture
def api(tmp_path, monkeypatch):
    """Importa o app com o hardware mockado e os logs isolados em tmp_path."""
    monkeypatch.chdir(tmp_path)
    with patch("telemetrix.telemetrix.Telemetrix"):
        main = importlib.import_module("backend.main")
        main = importlib.reload(main)
    return main


def _write_rows(path, rows):
    with open(path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "timestamp",
                "p_main_w",
                "p_ref_w",
                "temp_c",
                "lux",
                "limit_home",
                "limit_end",
            ]
        )
        writer.writerows(rows)


def _history(api, **kwargs):
    return asyncio.run(api.get_telemetry_history(**kwargs))


def test_history_returns_empty_when_file_missing(api):
    import os

    os.remove(api.logger.telemetry_file)
    assert _history(api) == []


def test_history_parses_rows_and_applies_limit(api):
    _write_rows(
        api.logger.telemetry_file,
        [
            ["2026-01-01 10:00:00", "1.5", "2.0", "30.5", "800", "1", "1"],
            ["2026-01-01 10:01:00", "1.6", "2.1", "31.0", "810", "1", "0"],
            ["2026-01-01 10:02:00", "1.7", "2.2", "31.5", "820", "0", "1"],
        ],
    )

    rows = _history(api, limit=2)
    assert len(rows) == 2
    assert rows[0]["timestamp"] == "2026-01-01 10:01:00"
    assert rows[-1] == {
        "timestamp": "2026-01-01 10:02:00",
        "p_main_w": 1.7,
        "p_ref_w": 2.2,
        "temp_c": 31.5,
        "lux": 820.0,
        "limit_home": 0,
        "limit_end": 1,
    }


def test_history_tolerates_blank_and_invalid_fields(api):
    _write_rows(
        api.logger.telemetry_file,
        [["2026-01-01 10:00:00", "", "n/a", "", "", "", ""]],
    )

    assert _history(api) == [
        {
            "timestamp": "2026-01-01 10:00:00",
            "p_main_w": 0.0,
            "p_ref_w": 0.0,
            "temp_c": 0.0,
            "lux": 0.0,
            "limit_home": 1,
            "limit_end": 1,
        }
    ]
