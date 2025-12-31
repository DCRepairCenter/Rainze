"""
记忆模块异常定义
Memory Module Exception Definitions

本模块定义记忆系统的所有自定义异常。
This module defines all custom exceptions for the memory system.

Reference:
    - MOD-Memory.md §6: 异常定义 / Exception Definitions

Author: Rainze Team
Created: 2025-12-30
"""

from __future__ import annotations


class MemoryError(Exception):
    """
    记忆模块基础异常
    Base exception for memory module
    """


class MemoryNotFoundError(MemoryError):
    """
    记忆不存在异常
    Memory not found exception
    """

    def __init__(self, memory_id: str) -> None:
        """
        初始化异常 / Initialize exception

        Args:
            memory_id: 未找到的记忆ID / Memory ID that was not found
        """
        self.memory_id = memory_id
        super().__init__(f"Memory not found: {memory_id}")


class RetrievalError(MemoryError):
    """
    检索失败异常
    Retrieval failure exception
    """

    def __init__(self, message: str, strategy: str = "unknown") -> None:
        """
        初始化异常 / Initialize exception

        Args:
            message: 错误信息 / Error message
            strategy: 检索策略 / Retrieval strategy
        """
        self.strategy = strategy
        super().__init__(f"Retrieval failed [{strategy}]: {message}")


class VectorizeError(MemoryError):
    """
    向量化失败异常
    Vectorization failure exception
    """

    def __init__(self, memory_id: str, reason: str) -> None:
        """
        初始化异常 / Initialize exception

        Args:
            memory_id: 记忆ID / Memory ID
            reason: 失败原因 / Failure reason
        """
        self.memory_id = memory_id
        self.reason = reason
        super().__init__(f"Vectorize failed for {memory_id}: {reason}")


class StorageError(MemoryError):
    """
    存储操作失败异常
    Storage operation failure exception
    """

    def __init__(self, operation: str, reason: str) -> None:
        """
        初始化异常 / Initialize exception

        Args:
            operation: 操作类型 / Operation type
            reason: 失败原因 / Failure reason
        """
        self.operation = operation
        self.reason = reason
        super().__init__(f"Storage {operation} failed: {reason}")


class MemoryQuotaExceededError(MemoryError):
    """
    记忆配额超限异常
    Memory quota exceeded exception
    """

    def __init__(self, current: int, max_allowed: int) -> None:
        """
        初始化异常 / Initialize exception

        Args:
            current: 当前数量 / Current count
            max_allowed: 最大允许数量 / Maximum allowed count
        """
        self.current = current
        self.max_allowed = max_allowed
        super().__init__(f"Memory quota exceeded: {current}/{max_allowed}")
