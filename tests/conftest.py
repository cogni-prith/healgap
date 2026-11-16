from __future__ import annotations

from pathlib import Path

import pytest

from healgap.env.datagen import DataConfig, build
from healgap.env.dataset import Dataset, load_dataset

REPO = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="session")
def cfg() -> DataConfig:
    return DataConfig.load(REPO / "configs" / "data.yaml")


@pytest.fixture(scope="session")
def ds(cfg: DataConfig, tmp_path_factory: pytest.TempPathFactory) -> Dataset:
    root = tmp_path_factory.mktemp("data")
    build(cfg, "smoke", root)
    return load_dataset("smoke", root)
