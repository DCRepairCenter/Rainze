"""
场景分类契约
Scene Classification Contract

本模块定义场景类型和响应层级的映射规则。
This module defines scene types and response tier mappings.

Reference:
    - PRD §0.3: 混合响应策略
    - MOD-Core.md §11.2: SceneType & ResponseTier

Author: Rainze Team
Created: 2025-12-30
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
from typing import Dict, List, Optional


class SceneType(Enum):
    """
    场景类型枚举
    Scene type enumeration

    所有模块必须使用此定义，禁止重复定义。
    All modules MUST use this, NO duplicates allowed.
    """

    SIMPLE = auto()  # 简单交互 -> Tier1 / Simple interaction
    MEDIUM = auto()  # 中等复杂度 -> Tier2 / Medium complexity
    COMPLEX = auto()  # 复杂场景 -> Tier3 / Complex scenario


class ResponseTier(Enum):
    """
    响应层级枚举
    Response tier enumeration
    """

    TIER1_TEMPLATE = 1  # 模板响应 / Template response (<50ms)
    TIER2_RULE = 2  # 规则生成 / Rule-based generation (<100ms)
    TIER3_LLM = 3  # LLM 生成 / LLM generation (<3s)


@dataclass
class SceneTierMapping:
    """
    场景-Tier 映射配置
    Scene-Tier mapping configuration

    Attributes:
        scene_type: 场景类型 / Scene type
        default_tier: 默认响应层级 / Default response tier
        allow_override: 是否允许覆盖 / Whether override is allowed
        fallback_chain: 降级链 / Fallback chain
        timeout_ms: 超时时间（毫秒）/ Timeout in ms
        memory_retrieval: 记忆检索策略 / Memory retrieval strategy
    """

    scene_type: SceneType
    default_tier: ResponseTier
    allow_override: bool = True
    fallback_chain: List[ResponseTier] = field(default_factory=list)
    timeout_ms: int = 3000
    memory_retrieval: str = "none"  # "none" | "facts_summary" | "full"


# 模块级缓存 / Module-level cache
_scene_tier_cache: Optional[Dict[str, SceneTierMapping]] = None


def get_scene_tier_table(
    config_path: Optional[Path] = None,
) -> Dict[str, SceneTierMapping]:
    """
    获取场景-Tier 中央映射表
    Get scene-tier central mapping table

    Args:
        config_path: 配置文件路径，默认 config/scene_tier_mapping.json
                     Config file path, defaults to config/scene_tier_mapping.json

    Returns:
        场景ID到映射配置的字典 / Scene ID to mapping config dict

    Raises:
        FileNotFoundError: 配置文件不存在 / Config file not found
    """
    global _scene_tier_cache
    if _scene_tier_cache is not None:
        return _scene_tier_cache

    if config_path is None:
        config_path = Path("./config/scene_tier_mapping.json")

    # 如果配置文件不存在，使用默认配置
    # If config file doesn't exist, use default config
    if not config_path.exists():
        _scene_tier_cache = _get_default_mappings()
        return _scene_tier_cache

    with open(config_path, encoding="utf-8") as f:
        raw_data = json.load(f)

    _scene_tier_cache = {}
    # 跳过 JSON Schema 元数据字段 / Skip JSON Schema metadata fields
    metadata_keys = {"$schema", "title", "description"}
    for scene_id, mapping in raw_data.items():
        if scene_id in metadata_keys:
            continue
        if not isinstance(mapping, dict):
            continue
        _scene_tier_cache[scene_id] = SceneTierMapping(
            scene_type=SceneType[mapping["scene_type"]],
            default_tier=ResponseTier[mapping["default_tier"]],
            timeout_ms=mapping.get("timeout_ms", 3000),
            memory_retrieval=mapping.get("memory_retrieval", "none"),
            fallback_chain=[ResponseTier[t] for t in mapping.get("fallback_chain", [])],
            allow_override=mapping.get("allow_override", True),
        )

    return _scene_tier_cache


def invalidate_scene_tier_cache() -> None:
    """
    使缓存失效（配置热重载时调用）
    Invalidate cache (called when config hot-reload)
    """
    global _scene_tier_cache
    _scene_tier_cache = None


def _get_default_mappings() -> Dict[str, SceneTierMapping]:
    """
    获取默认场景映射（备用）
    Get default scene mappings (fallback)
    """
    return {
        "click": SceneTierMapping(
            scene_type=SceneType.SIMPLE,
            default_tier=ResponseTier.TIER1_TEMPLATE,
            timeout_ms=50,
            memory_retrieval="none",
            fallback_chain=[],
        ),
        "drag": SceneTierMapping(
            scene_type=SceneType.SIMPLE,
            default_tier=ResponseTier.TIER1_TEMPLATE,
            timeout_ms=50,
            memory_retrieval="none",
            fallback_chain=[],
        ),
        "hourly_chime": SceneTierMapping(
            scene_type=SceneType.MEDIUM,
            default_tier=ResponseTier.TIER2_RULE,
            timeout_ms=100,
            memory_retrieval="facts_summary",
            fallback_chain=[ResponseTier.TIER1_TEMPLATE],
        ),
        "system_warning": SceneTierMapping(
            scene_type=SceneType.MEDIUM,
            default_tier=ResponseTier.TIER2_RULE,
            timeout_ms=100,
            memory_retrieval="none",
            fallback_chain=[ResponseTier.TIER1_TEMPLATE],
        ),
        "conversation": SceneTierMapping(
            scene_type=SceneType.COMPLEX,
            default_tier=ResponseTier.TIER3_LLM,
            timeout_ms=3000,
            memory_retrieval="full",
            fallback_chain=[ResponseTier.TIER2_RULE, ResponseTier.TIER1_TEMPLATE],
        ),
        "game_interaction": SceneTierMapping(
            scene_type=SceneType.SIMPLE,
            default_tier=ResponseTier.TIER1_TEMPLATE,
            timeout_ms=50,
            memory_retrieval="none",
            fallback_chain=[],
        ),
    }
