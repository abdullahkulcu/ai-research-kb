from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
EXAMPLES_ROOT = REPO_ROOT / "examples"
CLUSTER = EXAMPLES_ROOT / "rag-pipeline-degerlendirmesi"


@pytest.fixture
def examples_root() -> Path:
    return EXAMPLES_ROOT


@pytest.fixture
def cluster_dir() -> Path:
    return CLUSTER
