from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from stat_validation.contracts import build_design
from stat_validation.generator import synthetic_tables
from stat_validation.pipeline import run


@pytest.fixture
def tables():
    return synthetic_tables()


@pytest.fixture
def design(tables):
    return build_design(*tables)


@pytest.fixture(scope="session")
def completed_run(tmp_path_factory):
    destination = tmp_path_factory.mktemp("completed") / "statistics"
    run(destination)  # R is mandatory; never skip an unavailable implementation.
    return destination
