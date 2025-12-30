# MOD-Agent: Agent自主循环与行为计划模块

> **模块ID**: `rainze.agent`
> **版本**: v1.1.0
> **优先级**: P1 (Core Experience)
> **层级**: Business Layer
> **依赖**: Core (含contracts), AI, Memory, State, RustCore
> **关联PRD**: PRD-Rainze.md §0.5a, §0.7, §0.8, §0.15

---

## 1. 模块概述

### 1.1 职责定义

Agent模块是Rainze的"大脑"，负责：

- **统一上下文管理 (UCM)**: 所有交互的单一入口，确保状态一致性
- **Agent自主循环**: 周期性感知-评估-决策-执行循环
- **行为计划系统**: 轻量级短期意图规划
- **场景分类与路由**: 判断交互类型并路由到正确处理器
- **对话会话管理**: 多轮对话上下文维护

### 1.2 设计原则

| 原则 | 说明 |
|------|------|
| **Workflow优先** | 单步操作用Workflow，多步推理才用Agent |
| **统一入口** | 所有交互必须经过ContextManager |
| **最小侵入** | 主动行为可配置，默认低频 |
| **可观测** | 每个Phase记录span到追踪系统 |

### 1.3 技术选型

| 技术 | 选型 | 理由 |
|------|------|------|
| **调度器** | asyncio + APScheduler | 轻量级异步定时任务 |
| **状态机** | transitions库 | 成熟的Python FSM实现 |
| **意图识别** | 规则优先 + LLM兜底 | 低延迟，高准确率 |

---

## 2. 目录结构

```
src/rainze/agent/
├── __init__.py
├── context_manager.py      # 统一上下文管理器 (UCM)
├── agent_loop.py           # Agent自主循环
├── behavior_planner.py     # 行为计划系统
├── scene_classifier.py     # 场景分类器
├── intent_recognizer.py    # 意图识别器
├── conversation.py         # 对话会话管理
├── proactive/              # 主动行为
│   ├── __init__.py
│   ├── registry.py         # 主动行为注册表
│   ├── triggers.py         # 触发器定义
│   └── behaviors.py        # 行为实现
├── execution/              # 执行策略
│   ├── __init__.py
│   ├── workflow.py         # Workflow模式执行
│   └── react.py            # ReAct模式执行
└── models/
    ├── __init__.py
    ├── interaction.py      # 交互模型
    ├── intention.py        # 意图模型
    └── plan.py             # 计划模型
```

---

## 3. 核心类设计

### 3.1 UnifiedContextManager (统一上下文管理器)

```python
# src/rainze/agent/context_manager.py

from __future__ import annotations
from typing import TYPE_CHECKING, Optional, Dict, Any, Callable, Awaitable
from dataclasses import dataclass, field
from datetime import datetime

# ⭐ 从core.contracts导入统一类型定义
from rainze.core.contracts.scene import SceneType, ResponseTier, get_scene_tier_table
from rainze.core.contracts.interaction import (
    InteractionSource,
    InteractionRequest,
    InteractionResponse
)
from rainze.core.contracts.emotion import EmotionTag
from rainze.core.observability import Tracer

if TYPE_CHECKING:
    from rainze.ai import ResponseResult
    from rainze.memory import MemoryManager
    from rainze.state import StateManager


# ⚠️ InteractionType 已移至 core.contracts.interaction.InteractionSource
# 此处保留别名以兼容
InteractionType = InteractionSource


@dataclass
class InteractionContext:
    """交互上下文数据类
    
    ⭐ 更新: 使用统一的SceneType和EmotionTag
    """
    interaction_id: str
    interaction_type: InteractionSource  # 使用统一类型
    scene_type: SceneType                # 使用统一类型
    timestamp: datetime
    source: str                          # 来源标识
    trace_id: Optional[str] = None       # ⭐新增: 可观测性追踪
    user_input: Optional[str] = None     # 用户输入
    event_data: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # 处理过程中填充
    intent: Optional[str] = None
    confidence: float = 0.0
    memory_context: Optional[Dict[str, Any]] = None
    state_snapshot: Optional[Dict[str, Any]] = None


@dataclass
class InteractionResult:
    """交互结果数据类
    
    ⭐ 更新: 使用统一的EmotionTag
    """
    success: bool
    response_text: Optional[str] = None
    emotion: Optional[EmotionTag] = None  # 使用统一类型
    action_hint: Optional[str] = None
    state_changes: Dict[str, Any] = field(default_factory=dict)
    memory_written: bool = False
    trace_spans: list[str] = field(default_factory=list)  # ⭐新增
    error: Optional[str] = None


class UnifiedContextManager:
    """
    统一上下文管理器 (UCM)
    
    ⭐ 核心设计: 所有用户交互的**唯一入口点**
    
    确保：
    - 状态一致性：任何模块的状态变化都实时同步
    - 记忆完整性：游戏/插件/工具产生的交互同样写入记忆
    - 上下文共享：所有模块共享同一套用户画像和情绪状态
    - 可观测性：每个交互自动生成trace_id并记录span
    
    ⚠️ 禁止其他模块绕过UCM直接处理用户交互！
    
    Attributes:
        _memory_manager: 记忆管理器引用
        _state_manager: 状态管理器引用
        _scene_classifier: 场景分类器 (从AI模块获取)
        _intent_recognizer: 意图识别器
        _tier_table: 场景-Tier映射表 (从core.contracts加载)
        _handlers: 交互类型处理器映射
    """
    
    def __init__(
        self,
        memory_manager: MemoryManager,
        state_manager: StateManager,
        scene_classifier: "SceneClassifier",  # 从AI模块导入
        intent_recognizer: "IntentRecognizer",
    ) -> None:
        """
        初始化统一上下文管理器。
        
        Args:
            memory_manager: 记忆管理器实例
            state_manager: 状态管理器实例
            scene_classifier: 场景分类器实例
            intent_recognizer: 意图识别器实例
        """
        ...
    
    async def process_interaction(
        self,
        request: InteractionRequest
    ) -> InteractionResponse:
        """
        处理交互的统一入口。
        
        ⭐ 所有类型的交互（对话、游戏、工具、插件、系统事件）
        都必须通过此方法处理，确保状态和记忆的一致性。
        
        Args:
            request: 统一交互请求 (从core.contracts导入)
            
        Returns:
            InteractionResponse: 统一响应格式
            
        Raises:
            InteractionError: 交互处理失败时抛出
            
        Example:
            >>> request = InteractionRequest(
            ...     request_id=uuid4().hex,
            ...     source=InteractionSource.CHAT_INPUT,
            ...     timestamp=datetime.now(),
            ...     payload={"text": "今天天气怎么样？"}
            ... )
            >>> response = await ucm.process_interaction(request)
            >>> print(response.response_text)
        """
        with Tracer.span("ucm.process", {"source": request.source.name}) as span:
            # 1. 场景分类
            scene = await self._classify_scene(request)
            span.log("classified", {"scene": scene.scene_id})
            
            # 2. 获取Tier和降级链
            tier = scene.suggested_tier
            fallback_chain = scene.mapping.fallback_chain
            
            # 3. 路由到处理器
            result = await self._route_to_handler(request, scene, tier)
            
            # 4. 更新状态和记忆
            await self._post_process(request, result)
            
            return result
    
    # 保留旧接口以兼容
    async def process_interaction_legacy(
        self,
        interaction_type: InteractionSource,
        source: str,
        user_input: Optional[str] = None,
        event_data: Optional[Dict[str, Any]] = None,
    ) -> InteractionResult:
        """
        [兼容接口] 处理交互的旧入口。
        
        ⚠️ 已废弃，请使用 process_interaction(InteractionRequest)
        """
        ...
    
    async def _classify_scene(
        self, 
        request: InteractionRequest
    ) -> "ClassifiedScene":
        """分类场景并获取Tier配置"""
        ...
    
    async def _build_context(
        self,
        interaction_type: InteractionType,
        source: str,
        user_input: Optional[str],
        event_data: Optional[Dict[str, Any]],
    ) -> InteractionContext:
        """
        构建交互上下文。
        
        Args:
            interaction_type: 交互类型
            source: 来源标识
            user_input: 用户输入
            event_data: 事件数据
            
        Returns:
            InteractionContext: 完整的交互上下文
        """
        ...
    
    async def _classify_and_route(
        self,
        context: InteractionContext,
    ) -> InteractionResult:
        """
        分类场景并路由到对应处理器。
        
        Args:
            context: 交互上下文
            
        Returns:
            InteractionResult: 处理结果
        """
        ...
    
    async def _post_process(
        self,
        context: InteractionContext,
        result: InteractionResult,
    ) -> None:
        """
        后处理：记忆写入、状态更新、事件广播。
        
        Args:
            context: 交互上下文
            result: 交互结果
        """
        ...
    
    def register_handler(
        self,
        interaction_type: InteractionType,
        handler: Callable[[InteractionContext], Awaitable[InteractionResult]],
    ) -> None:
        """
        注册交互类型处理器。
        
        Args:
            interaction_type: 交互类型
            handler: 异步处理函数
        """
        ...


class MemoryWritePolicy(Enum):
    """记忆写入策略"""
    FULL = auto()           # 完整记录
    SUMMARY = auto()        # 摘要记录
    RESULT_ONLY = auto()    # 仅结果
    NONE = auto()           # 不记录


@dataclass
class MemoryWriteConfig:
    """记忆写入配置"""
    policy: MemoryWritePolicy
    default_importance: float
    aggregate_enabled: bool = False
    aggregate_template: Optional[str] = None


# 各交互类型的默认记忆写入策略
DEFAULT_MEMORY_POLICIES: Dict[InteractionType, MemoryWriteConfig] = {
    InteractionType.CONVERSATION: MemoryWriteConfig(
        policy=MemoryWritePolicy.FULL,
        default_importance=0.6,
    ),
    InteractionType.GAME_INTERACTION: MemoryWriteConfig(
        policy=MemoryWritePolicy.RESULT_ONLY,
        default_importance=0.3,
        aggregate_enabled=True,
        aggregate_template="今天和主人玩了{count}局{game_name}，赢了{win_count}局",
    ),
    InteractionType.TOOL_EXECUTION: MemoryWriteConfig(
        policy=MemoryWritePolicy.SUMMARY,
        default_importance=0.5,
    ),
    InteractionType.PLUGIN_ACTION: MemoryWriteConfig(
        policy=MemoryWritePolicy.SUMMARY,
        default_importance=0.4,
    ),
    InteractionType.SYSTEM_EVENT: MemoryWriteConfig(
        policy=MemoryWritePolicy.SUMMARY,
        default_importance=0.5,
    ),
    InteractionType.PASSIVE_TRIGGER: MemoryWriteConfig(
        policy=MemoryWritePolicy.NONE,
        default_importance=0.0,
    ),
}
```

### 3.2 AgentLoop (Agent自主循环)

```python
# src/rainze/agent/agent_loop.py

from __future__ import annotations
from typing import TYPE_CHECKING, Optional, List, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum, auto
import asyncio

if TYPE_CHECKING:
    from rainze.agent import UnifiedContextManager
    from rainze.state import StateManager


class LoopPhase(Enum):
    """循环阶段"""
    PERCEPTION = auto()       # 感知
    EVENT_EVALUATION = auto() # 事件评估
    PRIORITY_RESOLUTION = auto()  # 优先级决策
    EXECUTION = auto()        # 执行
    MEMORY_UPDATE = auto()    # 记忆更新


class ExecutionMode(Enum):
    """执行模式"""
    WORKFLOW = auto()   # 单步执行，不调用LLM
    AGENT = auto()      # 多步推理，需要LLM


class Priority(Enum):
    """优先级等级"""
    CRITICAL = 100   # 立即执行，中断其他
    HIGH = 80        # 优先执行
    MEDIUM = 50      # 正常队列
    LOW = 20         # 空闲时执行
    BACKGROUND = 0   # 后台静默


@dataclass
class PerceptionContext:
    """感知上下文"""
    timestamp: datetime
    time_since_last_interaction: timedelta
    current_hour: int
    is_night_mode: bool
    
    # 环境感知
    cpu_usage: float
    memory_usage: float
    is_fullscreen: bool
    is_meeting: bool
    weather: Optional[str] = None
    
    # 状态感知
    mood: str
    energy: float
    hunger: float
    affinity: int
    
    # 记忆感知
    pending_memories: int
    has_important_date: bool = False


@dataclass
class CandidateEvent:
    """候选事件"""
    event_type: str
    priority: Priority
    trigger_reason: str
    cooldown_key: str
    execution_mode: ExecutionMode
    config_key: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ExecutionResult:
    """执行结果"""
    success: bool
    event_type: str
    response: Optional[str] = None
    duration_ms: int = 0
    error: Optional[str] = None


class AgentLoop:
    """
    Agent自主循环
    
    周期性执行感知-评估-决策-执行循环，管理桌宠的主动行为。
    
    循环结构：
    1. Perception (感知): 收集时间、环境、状态、记忆信息
    2. Event Evaluation (事件评估): 遍历触发器，生成候选事件
    3. Priority Resolution (优先级决策): 排序、冷却检查、频率限制
    4. Execution (执行): 根据复杂度选择Workflow或Agent模式
    5. Memory Update (记忆更新): 记录行为、更新统计
    
    Attributes:
        _context_manager: 统一上下文管理器
        _state_manager: 状态管理器
        _behavior_registry: 主动行为注册表
        _cooldown_tracker: 冷却时间追踪器
        _is_running: 循环运行状态
        _loop_interval: 循环间隔（秒）
    """
    
    def __init__(
        self,
        context_manager: UnifiedContextManager,
        state_manager: StateManager,
        behavior_registry: ProactiveBehaviorRegistry,
        loop_interval: int = 60,
    ) -> None:
        """
        初始化Agent循环。
        
        Args:
            context_manager: 统一上下文管理器
            state_manager: 状态管理器
            behavior_registry: 主动行为注册表
            loop_interval: 循环间隔（秒），默认60秒
        """
        ...
    
    async def start(self) -> None:
        """
        启动Agent循环。
        
        开始周期性执行感知-评估-决策-执行循环。
        
        Raises:
            AgentLoopError: 启动失败时抛出
        """
        ...
    
    async def stop(self) -> None:
        """
        停止Agent循环。
        
        优雅关闭，等待当前循环完成。
        """
        ...
    
    async def _run_loop(self) -> None:
        """
        执行单次循环。
        
        完整的5阶段循环，每个阶段都记录到追踪系统。
        """
        ...
    
    async def _phase_perception(self) -> PerceptionContext:
        """
        Phase 1: 感知阶段
        
        收集当前时间、环境状态、宠物状态、待处理记忆等信息。
        
        Returns:
            PerceptionContext: 感知上下文
        """
        ...
    
    async def _phase_event_evaluation(
        self,
        perception: PerceptionContext,
    ) -> List[CandidateEvent]:
        """
        Phase 2: 事件评估阶段
        
        遍历所有注册的主动行为触发器，检查条件是否满足。
        
        Args:
            perception: 感知上下文
            
        Returns:
            List[CandidateEvent]: 满足条件的候选事件列表
        """
        ...
    
    async def _phase_priority_resolution(
        self,
        candidates: List[CandidateEvent],
    ) -> Optional[CandidateEvent]:
        """
        Phase 3: 优先级决策阶段
        
        对候选事件排序，检查冷却时间和全局频率限制，
        选择最高优先级的事件执行（或不执行）。
        
        Args:
            candidates: 候选事件列表
            
        Returns:
            Optional[CandidateEvent]: 选中的事件，或None（不执行）
        """
        ...
    
    async def _phase_execution(
        self,
        event: CandidateEvent,
    ) -> ExecutionResult:
        """
        Phase 4: 执行阶段
        
        根据事件复杂度选择Workflow或Agent模式执行。
        
        Args:
            event: 要执行的事件
            
        Returns:
            ExecutionResult: 执行结果
        """
        ...
    
    async def _phase_memory_update(
        self,
        event: CandidateEvent,
        result: ExecutionResult,
    ) -> None:
        """
        Phase 5: 记忆更新阶段
        
        记录执行的事件到短期记忆，更新行为统计。
        
        Args:
            event: 执行的事件
            result: 执行结果
        """
        ...
    
    def set_intervention_level(self, level: int) -> None:
        """
        设置介入级别。
        
        Args:
            level: 0=静默观察, 1=适度关心(默认), 2=积极伙伴
        """
        ...


class CooldownTracker:
    """
    冷却时间追踪器
    
    管理每个行为的冷却时间，支持持久化。
    """
    
    def __init__(self, persistence_path: str) -> None:
        """
        初始化冷却追踪器。
        
        Args:
            persistence_path: 持久化文件路径
        """
        ...
    
    def is_on_cooldown(self, key: str) -> bool:
        """
        检查是否在冷却中。
        
        Args:
            key: 冷却键
            
        Returns:
            bool: True=冷却中，False=可执行
        """
        ...
    
    def set_cooldown(self, key: str, duration_seconds: int) -> None:
        """
        设置冷却时间。
        
        Args:
            key: 冷却键
            duration_seconds: 冷却时长（秒）
        """
        ...
    
    def clear_cooldown(self, key: str) -> None:
        """
        清除冷却时间。
        
        Args:
            key: 冷却键
        """
        ...
```

### 3.3 BehaviorPlanner (行为计划器)

```python
# src/rainze/agent/behavior_planner.py

from __future__ import annotations
from typing import TYPE_CHECKING, Optional, List, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum, auto

if TYPE_CHECKING:
    from rainze.memory import MemoryManager
    from rainze.state import StateManager


class IntentionType(Enum):
    """意图类型"""
    PROACTIVE_CARE = auto()     # 主动关心
    TOPIC_INTEREST = auto()     # 话题意图
    BEHAVIOR_ADJUST = auto()    # 行为调整


@dataclass
class Intention:
    """意图定义"""
    type: IntentionType
    target: str                          # 目标行为标识
    trigger_condition: str               # 触发条件表达式
    reason: str                          # 生成原因
    priority: str                        # LOW/MEDIUM/HIGH
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class AvoidAction:
    """避免行为定义"""
    type: str
    target: str
    reason: str


@dataclass
class BehaviorPlan:
    """行为计划"""
    generated_at: datetime
    valid_until: datetime
    intentions: List[Intention] = field(default_factory=list)
    avoid_actions: List[AvoidAction] = field(default_factory=list)
    
    def is_valid(self) -> bool:
        """检查计划是否有效"""
        return datetime.now() < self.valid_until
    
    def get_active_intentions(self) -> List[Intention]:
        """获取活跃的意图列表"""
        ...


class BehaviorPlanner:
    """
    行为计划器
    
    轻量级行为规划系统，让桌宠的行为更有连贯性。
    
    设计目标：
    - 让行为更连贯：例如"连续几天提醒用户早睡"
    - 增加主动性：例如"今晚想和主人聊聊最近的心情"
    - 避免过度复杂：只是短期意图，不是长期目标系统
    - 零额外API调用：计划生成复用反思时间，或使用规则
    
    Attributes:
        _memory_manager: 记忆管理器
        _state_manager: 状态管理器
        _current_plan: 当前行为计划
        _intention_rules: 意图生成规则
    """
    
    def __init__(
        self,
        memory_manager: MemoryManager,
        state_manager: StateManager,
    ) -> None:
        """
        初始化行为计划器。
        
        Args:
            memory_manager: 记忆管理器
            state_manager: 状态管理器
        """
        ...
    
    async def generate_plan(self) -> BehaviorPlan:
        """
        生成新的行为计划。
        
        触发时机：
        - 每小时整点（与整点报时合并）
        - 每日反思时生成第二天的行为意图
        
        生成方式：
        1. 规则推断（优先，无API调用）
        2. LLM生成（复杂场景）
        
        Returns:
            BehaviorPlan: 新生成的行为计划
        """
        ...
    
    async def _infer_intentions_by_rules(self) -> List[Intention]:
        """
        基于规则推断意图（无需LLM）。
        
        检测规则：
        - 用户连续3天22点后活跃 -> remind_rest
        - 用户生日在3天内 -> celebrate_event
        - 用户本周互动减少50% -> check_mood
        - 用户昨天提到某话题且情绪积极 -> continue_topic
        
        Returns:
            List[Intention]: 推断出的意图列表
        """
        ...
    
    async def _infer_avoids_by_rules(self) -> List[AvoidAction]:
        """
        基于规则推断应避免的行为。
        
        Returns:
            List[AvoidAction]: 应避免的行为列表
        """
        ...
    
    def get_current_plan(self) -> Optional[BehaviorPlan]:
        """
        获取当前有效的行为计划。
        
        Returns:
            Optional[BehaviorPlan]: 当前计划，过期则返回None
        """
        ...
    
    def check_intention_trigger(
        self,
        perception: PerceptionContext,
    ) -> List[Intention]:
        """
        检查哪些意图的触发条件已满足。
        
        Args:
            perception: 当前感知上下文
            
        Returns:
            List[Intention]: 触发条件满足的意图列表
        """
        ...
    
    def mark_intention_completed(self, intention: Intention) -> None:
        """
        标记意图已完成。
        
        注意：完成后不立即生成新计划，等待下一整点统一生成。
        
        Args:
            intention: 已完成的意图
        """
        ...
    
    def inject_to_prompt(self) -> str:
        """
        生成注入到Prompt的意图描述。
        
        Returns:
            str: 格式化的意图描述，如 "[当前意图] 今晚想关心主人的休息情况"
        """
        ...


@dataclass
class IntentionRule:
    """意图生成规则"""
    name: str
    condition: str                       # 条件表达式
    generates: Dict[str, Any]            # 生成的意图配置
    check_interval_hours: int = 24       # 检查间隔


# 预定义的意图生成规则
DEFAULT_INTENTION_RULES: List[IntentionRule] = [
    IntentionRule(
        name="consecutive_late_nights",
        condition="late_night_count >= 3",
        generates={
            "type": IntentionType.PROACTIVE_CARE,
            "target": "remind_rest",
        },
    ),
    IntentionRule(
        name="upcoming_birthday",
        condition="days_to_birthday <= 3",
        generates={
            "type": IntentionType.PROACTIVE_CARE,
            "target": "celebrate_event",
        },
    ),
    IntentionRule(
        name="reduced_interaction",
        condition="interaction_drop_percent >= 50",
        generates=[
            {"type": IntentionType.BEHAVIOR_ADJUST, "target": "reduce_frequency"},
            {"type": IntentionType.PROACTIVE_CARE, "target": "check_mood"},
        ],
    ),
]
```

### 3.4 SceneClassifier (场景分类器)

```python
# src/rainze/agent/scene_classifier.py

from __future__ import annotations
from typing import Dict, List, Set, Optional, Any
from dataclasses import dataclass
import re

from rainze.agent.context_manager import SceneType, InteractionType


@dataclass
class ClassificationRule:
    """分类规则"""
    name: str
    conditions: List[str]           # 条件列表（AND关系）
    result: SceneType
    priority: int = 0               # 规则优先级


class SceneClassifier:
    """
    场景分类器
    
    在调用LLM前先判断场景复杂度，决定使用哪个Tier响应。
    
    分类规则（无API调用）：
    - SIMPLE: 高频简单交互（点击、拖拽、确认）
    - MEDIUM: 状态驱动事件（整点报时、系统警告）
    - COMPLEX: 需要上下文理解（自由对话、情感分析）
    
    Attributes:
        _rules: 分类规则列表
        _simple_interaction_types: 简单交互类型集合
        _medium_event_types: 中等事件类型集合
    """
    
    def __init__(self) -> None:
        """初始化场景分类器，加载默认规则。"""
        ...
    
    def classify(
        self,
        interaction_type: InteractionType,
        event_type: Optional[str] = None,
        user_input: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> SceneType:
        """
        分类场景复杂度。
        
        Args:
            interaction_type: 交互类型
            event_type: 事件类型（如 "hourly_chime", "system_warning"）
            user_input: 用户输入文本
            context: 额外上下文信息
            
        Returns:
            SceneType: 场景复杂度分类
            
        Example:
            >>> classifier.classify(InteractionType.PASSIVE_TRIGGER)
            SceneType.SIMPLE
            >>> classifier.classify(
            ...     InteractionType.CONVERSATION,
            ...     user_input="你好啊"
            ... )
            SceneType.COMPLEX
        """
        ...
    
    def _check_simple_conditions(
        self,
        interaction_type: InteractionType,
        event_type: Optional[str],
        user_input: Optional[str],
    ) -> bool:
        """
        检查是否满足SIMPLE场景条件。
        
        条件（OR关系）：
        - interaction_type in [PASSIVE_TRIGGER]
        - event_type in ["click", "drag", "hover", "release"]
        - user_input长度 < 5
        - is_confirmation == true
        """
        ...
    
    def _check_medium_conditions(
        self,
        interaction_type: InteractionType,
        event_type: Optional[str],
        context: Optional[Dict[str, Any]],
    ) -> bool:
        """
        检查是否满足MEDIUM场景条件。
        
        条件（OR关系）：
        - event_type in ["hourly_chime", "system_warning", "weather_update"]
        - has_clear_trigger == true
        - requires_memory_lookup == false
        """
        ...
    
    def add_rule(self, rule: ClassificationRule) -> None:
        """
        添加自定义分类规则。
        
        Args:
            rule: 分类规则
        """
        ...
    
    def get_tier_for_scene(self, scene_type: SceneType) -> int:
        """
        获取场景对应的响应Tier。
        
        Args:
            scene_type: 场景类型
            
        Returns:
            int: 响应Tier (1, 2, 或 3)
        """
        ...


# 简单交互类型（直接判定为SIMPLE）
SIMPLE_INTERACTION_TYPES: Set[InteractionType] = {
    InteractionType.PASSIVE_TRIGGER,
}

# 中等事件类型
MEDIUM_EVENT_TYPES: Set[str] = {
    "hourly_chime",
    "system_warning",
    "weather_update",
    "focus_warning",
    "focus_complete",
    "feed_response",
}

# 复杂场景关键词（触发COMPLEX）
COMPLEX_KEYWORDS: Set[str] = {
    "为什么", "怎么", "帮我", "记得", "之前", "上次",
    "你觉得", "你认为", "建议", "推荐",
}
```

### 3.5 IntentRecognizer (意图识别器)

```python
# src/rainze/agent/intent_recognizer.py

from __future__ import annotations
from typing import Dict, List, Optional, Tuple, Pattern
from dataclasses import dataclass
import re


@dataclass
class IntentMatch:
    """意图匹配结果"""
    intent: str                      # 意图标识
    confidence: float                # 置信度 (0-1)
    entities: Dict[str, str]         # 提取的实体
    route: Optional[str] = None      # 路由目标


class IntentRecognizer:
    """
    意图识别器
    
    从用户输入中识别意图，用于路由到正确的处理模块。
    
    识别优先级：
    1. 指令检测：以"/"开头的隐藏指令
    2. 工具/游戏意图：关键词匹配
    3. 自由对话：默认路径
    
    Attributes:
        _command_prefix: 指令前缀（默认"/"）
        _intent_patterns: 意图关键词模式
        _confidence_threshold: 置信度阈值
    """
    
    def __init__(
        self,
        command_prefix: str = "/",
        confidence_threshold: float = 0.6,
    ) -> None:
        """
        初始化意图识别器。
        
        Args:
            command_prefix: 指令前缀
            confidence_threshold: 置信度阈值，低于此值视为低置信
        """
        ...
    
    def recognize(self, user_input: str) -> IntentMatch:
        """
        识别用户输入的意图。
        
        Args:
            user_input: 用户输入文本
            
        Returns:
            IntentMatch: 意图匹配结果
            
        Example:
            >>> recognizer.recognize("/dance")
            IntentMatch(intent="command", confidence=1.0, route="dance_animation")
            >>> recognizer.recognize("帮我打开VS Code")
            IntentMatch(intent="launcher", confidence=0.9, entities={"app": "VS Code"})
            >>> recognizer.recognize("今天过得怎么样")
            IntentMatch(intent="conversation", confidence=1.0)
        """
        ...
    
    def _check_command(self, user_input: str) -> Optional[IntentMatch]:
        """
        检查是否为隐藏指令。
        
        Args:
            user_input: 用户输入
            
        Returns:
            Optional[IntentMatch]: 指令匹配结果，非指令返回None
        """
        ...
    
    def _match_intent_patterns(self, user_input: str) -> Optional[IntentMatch]:
        """
        匹配意图关键词模式。
        
        Args:
            user_input: 用户输入
            
        Returns:
            Optional[IntentMatch]: 匹配结果
        """
        ...
    
    def _extract_entities(
        self,
        user_input: str,
        intent: str,
    ) -> Dict[str, str]:
        """
        从输入中提取实体。
        
        Args:
            user_input: 用户输入
            intent: 识别出的意图
            
        Returns:
            Dict[str, str]: 实体字典
        """
        ...
    
    def add_intent_pattern(
        self,
        intent: str,
        keywords: List[str],
        route: Optional[str] = None,
    ) -> None:
        """
        添加意图关键词模式。
        
        Args:
            intent: 意图标识
            keywords: 关键词列表
            route: 路由目标
        """
        ...


# 默认意图关键词配置
DEFAULT_INTENT_KEYWORDS: Dict[str, Dict[str, Any]] = {
    "game": {
        "keywords": ["玩游戏", "猜拳", "骰子", "来一局", "玩一下"],
        "route": "game_module",
    },
    "tool": {
        "keywords": ["提醒我", "记住", "设置", "帮我记", "别让我忘"],
        "route": "tool_module",
    },
    "launcher": {
        "keywords": ["打开", "启动", "运行", "帮我开"],
        "route": "launcher_tool",
    },
    "query": {
        "keywords": ["查一下", "搜索", "天气", "几点了"],
        "route": "query_tool",
    },
}

# 隐藏指令映射
HIDDEN_COMMANDS: Dict[str, str] = {
    "dance": "dance_animation",
    "secret": "unlock_secret_dialogue",
    "debug": "show_debug_panel",
    "sleep": "force_sleep",
    "wake": "force_wake",
}
```

### 3.6 ConversationManager (对话管理器)

```python
# src/rainze/agent/conversation.py

from __future__ import annotations
from typing import TYPE_CHECKING, Optional, List, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import deque
import hashlib

if TYPE_CHECKING:
    from rainze.memory import MemoryManager


@dataclass
class Message:
    """对话消息"""
    role: str                        # "user" 或 "assistant"
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Session:
    """对话会话"""
    session_id: str
    started_at: datetime
    last_active: datetime
    messages: List[Message] = field(default_factory=list)
    topic_keywords: List[str] = field(default_factory=list)
    user_mood_history: List[str] = field(default_factory=list)
    
    def add_message(self, role: str, content: str) -> None:
        """添加消息"""
        ...
    
    def get_recent_messages(self, n: int) -> List[Message]:
        """获取最近n条消息"""
        ...


class ConversationManager:
    """
    对话会话管理器
    
    管理多轮对话上下文，包括：
    - 会话生命周期管理
    - 对话历史压缩
    - 话题追踪
    - 用户情绪推断
    
    Attributes:
        _memory_manager: 记忆管理器
        _current_session: 当前会话
        _session_timeout: 会话超时时间（分钟）
        _max_history_turns: 最大历史轮数
    """
    
    def __init__(
        self,
        memory_manager: MemoryManager,
        session_timeout_minutes: int = 120,
        max_history_turns: int = 20,
        compression_threshold_tokens: int = 4000,
    ) -> None:
        """
        初始化对话管理器。
        
        Args:
            memory_manager: 记忆管理器
            session_timeout_minutes: 会话超时（分钟），默认120
            max_history_turns: 最大保留轮数，默认20
            compression_threshold_tokens: 压缩阈值（tokens），默认4000
        """
        ...
    
    def get_or_create_session(self) -> Session:
        """
        获取或创建会话。
        
        如果当前会话过期或不存在，创建新会话。
        
        Returns:
            Session: 当前有效的会话
        """
        ...
    
    def add_user_message(self, content: str) -> None:
        """
        添加用户消息。
        
        Args:
            content: 用户输入内容
        """
        ...
    
    def add_assistant_message(self, content: str) -> None:
        """
        添加助手回复。
        
        Args:
            content: 助手回复内容
        """
        ...
    
    def get_conversation_history(
        self,
        max_turns: Optional[int] = None,
        format: str = "list",
    ) -> Any:
        """
        获取对话历史。
        
        Args:
            max_turns: 最大轮数，None表示使用默认值
            format: 返回格式，"list"返回Message列表，"string"返回格式化字符串
            
        Returns:
            对话历史（格式由format参数决定）
        """
        ...
    
    def compress_history(self) -> str:
        """
        压缩对话历史。
        
        当历史超过Token阈值时，压缩早期轮次为摘要。
        
        压缩优先级（从低到高）：
        1. 早期轮次的完整内容 → 摘要
        2. 中间轮次保留关键句
        3. 最近3轮始终保留完整
        4. 当前轮始终保留完整
        
        Returns:
            str: 压缩后的历史字符串
        """
        ...
    
    def infer_user_mood(self, user_input: str) -> str:
        """
        推断用户情绪。
        
        基于规则检测：
        - 标点符号（!/?/...）
        - 关键词（累/烦/开心等）
        - Emoji
        
        Args:
            user_input: 用户输入
            
        Returns:
            str: 推断的情绪标签
        """
        ...
    
    def detect_topic_switch(self, user_input: str) -> bool:
        """
        检测话题切换。
        
        通过计算与近期对话的相似度判断是否切换话题。
        
        Args:
            user_input: 用户输入
            
        Returns:
            bool: True表示话题切换
        """
        ...
    
    def end_session(self) -> None:
        """
        结束当前会话。
        
        将会话摘要写入长期记忆。
        """
        ...
    
    def clear_session(self) -> None:
        """
        清空当前会话（用户手动清空）。
        """
        ...


# 情绪关键词配置
MOOD_KEYWORDS: Dict[str, List[str]] = {
    "negative": ["累", "烦", "难过", "生气", "无聊", "孤独", "压力", "焦虑", "郁闷"],
    "positive": ["开心", "高兴", "哈哈", "太好了", "喜欢", "爱", "棒", "赞"],
    "urgent": ["急", "快", "马上", "立刻", "赶紧"],
    "tired": ["困", "累", "睡", "休息", "疲惫"],
}

# 情绪标点符号权重
PUNCTUATION_MOOD_HINTS: Dict[str, str] = {
    "!": "excited",
    "！": "excited",
    "?": "questioning",
    "？": "questioning",
    "...": "hesitant",
    "…": "hesitant",
}
```

---

## 4. 主动行为注册表

### 4.1 ProactiveBehaviorRegistry

```python
# src/rainze/agent/proactive/registry.py

from __future__ import annotations
from typing import Dict, List, Callable, Awaitable, Any, Optional
from dataclasses import dataclass, field
from enum import Enum

from rainze.agent.agent_loop import Priority, ExecutionMode


@dataclass
class ProactiveBehavior:
    """主动行为定义"""
    name: str                            # 行为名称
    trigger_type: str                    # 触发类型: time/state/idle/memory/random
    trigger_condition: Callable[[Any], bool]  # 触发条件函数
    priority: Priority                   # 优先级
    execution_mode: ExecutionMode        # 执行模式
    cooldown_seconds: int                # 冷却时间
    config_key: str                      # 配置键名
    handler: Callable[[Any], Awaitable[Any]]  # 处理函数
    enabled: bool = True                 # 是否启用


class ProactiveBehaviorRegistry:
    """
    主动行为注册表
    
    管理所有注册的主动行为，供Agent循环使用。
    
    行为分类：
    - 时间驱动: hourly_chime, daily_reflection, scheduled_reminder
    - 状态驱动: low_energy_warning, system_warning, mood_transition
    - 空闲驱动: idle_chat, sleep_trigger, memory_consolidation
    - 记忆驱动: important_date_reminder, behavior_insight
    - 随机事件: random_event
    """
    
    def __init__(self) -> None:
        """初始化注册表，加载默认行为。"""
        ...
    
    def register(self, behavior: ProactiveBehavior) -> None:
        """
        注册主动行为。
        
        Args:
            behavior: 行为定义
        """
        ...
    
    def unregister(self, name: str) -> None:
        """
        注销主动行为。
        
        Args:
            name: 行为名称
        """
        ...
    
    def get_all_behaviors(self) -> List[ProactiveBehavior]:
        """获取所有注册的行为"""
        ...
    
    def get_behaviors_by_type(self, trigger_type: str) -> List[ProactiveBehavior]:
        """按触发类型获取行为"""
        ...
    
    def enable_behavior(self, name: str) -> None:
        """启用行为"""
        ...
    
    def disable_behavior(self, name: str) -> None:
        """禁用行为"""
        ...
    
    def update_cooldown(self, name: str, cooldown_seconds: int) -> None:
        """更新冷却时间"""
        ...


def register_default_behaviors(registry: ProactiveBehaviorRegistry) -> None:
    """
    注册默认主动行为。
    
    包括：整点报时、系统警告、闲聊触发、睡眠触发等。
    """
    ...
```

---

## 5. 配置文件

### 5.1 context_manager_settings.json

```json
{
  "unified_entry": {
    "enable": true,
    "log_all_interactions": false,
    "interaction_timeout_ms": 30000
  },
  
  "intent_recognition": {
    "enable": true,
    "confidence_threshold": 0.6,
    "command_prefix": "/",
    "keywords": {
      "game": ["玩游戏", "猜拳", "骰子", "来一局", "玩一下"],
      "tool": ["提醒我", "记住", "设置", "帮我记", "别让我忘"],
      "launcher": ["打开", "启动", "运行", "帮我开"],
      "query": ["查一下", "搜索", "天气", "几点了"]
    },
    "fallback_to_conversation": true
  },
  
  "memory_write_policy": {
    "CONVERSATION": {"level": "FULL", "default_importance": 0.6},
    "GAME_INTERACTION": {"level": "RESULT_ONLY", "default_importance": 0.3},
    "TOOL_EXECUTION": {"level": "SUMMARY", "default_importance": 0.5},
    "PLUGIN_ACTION": {"level": "SUMMARY", "default_importance": 0.4},
    "SYSTEM_EVENT": {"level": "SUMMARY", "default_importance": 0.5},
    "PASSIVE_TRIGGER": {"level": "NONE", "default_importance": 0}
  },
  
  "memory_aggregation": {
    "enable": true,
    "aggregate_window_hours": 24,
    "min_count_to_aggregate": 3
  }
}
```

### 5.2 agent_loop_settings.json

```json
{
  "enable_autonomous_loop": true,
  "loop_interval_seconds": 60,
  
  "execution_mode": {
    "prefer_workflow": true,
    "agent_mode_triggers": [
      "free_conversation",
      "emotion_analysis_needed",
      "memory_retrieval_required",
      "creative_content_generation"
    ]
  },
  
  "priority_levels": {
    "CRITICAL": 100,
    "HIGH": 80,
    "MEDIUM": 50,
    "LOW": 20,
    "BACKGROUND": 0
  },
  
  "rate_limits": {
    "base_max_proactive_per_hour": 6,
    "min_interval_between_proactive_seconds": 300,
    "quiet_hours": {
      "enable": true,
      "start": "23:00",
      "end": "07:00",
      "allowed_priorities": ["CRITICAL", "HIGH"]
    }
  },
  
  "intervention_level": {
    "current_level": 1,
    "level_descriptions": {
      "0": "静默观察",
      "1": "适度关心",
      "2": "积极伙伴"
    }
  },
  
  "adaptive_frequency": {
    "enable": true,
    "positive_feedback_boost": 1.1,
    "negative_feedback_reduce": 0.8,
    "ignored_event_reduce": 0.95
  }
}
```

### 5.3 behavior_plan_settings.json

```json
{
  "enable_behavior_planning": true,
  "plan_generation": {
    "interval_hours": 1,
    "prefer_rule_based": true,
    "llm_generation_threshold": "complex_only",
    "max_intentions_per_plan": 3
  },
  "intention_rules": {
    "consecutive_late_nights": {
      "condition": "late_night_count >= 3",
      "generates": {"type": "proactive_care", "target": "remind_rest"}
    },
    "upcoming_birthday": {
      "condition": "days_to_birthday <= 3",
      "generates": {"type": "proactive_care", "target": "celebrate_event"}
    },
    "reduced_interaction": {
      "condition": "interaction_drop_percent >= 50",
      "generates": [
        {"type": "behavior_adjust", "target": "reduce_frequency"},
        {"type": "proactive_care", "target": "check_mood"}
      ]
    }
  },
  "plan_injection": {
    "inject_to_prompt": true,
    "prompt_template": "[当前意图] {intention_description}"
  }
}
```

### 5.4 conversation_settings.json

```json
{
  "input_processing": {
    "max_input_length": 500,
    "truncate_warning": "你说的太多了，我记不住啦...",
    "enable_sensitive_filter": true
  },
  
  "session_management": {
    "session_timeout_minutes": 120,
    "max_history_turns": 20,
    "history_compression_threshold_tokens": 4000,
    "always_keep_recent_turns": 3
  },
  
  "user_mood_inference": {
    "enable": true,
    "negative_keywords": ["累", "烦", "难过", "生气", "无聊", "孤独", "压力"],
    "positive_keywords": ["开心", "高兴", "哈哈", "太好了", "喜欢"],
    "urgency_indicators": ["!", "！", "急", "快", "马上"],
    "inject_mood_hint": true
  },
  
  "topic_tracking": {
    "enable": true,
    "switch_threshold": 0.3,
    "enable_transition_phrase": false
  }
}
```

---

## 6. 依赖关系

```
Agent模块依赖图:

┌──────────────────────────────────────────────────────────────┐
│                         Agent模块                            │
├──────────────────────────────────────────────────────────────┤
│  UnifiedContextManager ──────┬──────────────────────────────│
│         │                    │                              │
│         ▼                    ▼                              │
│  SceneClassifier      IntentRecognizer                      │
│         │                    │                              │
│         └────────┬───────────┘                              │
│                  │                                          │
│                  ▼                                          │
│            AgentLoop ◄──────── BehaviorPlanner              │
│                  │                    │                     │
│                  ▼                    │                     │
│     ProactiveBehaviorRegistry ────────┘                     │
│                  │                                          │
│                  ▼                                          │
│       ConversationManager                                   │
└──────────────────────────────────────────────────────────────┘
                  │
                  │ 依赖
                  ▼
┌─────────────────┬─────────────────┬─────────────────┐
│   Core模块      │   AI模块        │   Memory模块    │
│  (事件总线)     │  (响应生成)     │  (记忆检索)     │
└─────────────────┴─────────────────┴─────────────────┘
                  │
                  ▼
┌─────────────────┬─────────────────┐
│   State模块     │   RustCore模块  │
│  (状态管理)     │  (系统检测)     │
└─────────────────┴─────────────────┘
```

---

## 7. 与PRD章节对应

| 类/组件 | PRD章节 | 说明 |
|---------|---------|------|
| UnifiedContextManager | §0.5a | 统一上下文管理器 |
| InteractionType | §0.5a | 交互类型注册表 |
| MemoryWritePolicy | §0.5a | 记忆写入策略 |
| AgentLoop | §0.7 | Agent自主循环架构 |
| BehaviorPlanner | §0.7 | 轻量行为计划 |
| SceneClassifier | §0.3 | 场景分类规则 |
| ConversationManager | §0.5b | 用户主动对话场景 |
| ProactiveBehaviorRegistry | §0.7 | 主动行为注册表 |

---

> **文档版本**: v1.0.0
> **创建时间**: 2025-01-13
> **作者**: Claude Opus 4
