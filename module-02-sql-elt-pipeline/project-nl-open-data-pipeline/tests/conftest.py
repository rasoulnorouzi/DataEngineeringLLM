import json
from pathlib import Path

import pytest

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def open_meteo_payload() -> dict:
    """A saved real-shaped API response (never call the live API in unit tests)."""
    return json.loads((FIXTURES / "open_meteo_sample.json").read_text(encoding="utf-8"))
