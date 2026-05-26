"""Shared fixtures for rotation tests."""

from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from transform import DEFAULT_SHUFFLE_SEED, load_manifest


@pytest.fixture
def manifest() -> dict:
    return load_manifest()


@pytest.fixture
def characters(manifest: dict) -> dict:
    return manifest["characters"]


@pytest.fixture
def shuffle_seed() -> str:
    return DEFAULT_SHUFFLE_SEED


@pytest.fixture
def rotation_start() -> date:
    return date(2026, 1, 1)
