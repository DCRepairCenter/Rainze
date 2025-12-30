"""
工作记忆层
Working Memory Layer

本模块实现工作记忆（Layer 2），包括对话历史管理。
This module implements working memory (Layer 2), including conversation history.

Reference:
    - MOD-Memory.md §1.1: Layer 2 (Working Memory)
    - MOD-Memory.md §3.1: get_conversation_history, add_conversation_turn

Author: Rainze Team
Created: 2025-12-30
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Deque, Dict, List, Literal, Optional


@dataclass
class ConversationTurn:
    """
    对话轮次
    Conversation turn

    代表一轮对话（用户或助手的一条消息）。
    Represents a single turn in conversation (user or assistant message).

    Attributes:
        role: 角色 / Role ("user" | "assistant" | "system")
        content: 内容 / Content
        timestamp: 时间戳 / Timestamp
        metadata: 元数据 / Metadata
    """

    role: Literal["user", "assistant", "system"]
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典格式
        Convert to dictionary format

        Returns:
            对话轮次的字典表示 / Dictionary representation
        """
        return {
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ConversationTurn":
        """
        从字典创建对话轮次
        Create conversation turn from dictionary

        Args:
            data: 对话轮次字典 / Conversation turn dictionary

        Returns:
            对话轮次实例 / ConversationTurn instance
        """
        timestamp = data.get("timestamp")
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp)
        elif timestamp is None:
            timestamp = datetime.now()

        return cls(
            role=data["role"],
            content=data["content"],
            timestamp=timestamp,
            metadata=data.get("metadata", {}),
        )


class WorkingMemory:
    """
    工作记忆
    Working memory

    管理会话级的对话历史和实时状态。
    Manages session-level conversation history and real-time state.

    这是 Layer 2 记忆层的实现，内容仅存在于内存中，会话结束后清空。
    This is the Layer 2 memory implementation, content exists only in memory.

    Attributes:
        max_turns: 最大对话轮次 / Maximum conversation turns
        _history: 对话历史队列 / Conversation history queue
        _context: 实时上下文 / Real-time context

    Example:
        >>> wm = WorkingMemory(max_turns=10)
        >>> wm.add_turn("user", "你好")
        >>> wm.add_turn("assistant", "你好呀~")
        >>> history = wm.get_history()
        >>> print(len(history))
        2
    """

    def __init__(self, max_turns: int = 20) -> None:
        """
        初始化工作记忆
        Initialize working memory

        Args:
            max_turns: 最大保留的对话轮次 / Maximum turns to keep
        """
        self.max_turns = max_turns
        self._history: Deque[ConversationTurn] = deque(maxlen=max_turns)
        self._context: Dict[str, Any] = {}

    def add_turn(
        self,
        role: Literal["user", "assistant", "system"],
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ConversationTurn:
        """
        添加对话轮次
        Add conversation turn

        Args:
            role: 角色 / Role
            content: 内容 / Content
            metadata: 元数据 / Metadata

        Returns:
            创建的对话轮次 / Created conversation turn
        """
        turn = ConversationTurn(
            role=role,
            content=content,
            metadata=metadata or {},
        )
        self._history.append(turn)
        return turn

    def get_history(
        self,
        max_turns: Optional[int] = None,
    ) -> List[ConversationTurn]:
        """
        获取对话历史
        Get conversation history

        Args:
            max_turns: 最大返回轮次，None 则返回全部 / Max turns, None for all

        Returns:
            对话历史列表 / Conversation history list
        """
        history_list = list(self._history)

        if max_turns is not None and max_turns < len(history_list):
            # 返回最近的 N 轮 / Return most recent N turns
            return history_list[-max_turns:]

        return history_list

    def get_history_for_prompt(
        self,
        max_turns: Optional[int] = None,
    ) -> List[Dict[str, str]]:
        """
        获取适用于 LLM Prompt 的对话历史
        Get conversation history for LLM prompt

        Args:
            max_turns: 最大返回轮次 / Max turns

        Returns:
            对话历史字典列表 / Conversation history dict list
        """
        history = self.get_history(max_turns)
        return [{"role": turn.role, "content": turn.content} for turn in history]

    def clear(self) -> None:
        """
        清空对话历史
        Clear conversation history
        """
        self._history.clear()
        self._context.clear()

    def set_context(self, key: str, value: Any) -> None:
        """
        设置实时上下文
        Set real-time context

        Args:
            key: 上下文键 / Context key
            value: 上下文值 / Context value
        """
        self._context[key] = value

    def get_context(self, key: str, default: Any = None) -> Any:
        """
        获取实时上下文
        Get real-time context

        Args:
            key: 上下文键 / Context key
            default: 默认值 / Default value

        Returns:
            上下文值 / Context value
        """
        return self._context.get(key, default)

    def remove_context(self, key: str) -> None:
        """
        移除实时上下文
        Remove real-time context

        Args:
            key: 上下文键 / Context key
        """
        self._context.pop(key, None)

    @property
    def turn_count(self) -> int:
        """
        当前对话轮次数
        Current turn count

        Returns:
            轮次数量 / Turn count
        """
        return len(self._history)

    @property
    def is_empty(self) -> bool:
        """
        对话历史是否为空
        Whether conversation history is empty

        Returns:
            是否为空 / Whether empty
        """
        return len(self._history) == 0

    def get_last_user_message(self) -> Optional[str]:
        """
        获取最后一条用户消息
        Get last user message

        Returns:
            最后一条用户消息内容，不存在返回 None / Last user message or None
        """
        for turn in reversed(self._history):
            if turn.role == "user":
                return turn.content
        return None

    def get_last_assistant_message(self) -> Optional[str]:
        """
        获取最后一条助手消息
        Get last assistant message

        Returns:
            最后一条助手消息内容，不存在返回 None / Last assistant message or None
        """
        for turn in reversed(self._history):
            if turn.role == "assistant":
                return turn.content
        return None

    def estimate_token_count(self, chars_per_token: float = 2.0) -> int:
        """
        估算对话历史的 Token 数量
        Estimate token count of conversation history

        Args:
            chars_per_token: 每个 Token 的平均字符数 / Chars per token

        Returns:
            估算的 Token 数量 / Estimated token count

        Note:
            中文大约 1.5-2 字符/token，英文大约 4 字符/token。
            Chinese: ~1.5-2 chars/token, English: ~4 chars/token.
        """
        total_chars = sum(len(turn.content) for turn in self._history)
        return int(total_chars / chars_per_token)

    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典格式
        Convert to dictionary format

        Returns:
            工作记忆的字典表示 / Dictionary representation
        """
        return {
            "max_turns": self.max_turns,
            "history": [turn.to_dict() for turn in self._history],
            "context": self._context,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WorkingMemory":
        """
        从字典创建工作记忆
        Create working memory from dictionary

        Args:
            data: 工作记忆字典 / Working memory dictionary

        Returns:
            工作记忆实例 / WorkingMemory instance
        """
        wm = cls(max_turns=data.get("max_turns", 20))

        for turn_data in data.get("history", []):
            turn = ConversationTurn.from_dict(turn_data)
            wm._history.append(turn)

        wm._context = data.get("context", {})

        return wm
