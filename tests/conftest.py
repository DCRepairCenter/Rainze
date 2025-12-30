"""
测试包初始化
Test Package Initialization

pytest 配置和共享 fixtures。
pytest configuration and shared fixtures.
"""

from __future__ import annotations

import pytest
from pathlib import Path


@pytest.fixture
def config_dir(tmp_path: Path) -> Path:
    """
    提供临时配置目录
    Provides temporary config directory
    """
    config = tmp_path / "config"
    config.mkdir()
    return config


@pytest.fixture
def data_dir(tmp_path: Path) -> Path:
    """
    提供临时数据目录
    Provides temporary data directory
    """
    data = tmp_path / "data"
    data.mkdir()
    return data
