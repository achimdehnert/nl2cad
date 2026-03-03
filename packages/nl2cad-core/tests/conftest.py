"""nl2cad-core test configuration and shared fixtures."""

from __future__ import annotations

from pathlib import Path

import pytest

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def fixture_ifc_simple() -> Path:
    """Minimale IFC2X3-Testdatei."""
    return FIXTURES_DIR / "simple.ifc"


@pytest.fixture
def fixture_dxf_simple() -> Path:
    """Minimale DXF-Testdatei."""
    return FIXTURES_DIR / "simple.dxf"


@pytest.fixture
def fixtures_dir() -> Path:
    """Verzeichnis mit allen Test-Fixtures."""
    return FIXTURES_DIR
