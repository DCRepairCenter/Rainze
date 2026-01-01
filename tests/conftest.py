"""
测试包初始化
Test Package Initialization

pytest 配置和共享 fixtures。
pytest configuration and shared fixtures.
"""

from __future__ import annotations

import os
import pytest
from pathlib import Path

# 设置环境变量避免 FAISS 多线程冲突
# Set environment variables to avoid FAISS multi-threading conflicts
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["OPENBLAS_NUM_THREADS"] = "1"


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
