"""
可观测性模块 - 追踪与指标
Observability Module - Tracing and Metrics

本模块提供统一的可观测性能力：
This module provides unified observability capabilities:

- Tracer: 分布式追踪 / Distributed tracing
- Metrics: 性能指标收集 / Performance metrics collection

Usage / 使用方式:
    from rainze.core.observability import Tracer
    
    with Tracer.span("memory.search", {"query": q}) as span:
        result = await search(q)
        span.log("found", {"count": len(result)})

Reference:
    - PRD §0.11-0.11a: 可观测性系统
    - MOD-Core.md §11.5: Tracer

Author: Rainze Team
Created: 2025-12-30
"""

from __future__ import annotations

# TODO: 实现后取消注释 / Uncomment after implementation
# from .tracer import Tracer, TraceSpan
# from .metrics import MetricsCollector

__all__: list[str] = [
    # "Tracer",
    # "TraceSpan",
    # "MetricsCollector",
]
