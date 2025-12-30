"""
响应生成子模块
Response Generation Submodule

本模块提供三层响应生成策略的实现。
This module provides three-tier response generation strategy implementations.

Reference:
    - PRD §0.3: 混合响应策略
    - MOD-AI.md §3.4: ResponseGenerator

Exports / 导出:
    - GeneratedResponse: 生成响应数据类 / Generated response dataclass
    - ResponseGenerator: 响应生成协调器 / Response generation coordinator
    - Tier1TemplateGenerator: Tier1 模板生成器 / Tier1 template generator
    - Tier2RuleGenerator: Tier2 规则生成器 / Tier2 rule generator
    - Tier3LLMGenerator: Tier3 LLM 生成器 / Tier3 LLM generator

Author: Rainze Team
Created: 2025-12-30
"""

from __future__ import annotations

from .strategy import GeneratedResponse, ResponseGenerator
from .tier1_template import Tier1TemplateGenerator
from .tier2_rule import Tier2RuleGenerator
from .tier3_llm import Tier3LLMGenerator

__all__: list[str] = [
    "GeneratedResponse",
    "ResponseGenerator",
    "Tier1TemplateGenerator",
    "Tier2RuleGenerator",
    "Tier3LLMGenerator",
]
