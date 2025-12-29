# MOD-State: 状态管理模块

> **模块版本**: v1.0.0
> **最后更新**: 2025-12-29
> **关联PRD**: PRD-Rainze.md v3.0.3 - 0.6a节
> **关联技术栈**: TECH-Rainze.md v1.0.1

---

## 1. 模块概述

### 1.1 职责定义

状态管理模块负责桌宠的核心状态维护，包括：

- **情绪状态机**: 5态+子态的混合驱动情绪系统
- **数值状态**: 能量、饥饿度、好感度的管理与计算
- **状态同步**: 单一数据源、持久化、检查点机制
- **状态转换**: 规则层优先 + LLM层软决策的混合驱动

### 1.2 设计哲学

```
轻度养成 × 自适应主动性 = 有生命感，但不是负担

核心原则：
- 用"情感共鸣"替代"惩罚机制"
- 桌宠不会因为被忽略而"死亡"
- 规则层始终优先于LLM层
- 状态变化触发重新评估，而非"覆盖"
```

### 1.3 状态优先级矩阵

| 状态 | 优先级 | 可覆盖性 | 触发条件 |
|------|--------|----------|----------|
| Sleeping | 100 | 不可覆盖 | 睡眠中 |
| Tired_LowEnergy | 90 | 不可覆盖 | energy < 20 |
| Anxious | 50 | 可覆盖 | 用户异常行为检测 |
| Sad | 40 | 可覆盖 | 连续负面事件/被忽视 |
| Tired_Night | 30 | 可覆盖 | hour >= 23 AND energy >= 20 |
| Excited | 20 | 可覆盖 | 强正面事件 |
| Happy | 10 | 可覆盖 | 正面交互 |
| Normal | 0 | 基准态 | 默认状态 |

---

## 2. 目录结构

```
src/rainze/state/
├── __init__.py
├── manager.py              # StateManager 状态管理器
├── emotion/
│   ├── __init__.py
│   ├── state_machine.py    # EmotionStateMachine 情绪状态机
│   ├── states.py           # 状态定义与子状态
│   ├── transitions.py      # 状态转换规则
│   └── intensity.py        # IntensityParser 情感强度解析
├── attributes/
│   ├── __init__.py
│   ├── energy.py           # EnergyManager 能量管理
│   ├── hunger.py           # HungerManager 饥饿度管理
│   ├── affinity.py         # AffinityManager 好感度管理
│   └── coins.py            # CoinsManager 金币管理
├── sync/
│   ├── __init__.py
│   ├── store.py            # StateStore 状态存储
│   ├── checkpoint.py       # CheckpointManager 检查点管理
│   ├── cache.py            # StateCache 内存缓存
│   └── notifier.py         # ChangeNotifier 变更通知
└── models/
    ├── __init__.py
    ├── state.py            # 状态数据模型
    └── events.py           # 状态事件模型
```

---

## 3. 核心类设计

### 3.1 StateManager (状态管理器)

```python
"""状态管理器 - 统一管理所有状态的入口"""

from enum import Enum
from typing import Optional, Callable, Any
from dataclasses import dataclass
from datetime import datetime

class StateManager:
    """
    状态管理器
    
    职责：
    - 协调各子状态管理器
    - 提供统一的状态访问接口
    - 触发状态变更事件
    - 管理状态持久化
    """
    
    def __init__(
        self,
        config: "StateConfig",
        storage: "StorageManager",
        event_bus: "EventBus"
    ) -> None:
        """
        初始化状态管理器
        
        Args:
            config: 状态配置
            storage: 存储管理器
            event_bus: 事件总线
        """
        ...
    
    # ==================== 状态访问 ====================
    
    @property
    def emotion(self) -> "EmotionStateMachine":
        """获取情绪状态机"""
        ...
    
    @property
    def energy(self) -> "EnergyManager":
        """获取能量管理器"""
        ...
    
    @property
    def hunger(self) -> "HungerManager":
        """获取饥饿度管理器"""
        ...
    
    @property
    def affinity(self) -> "AffinityManager":
        """获取好感度管理器"""
        ...
    
    @property
    def coins(self) -> "CoinsManager":
        """获取金币管理器"""
        ...
    
    # ==================== 快照与恢复 ====================
    
    def get_snapshot(self) -> "StateSnapshot":
        """
        获取当前状态快照
        
        Returns:
            包含所有状态的快照对象
        """
        ...
    
    def restore_from_snapshot(self, snapshot: "StateSnapshot") -> None:
        """
        从快照恢复状态
        
        Args:
            snapshot: 状态快照
        """
        ...
    
    # ==================== 持久化 ====================
    
    async def save(self) -> None:
        """保存所有状态到持久化存储"""
        ...
    
    async def load(self) -> None:
        """从持久化存储加载状态"""
        ...
    
    # ==================== 状态评估 ====================
    
    def evaluate_all_states(self) -> None:
        """
        重新评估所有状态
        
        在数值变化后调用，触发状态转换评估
        """
        ...
    
    def get_prompt_modifiers(self) -> dict[str, str]:
        """
        获取当前状态对Prompt的修饰
        
        Returns:
            状态对应的Prompt修饰词典
        """
        ...
    
    def get_behavior_modifiers(self) -> dict[str, float]:
        """
        获取当前状态对行为的修饰
        
        Returns:
            行为修饰因子词典
        """
        ...
    
    # ==================== 生命周期 ====================
    
    async def start(self) -> None:
        """启动状态管理器"""
        ...
    
    async def stop(self) -> None:
        """停止状态管理器，保存状态"""
        ...
    
    def register_change_listener(
        self,
        callback: Callable[["StateChangedEvent"], None]
    ) -> None:
        """
        注册状态变更监听器
        
        Args:
            callback: 变更回调函数
        """
        ...
```

### 3.2 EmotionStateMachine (情绪状态机)

```python
"""情绪状态机 - 混合驱动的5态+子态系统"""

from enum import Enum
from typing import Optional
from dataclasses import dataclass

class MoodState(Enum):
    """主情绪状态"""
    HAPPY = "happy"
    NORMAL = "normal"
    TIRED = "tired"
    SAD = "sad"
    ANXIOUS = "anxious"

class MoodSubState(Enum):
    """子情绪状态"""
    # Happy子状态
    EXCITED = "excited"
    CONTENT = "content"
    # Normal子状态
    RELAXED = "relaxed"
    FOCUSED = "focused"
    # Tired子状态
    SLEEPY = "sleepy"
    EXHAUSTED = "exhausted"
    # Sad子状态
    DISAPPOINTED = "disappointed"
    LONELY = "lonely"
    # Anxious子状态
    WORRIED = "worried"
    NERVOUS = "nervous"

@dataclass
class EmotionState:
    """情绪状态数据"""
    main_state: MoodState
    sub_state: Optional[MoodSubState]
    intensity: float  # 0.0-1.0
    entered_at: datetime
    trigger_reason: str

class EmotionStateMachine:
    """
    情绪状态机
    
    实现混合驱动架构：
    - 规则层（硬约束）：确定性转换，不依赖LLM
    - LLM层（软决策）：情感细微调整，需要上下文理解
    
    规则层始终优先于LLM层
    """
    
    def __init__(
        self,
        config: "EmotionConfig",
        event_bus: "EventBus"
    ) -> None:
        """
        初始化情绪状态机
        
        Args:
            config: 情绪配置
            event_bus: 事件总线
        """
        ...
    
    # ==================== 状态访问 ====================
    
    @property
    def current_state(self) -> EmotionState:
        """获取当前情绪状态"""
        ...
    
    @property
    def main_mood(self) -> MoodState:
        """获取主情绪状态"""
        ...
    
    @property
    def sub_mood(self) -> Optional[MoodSubState]:
        """获取子情绪状态"""
        ...
    
    @property
    def intensity(self) -> float:
        """获取情绪强度 (0.0-1.0)"""
        ...
    
    # ==================== 规则层转换 ====================
    
    def apply_rule_transition(
        self,
        energy: float,
        hour: int,
        idle_minutes: int,
        is_sleeping: bool
    ) -> Optional[MoodState]:
        """
        应用规则层状态转换（硬约束）
        
        规则层判断优先于任何LLM层决策
        
        Args:
            energy: 当前能量值
            hour: 当前小时
            idle_minutes: 空闲分钟数
            is_sleeping: 是否睡眠中
            
        Returns:
            需要转换到的状态，None表示规则层不触发转换
        """
        ...
    
    # ==================== LLM层转换 ====================
    
    def apply_llm_suggestion(
        self,
        emotion_tag: str,
        intensity: float,
        context: dict[str, Any]
    ) -> bool:
        """
        应用LLM层情绪建议（软决策）
        
        仅在规则层未触发且状态允许覆盖时生效
        
        Args:
            emotion_tag: LLM输出的情感标签
            intensity: 情感强度
            context: 上下文信息
            
        Returns:
            是否应用了转换
        """
        ...
    
    # ==================== 状态转换 ====================
    
    def transition_to(
        self,
        target_state: MoodState,
        reason: str,
        sub_state: Optional[MoodSubState] = None,
        intensity: float = 0.5
    ) -> bool:
        """
        执行状态转换
        
        检查状态优先级矩阵和覆盖条件
        
        Args:
            target_state: 目标状态
            reason: 转换原因
            sub_state: 子状态
            intensity: 强度
            
        Returns:
            是否成功转换
        """
        ...
    
    def can_transition_to(self, target_state: MoodState) -> bool:
        """
        检查是否可以转换到目标状态
        
        Args:
            target_state: 目标状态
            
        Returns:
            是否允许转换
        """
        ...
    
    # ==================== 平滑过渡 ====================
    
    def apply_inertia(
        self,
        target_intensity: float,
        inertia_factor: float = 0.7
    ) -> float:
        """
        应用情绪惯性
        
        new_intensity = current * inertia + target * (1 - inertia)
        
        Args:
            target_intensity: 目标强度
            inertia_factor: 惯性因子
            
        Returns:
            平滑后的强度
        """
        ...
    
    def check_switch_protection(self, target_state: MoodState) -> bool:
        """
        检查状态切换保护
        
        同一状态对60秒内不可重复切换
        
        Args:
            target_state: 目标状态
            
        Returns:
            是否在保护期内
        """
        ...
    
    # ==================== 衰减与恢复 ====================
    
    def apply_decay(self) -> None:
        """
        应用情绪衰减
        
        Happy 2小时无强化 → Normal
        """
        ...
    
    def apply_recovery(
        self,
        positive_action: str,
        intensity: float
    ) -> None:
        """
        应用情绪恢复
        
        Args:
            positive_action: 正面行为类型
            intensity: 行为强度
        """
        ...
    
    # ==================== 表情映射 ====================
    
    def get_expression(self) -> str:
        """
        获取当前状态对应的表情
        
        Returns:
            表情标识符
        """
        ...
    
    def get_animation_hint(self) -> Optional[str]:
        """
        获取动画提示
        
        Returns:
            动画标识符
        """
        ...
```

### 3.3 IntensityParser (情感强度解析器)

```python
"""情感强度解析器 - 从LLM输出中提取情感标签"""

import re
from dataclasses import dataclass
from typing import Optional

@dataclass
class ParsedEmotion:
    """解析后的情感数据"""
    tag: str
    intensity: float
    raw_text: str  # 移除标签后的文本

class IntensityParser:
    """
    情感强度解析器
    
    从LLM输出中提取 [EMOTION:tag:intensity] 格式的标签
    支持规则回退推断
    """
    
    # 正则模式
    EMOTION_PATTERN = re.compile(r"\[EMOTION:(\w+):([\d.]+)\]")
    
    # 有效标签
    VALID_TAGS = {
        "happy", "excited", "sad", "angry", "shy",
        "surprised", "tired", "anxious", "neutral"
    }
    
    def __init__(self, config: "IntensityConfig") -> None:
        """
        初始化解析器
        
        Args:
            config: 解析器配置
        """
        ...
    
    def parse(self, text: str) -> ParsedEmotion:
        """
        解析文本中的情感标签
        
        Args:
            text: LLM输出文本
            
        Returns:
            解析后的情感数据
        """
        ...
    
    def parse_with_fallback(self, text: str) -> ParsedEmotion:
        """
        带规则回退的解析
        
        解析失败时使用规则推断
        
        Args:
            text: LLM输出文本
            
        Returns:
            解析后的情感数据
        """
        ...
    
    def infer_from_rules(self, text: str) -> ParsedEmotion:
        """
        使用规则推断情感
        
        基于标点符号、emoji、关键词等推断
        
        Args:
            text: 文本内容
            
        Returns:
            推断的情感数据
        """
        ...
    
    def strip_emotion_tag(self, text: str) -> str:
        """
        移除文本中的情感标签
        
        Args:
            text: 原始文本
            
        Returns:
            移除标签后的文本
        """
        ...
    
    def validate_tag(self, tag: str) -> bool:
        """
        验证标签是否有效
        
        Args:
            tag: 标签名
            
        Returns:
            是否有效
        """
        ...
    
    def validate_intensity(self, intensity: float) -> float:
        """
        验证并裁剪强度值到 [0.0, 1.0]
        
        Args:
            intensity: 原始强度
            
        Returns:
            有效强度值
        """
        ...
```

### 3.4 属性管理器

```python
"""属性管理器 - 能量、饥饿度、好感度、金币"""

from abc import ABC, abstractmethod
from typing import Callable

class AttributeManager(ABC):
    """属性管理器基类"""
    
    @property
    @abstractmethod
    def value(self) -> float:
        """获取当前值"""
        ...
    
    @abstractmethod
    def add(self, amount: float, reason: str) -> float:
        """增加值"""
        ...
    
    @abstractmethod
    def subtract(self, amount: float, reason: str) -> float:
        """减少值"""
        ...
    
    @abstractmethod
    def set(self, value: float, reason: str) -> None:
        """设置值"""
        ...


class EnergyManager(AttributeManager):
    """
    能量管理器
    
    范围: 0-100
    消耗: 长时间运行、频繁互动
    恢复: 睡眠模式、用户关闭应用
    """
    
    def __init__(
        self,
        config: "EnergyConfig",
        event_bus: "EventBus"
    ) -> None:
        ...
    
    @property
    def value(self) -> float:
        """当前能量值 (0-100)"""
        ...
    
    @property
    def is_low(self) -> bool:
        """是否低能量 (< low_threshold)"""
        ...
    
    @property
    def is_critical(self) -> bool:
        """是否极低能量 (< critical_threshold)"""
        ...
    
    def add(self, amount: float, reason: str) -> float:
        """
        增加能量
        
        Args:
            amount: 增加量
            reason: 原因
            
        Returns:
            增加后的值
        """
        ...
    
    def subtract(self, amount: float, reason: str) -> float:
        """
        消耗能量
        
        Args:
            amount: 消耗量
            reason: 原因
            
        Returns:
            消耗后的值
        """
        ...
    
    def apply_hourly_decay(self) -> float:
        """
        应用每小时衰减
        
        Returns:
            衰减后的值
        """
        ...
    
    def apply_sleep_recovery(self, hours: float) -> float:
        """
        应用睡眠恢复
        
        Args:
            hours: 睡眠时长
            
        Returns:
            恢复后的值
        """
        ...


class HungerManager(AttributeManager):
    """
    饥饿度管理器
    
    范围: 0-100 (0=饱, 100=很饿)
    增长: 时间流逝 (+2/小时)
    降低: 用户喂食
    """
    
    def __init__(
        self,
        config: "HungerConfig",
        event_bus: "EventBus"
    ) -> None:
        ...
    
    @property
    def value(self) -> float:
        """当前饥饿度 (0-100)"""
        ...
    
    @property
    def should_mention(self) -> bool:
        """是否应该提及饥饿 (>= mention_threshold)"""
        ...
    
    @property
    def is_obvious(self) -> bool:
        """是否明显饥饿 (>= obvious_threshold)"""
        ...
    
    @property
    def should_auto_feed(self) -> bool:
        """是否应该自主觅食 (>= auto_feed_threshold)"""
        ...
    
    def feed(self, food_item: "FoodItem") -> float:
        """
        喂食
        
        Args:
            food_item: 食物物品
            
        Returns:
            喂食后的饥饿度
        """
        ...
    
    def apply_hourly_increase(self) -> float:
        """
        应用每小时增长
        
        Returns:
            增长后的值
        """
        ...


class AffinityManager(AttributeManager):
    """
    好感度管理器
    
    范围: 0-999
    等级:
      - Lv.1 (0-24): 陌生
      - Lv.2 (25-49): 熟悉
      - Lv.3 (50-74): 亲密
      - Lv.4 (75-99): 挚爱
      - Lv.5 (100+): 羁绊
    """
    
    def __init__(
        self,
        config: "AffinityConfig",
        event_bus: "EventBus"
    ) -> None:
        ...
    
    @property
    def value(self) -> int:
        """当前好感度 (0-999)"""
        ...
    
    @property
    def level(self) -> int:
        """当前等级 (1-5)"""
        ...
    
    @property
    def level_name(self) -> str:
        """等级名称"""
        ...
    
    @property
    def proactivity_multiplier(self) -> float:
        """主动性乘数（基于好感度等级）"""
        ...
    
    def add(self, amount: int, reason: str) -> int:
        """
        增加好感度
        
        Args:
            amount: 增加量
            reason: 原因
            
        Returns:
            增加后的值
        """
        ...
    
    def subtract(self, amount: int, reason: str) -> int:
        """
        减少好感度
        
        有下限保护 (min_affinity)
        
        Args:
            amount: 减少量
            reason: 原因
            
        Returns:
            减少后的值
        """
        ...
    
    def check_level_up(self) -> Optional[int]:
        """
        检查等级提升
        
        Returns:
            新等级，None表示未提升
        """
        ...


class CoinsManager(AttributeManager):
    """
    金币管理器
    
    获取: 专注时长、完成日程、每日签到、小游戏
    消费: 商城购买
    """
    
    def __init__(
        self,
        config: "EconomyConfig",
        event_bus: "EventBus"
    ) -> None:
        ...
    
    @property
    def value(self) -> int:
        """当前金币数"""
        ...
    
    def add(self, amount: int, reason: str) -> int:
        """
        增加金币
        
        Args:
            amount: 增加量
            reason: 原因
            
        Returns:
            增加后的值
        """
        ...
    
    def subtract(self, amount: int, reason: str) -> int:
        """
        消费金币
        
        Args:
            amount: 消费量
            reason: 原因
            
        Returns:
            消费后的值
            
        Raises:
            InsufficientCoinsError: 金币不足
        """
        ...
    
    def can_afford(self, amount: int) -> bool:
        """
        检查是否能负担
        
        Args:
            amount: 金额
            
        Returns:
            是否足够
        """
        ...
```

### 3.5 StateStore (状态存储)

```python
"""状态存储 - 单一数据源与持久化"""

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional

@dataclass
class StateSnapshot:
    """状态快照"""
    # 核心状态
    mood: str
    mood_sub: Optional[str]
    mood_intensity: float
    energy: float
    hunger: float
    affinity: int
    coins: int
    
    # 位置信息
    position_x: int
    position_y: int
    display_mode: str
    
    # 会话状态
    last_interaction_time: datetime
    session_id: str
    
    # 元数据
    checkpoint_id: str
    timestamp: datetime
    schema_version: str


class StateStore:
    """
    状态存储
    
    实现单一数据源 (Single Source of Truth)
    - 所有状态通过此类存取
    - UI组件订阅变化通知
    - 禁止外部直接修改状态
    """
    
    def __init__(
        self,
        config: "StorageConfig",
        file_path: str
    ) -> None:
        """
        初始化状态存储
        
        Args:
            config: 存储配置
            file_path: 状态文件路径
        """
        ...
    
    # ==================== 状态访问 ====================
    
    def get(self, key: str) -> Any:
        """
        获取状态值
        
        Args:
            key: 状态键
            
        Returns:
            状态值
        """
        ...
    
    def set(self, key: str, value: Any, reason: str) -> None:
        """
        设置状态值（触发变更通知）
        
        Args:
            key: 状态键
            value: 状态值
            reason: 变更原因
        """
        ...
    
    def batch_update(
        self,
        updates: dict[str, Any],
        reason: str
    ) -> None:
        """
        批量更新状态
        
        Args:
            updates: 更新字典
            reason: 变更原因
        """
        ...
    
    # ==================== 快照 ====================
    
    def create_snapshot(self) -> StateSnapshot:
        """
        创建当前状态快照
        
        Returns:
            状态快照
        """
        ...
    
    def restore_snapshot(self, snapshot: StateSnapshot) -> None:
        """
        从快照恢复状态
        
        Args:
            snapshot: 状态快照
        """
        ...
    
    # ==================== 持久化 ====================
    
    async def save_to_file(self) -> None:
        """保存状态到文件"""
        ...
    
    async def load_from_file(self) -> None:
        """从文件加载状态"""
        ...
    
    async def load_from_backup(self) -> bool:
        """
        从备份恢复
        
        Returns:
            是否成功恢复
        """
        ...
    
    # ==================== 订阅 ====================
    
    def subscribe(
        self,
        callback: Callable[["StateChangedEvent"], None]
    ) -> Callable[[], None]:
        """
        订阅状态变化
        
        Args:
            callback: 变化回调
            
        Returns:
            取消订阅函数
        """
        ...
```

### 3.6 CheckpointManager (检查点管理器)

```python
"""检查点管理器 - 状态持久化与恢复"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum

class CheckpointTrigger(Enum):
    """检查点触发条件"""
    STATE_CHANGED = "state_changed"      # 状态变化
    CONVERSATION_END = "conversation_end" # 对话结束
    TOOL_SUCCESS = "tool_success"        # 工具执行成功
    TIMER = "timer"                      # 定时保存
    SHUTDOWN = "shutdown"                # 程序关闭

@dataclass
class Checkpoint:
    """检查点数据"""
    id: str
    trigger: CheckpointTrigger
    snapshot: "StateSnapshot"
    created_at: datetime

class CheckpointManager:
    """
    检查点管理器
    
    触发条件（满足任一即保存）:
    - 状态变化时
    - 每次对话结束后
    - 工具执行成功后
    - 定时保存（间隔30秒）
    - 程序正常退出时
    """
    
    def __init__(
        self,
        config: "CheckpointConfig",
        state_store: "StateStore"
    ) -> None:
        """
        初始化检查点管理器
        
        Args:
            config: 检查点配置
            state_store: 状态存储
        """
        ...
    
    async def create_checkpoint(
        self,
        trigger: CheckpointTrigger
    ) -> Checkpoint:
        """
        创建检查点
        
        Args:
            trigger: 触发原因
            
        Returns:
            检查点对象
        """
        ...
    
    async def on_state_changed(self, event: "StateChangedEvent") -> None:
        """
        状态变化时的处理
        
        Args:
            event: 状态变化事件
        """
        ...
    
    async def on_conversation_end(self) -> None:
        """对话结束时创建检查点"""
        ...
    
    async def on_tool_success(self, tool_name: str) -> None:
        """
        工具执行成功时创建检查点
        
        Args:
            tool_name: 工具名称
        """
        ...
    
    async def start_timer(self) -> None:
        """启动定时保存"""
        ...
    
    async def stop_timer(self) -> None:
        """停止定时保存"""
        ...
    
    async def on_shutdown(self) -> None:
        """程序关闭时创建检查点"""
        ...
    
    def get_latest_checkpoint(self) -> Optional[Checkpoint]:
        """
        获取最新检查点
        
        Returns:
            最新检查点，不存在返回None
        """
        ...
    
    async def restore_from_checkpoint(
        self,
        checkpoint: Optional[Checkpoint] = None
    ) -> bool:
        """
        从检查点恢复
        
        Args:
            checkpoint: 指定检查点，None则使用最新
            
        Returns:
            是否成功恢复
        """
        ...
    
    async def detect_crash_recovery(self) -> bool:
        """
        检测是否需要崩溃恢复
        
        Returns:
            是否检测到异常退出
        """
        ...
```

---

## 4. 数据模型

### 4.1 状态事件模型

```python
"""状态事件模型"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Optional

class StateChangeType(Enum):
    """状态变化类型"""
    MOOD_CHANGED = "mood_changed"
    ENERGY_CHANGED = "energy_changed"
    HUNGER_CHANGED = "hunger_changed"
    AFFINITY_CHANGED = "affinity_changed"
    COINS_CHANGED = "coins_changed"
    LEVEL_UP = "level_up"
    POSITION_CHANGED = "position_changed"

@dataclass
class StateChangedEvent:
    """状态变化事件"""
    change_type: StateChangeType
    old_value: Any
    new_value: Any
    reason: str
    timestamp: datetime
    
    # 可选的额外信息
    extra: Optional[dict[str, Any]] = None

@dataclass
class MoodTransitionEvent:
    """情绪转换事件"""
    from_state: "MoodState"
    to_state: "MoodState"
    from_sub: Optional["MoodSubState"]
    to_sub: Optional["MoodSubState"]
    trigger: str  # "rule" | "llm" | "decay" | "recovery"
    reason: str
    timestamp: datetime

@dataclass
class LevelUpEvent:
    """等级提升事件"""
    attribute: str  # "affinity"
    old_level: int
    new_level: int
    old_value: int
    new_value: int
    unlocks: list[str]  # 解锁内容
    timestamp: datetime
```

### 4.2 配置模型

```python
"""状态配置模型"""

from dataclasses import dataclass, field
from typing import Optional

@dataclass
class EmotionConfig:
    """情绪配置"""
    initial_state: str = "Normal"
    states: list[str] = field(default_factory=lambda: [
        "Happy", "Normal", "Tired", "Sad", "Anxious"
    ])
    
    # 状态优先级
    state_priority: dict[str, int] = field(default_factory=lambda: {
        "Sleeping": 100,
        "Tired_LowEnergy": 90,
        "Anxious": 50,
        "Sad": 40,
        "Tired_Night": 30,
        "Excited": 20,
        "Happy": 10,
        "Normal": 0
    })
    
    # 平滑过渡
    min_condition_duration_seconds: int = 30
    switch_protection_seconds: int = 60
    inertia_factor: float = 0.7
    
    # 衰减设置
    happy_decay_hours: float = 2.0
    sad_recovery_hours: float = 4.0
    natural_decay_per_hour: float = 3.0

@dataclass
class EnergyConfig:
    """能量配置"""
    max_value: float = 100.0
    min_value: float = 0.0
    initial_value: float = 80.0
    decay_per_hour: float = 2.0
    sleep_recovery_per_hour: float = 20.0
    low_threshold: float = 30.0
    critical_threshold: float = 10.0

@dataclass
class HungerConfig:
    """饥饿度配置"""
    max_value: float = 100.0
    min_value: float = 0.0
    initial_value: float = 20.0
    increase_per_hour: float = 2.0
    mention_threshold: float = 40.0
    obvious_threshold: float = 60.0
    auto_feed_threshold: float = 70.0
    auto_feed_affinity_penalty: int = 3
    starving_affinity_decay_per_hour: int = 1
    affinity_decay_min_floor: int = 10

@dataclass
class AffinityConfig:
    """好感度配置"""
    max_value: int = 999
    min_value: int = 10
    initial_value: int = 50
    level_thresholds: list[int] = field(default_factory=lambda: [0, 25, 50, 75, 100])
    level_names: list[str] = field(default_factory=lambda: [
        "陌生", "熟悉", "亲密", "挚爱", "羁绊"
    ])
    proactivity_by_level: dict[int, float] = field(default_factory=lambda: {
        1: 0.2, 2: 0.4, 3: 0.6, 4: 0.8, 5: 1.0
    })

@dataclass
class CheckpointConfig:
    """检查点配置"""
    persistence_file: str = "./data/user_state.json"
    backup_file: str = "./data/user_state.backup.json"
    auto_save_interval_seconds: int = 30
    save_on_change: bool = True
    save_on_conversation_end: bool = True
    save_on_tool_success: bool = True
    enable_backup: bool = True
    schema_version: str = "1.0"
    enable_crash_detection: bool = True

@dataclass
class StateConfig:
    """状态系统总配置"""
    emotion: EmotionConfig = field(default_factory=EmotionConfig)
    energy: EnergyConfig = field(default_factory=EnergyConfig)
    hunger: HungerConfig = field(default_factory=HungerConfig)
    affinity: AffinityConfig = field(default_factory=AffinityConfig)
    checkpoint: CheckpointConfig = field(default_factory=CheckpointConfig)
```

---

## 5. 配置文件规范

### 5.1 emotion_settings.json

```json
{
  "state_machine": {
    "initial_state": "Normal",
    "states": ["Happy", "Normal", "Tired", "Sad", "Anxious"],
    "sub_states": {
      "Happy": ["Excited", "Content"],
      "Normal": ["Relaxed", "Focused"],
      "Tired": ["Sleepy", "Exhausted"],
      "Sad": ["Disappointed", "Lonely"],
      "Anxious": ["Worried", "Nervous"]
    },
    "state_priority": {
      "Sleeping": 100,
      "Tired_LowEnergy": 90,
      "Anxious": 50,
      "Sad": 40,
      "Tired_Night": 30,
      "Excited": 20,
      "Happy": 10,
      "Normal": 0
    },
    "uncoverridable_conditions": {
      "Tired": "energy < 20",
      "Sleeping": "is_sleeping == true"
    },
    "override_requirements": {
      "min_positive_intensity": 0.8,
      "min_consecutive_positive_interactions": 3,
      "comfort_actions": ["pet", "feed", "caring_dialogue"]
    }
  },
  
  "emotion_intensity_parsing": {
    "enable": true,
    "output_format": "[EMOTION:tag:intensity]",
    "regex_pattern": "\\[EMOTION:(\\w+):([\\d.]+)\\]",
    "strip_from_display": true,
    "valid_tags": ["happy", "excited", "sad", "angry", "shy", "surprised", "tired", "anxious", "neutral"],
    "intensity_range": [0.0, 1.0],
    "rule_fallback": {
      "enable": true,
      "exclamation_boost": 0.2,
      "emoji_boost": 0.1,
      "ellipsis_reduce": 0.2,
      "default_tag": "neutral",
      "default_intensity": 0.5
    }
  },
  
  "smooth_transition": {
    "min_condition_duration_seconds": 30,
    "switch_protection_seconds": 60,
    "inertia_factor": 0.7
  },
  
  "decay_settings": {
    "happy_decay_hours": 2,
    "sad_recovery_hours": 4,
    "natural_decay_per_hour": 3
  },
  
  "mood_expressions": {
    "Happy": ["smile", "excited"],
    "Normal": ["idle", "relaxed"],
    "Tired": ["yawn", "sleepy"],
    "Sad": ["sad", "disappointed"],
    "Anxious": ["worried", "nervous"]
  },
  
  "mood_prompt_modifiers": {
    "Happy": "用活泼开心的语气回复，可以用emoji",
    "Excited": "非常兴奋和热情，表达更夸张",
    "Normal": "",
    "Tired": "用简短的语气回复，偶尔打哈欠",
    "Sad": "用低落、简短的语气回复",
    "Anxious": "表现出担心和关心，多问候用户状况"
  },
  
  "behavior_modifiers": {
    "Happy": {
      "idle_chat_frequency": 1.5,
      "proactive_event_probability": 1.3
    },
    "Tired": {
      "idle_chat_frequency": 0.5,
      "proactive_event_probability": 0.3
    },
    "Sad": {
      "idle_chat_frequency": 0.7,
      "proactive_event_probability": 0.5
    }
  }
}
```

### 5.2 state_settings.json

```json
{
  "energy": {
    "max": 100,
    "initial": 80,
    "decay_per_hour": 2,
    "sleep_recovery_per_hour": 20,
    "low_threshold": 30,
    "critical_threshold": 10
  },
  
  "hunger": {
    "max": 100,
    "initial": 20,
    "increase_per_hour": 2,
    "mention_threshold": 40,
    "obvious_threshold": 60,
    "auto_feed_threshold": 70,
    "auto_feed_affinity_penalty": 3,
    "starving_affinity_decay_per_hour": 1,
    "affinity_decay_min_floor": 10
  },
  
  "affinity": {
    "level_thresholds": [0, 25, 50, 75, 100],
    "level_names": ["陌生", "熟悉", "亲密", "挚爱", "羁绊"],
    "max": 999,
    "min": 10,
    "initial": 50,
    "decay_per_day_inactive": 0,
    "proactivity_by_level": {
      "1": 0.2,
      "2": 0.4,
      "3": 0.6,
      "4": 0.8,
      "5": 1.0
    }
  },
  
  "coins": {
    "initial": 100
  },
  
  "state_sync": {
    "persistence_file": "./data/user_state.json",
    "backup_file": "./data/user_state.backup.json",
    "auto_save_interval_seconds": 30,
    "save_on_change": true,
    "save_on_conversation_end": true,
    "save_on_tool_success": true,
    "enable_backup": true,
    "backup_on_save": true,
    "schema_version": "1.0",
    "enable_memory_cache": true,
    "cache_size": 100,
    "enable_change_log": true,
    "change_log_to_trace": true,
    "batch_update_delay_ms": 100,
    "crash_recovery": {
      "enable": true,
      "detect_abnormal_exit": true,
      "show_recovery_prompt": true
    },
    "default_state_on_corruption": {
      "mood": "Normal",
      "energy": 80,
      "hunger": 20,
      "affinity": 50,
      "coins": 100
    }
  }
}
```

---

## 6. 异常定义

```python
"""状态系统异常"""

class StateError(Exception):
    """状态系统基础异常"""
    pass

class InvalidStateTransitionError(StateError):
    """无效状态转换"""
    def __init__(
        self,
        from_state: str,
        to_state: str,
        reason: str
    ):
        self.from_state = from_state
        self.to_state = to_state
        super().__init__(
            f"无法从 {from_state} 转换到 {to_state}: {reason}"
        )

class StateProtectionError(StateError):
    """状态保护期错误"""
    def __init__(self, state: str, remaining_seconds: int):
        self.state = state
        self.remaining_seconds = remaining_seconds
        super().__init__(
            f"状态 {state} 在保护期内，剩余 {remaining_seconds} 秒"
        )

class InsufficientCoinsError(StateError):
    """金币不足"""
    def __init__(self, required: int, available: int):
        self.required = required
        self.available = available
        super().__init__(
            f"金币不足: 需要 {required}，当前 {available}"
        )

class StatePersistenceError(StateError):
    """状态持久化错误"""
    pass

class StateCorruptionError(StateError):
    """状态数据损坏"""
    def __init__(self, file_path: str, reason: str):
        self.file_path = file_path
        super().__init__(f"状态文件损坏 {file_path}: {reason}")

class CheckpointError(StateError):
    """检查点错误"""
    pass
```

---

## 7. 使用示例

### 7.1 基础状态管理

```python
"""基础状态管理示例"""

async def basic_state_usage():
    # 初始化状态管理器
    state_manager = StateManager(
        config=StateConfig(),
        storage=storage_manager,
        event_bus=event_bus
    )
    
    # 启动状态管理器
    await state_manager.start()
    
    # 访问各子管理器
    print(f"当前情绪: {state_manager.emotion.main_mood}")
    print(f"当前能量: {state_manager.energy.value}")
    print(f"当前饥饿度: {state_manager.hunger.value}")
    print(f"当前好感度: {state_manager.affinity.value} (Lv.{state_manager.affinity.level})")
    print(f"当前金币: {state_manager.coins.value}")
    
    # 修改状态
    state_manager.energy.subtract(10, "用户互动")
    state_manager.affinity.add(5, "完成对话")
    
    # 获取Prompt修饰
    modifiers = state_manager.get_prompt_modifiers()
    print(f"Prompt修饰: {modifiers}")
    
    # 获取行为修饰
    behavior = state_manager.get_behavior_modifiers()
    print(f"行为修饰: {behavior}")
    
    # 保存状态
    await state_manager.save()
    
    # 停止状态管理器
    await state_manager.stop()
```

### 7.2 情绪状态机使用

```python
"""情绪状态机使用示例"""

async def emotion_state_machine_usage():
    emotion = EmotionStateMachine(
        config=EmotionConfig(),
        event_bus=event_bus
    )
    
    # 获取当前状态
    print(f"当前情绪: {emotion.main_mood}")
    print(f"子状态: {emotion.sub_mood}")
    print(f"强度: {emotion.intensity}")
    
    # 规则层转换（硬约束）
    # 能量低于20，强制转换到Tired
    new_state = emotion.apply_rule_transition(
        energy=15,
        hour=23,
        idle_minutes=10,
        is_sleeping=False
    )
    if new_state:
        print(f"规则层触发转换到: {new_state}")
    
    # LLM层建议（软决策）
    # 仅在规则层未触发且状态允许覆盖时生效
    success = emotion.apply_llm_suggestion(
        emotion_tag="happy",
        intensity=0.8,
        context={"interaction": "positive"}
    )
    print(f"LLM建议是否生效: {success}")
    
    # 手动转换
    if emotion.can_transition_to(MoodState.HAPPY):
        emotion.transition_to(
            target_state=MoodState.HAPPY,
            reason="用户抚摸",
            sub_state=MoodSubState.CONTENT,
            intensity=0.6
        )
    
    # 获取表情
    expression = emotion.get_expression()
    print(f"当前表情: {expression}")
```

### 7.3 检查点与恢复

```python
"""检查点与恢复示例"""

async def checkpoint_usage():
    checkpoint_manager = CheckpointManager(
        config=CheckpointConfig(),
        state_store=state_store
    )
    
    # 启动定时保存
    await checkpoint_manager.start_timer()
    
    # 检测崩溃恢复
    if await checkpoint_manager.detect_crash_recovery():
        print("检测到上次异常退出，尝试恢复...")
        success = await checkpoint_manager.restore_from_checkpoint()
        if success:
            print("状态恢复成功")
        else:
            print("状态恢复失败，使用默认值")
    
    # 手动创建检查点
    checkpoint = await checkpoint_manager.create_checkpoint(
        trigger=CheckpointTrigger.STATE_CHANGED
    )
    print(f"创建检查点: {checkpoint.id}")
    
    # 对话结束时自动创建检查点
    await checkpoint_manager.on_conversation_end()
    
    # 工具执行成功时自动创建检查点
    await checkpoint_manager.on_tool_success("system_reminder")
    
    # 程序关闭时创建检查点
    await checkpoint_manager.on_shutdown()
    
    # 停止定时保存
    await checkpoint_manager.stop_timer()
```

### 7.4 状态变更监听

```python
"""状态变更监听示例"""

def on_state_changed(event: StateChangedEvent):
    """状态变更回调"""
    print(f"状态变化: {event.change_type}")
    print(f"  旧值: {event.old_value}")
    print(f"  新值: {event.new_value}")
    print(f"  原因: {event.reason}")

def on_mood_transition(event: MoodTransitionEvent):
    """情绪转换回调"""
    print(f"情绪转换: {event.from_state} -> {event.to_state}")
    print(f"  触发: {event.trigger}")
    print(f"  原因: {event.reason}")

def on_level_up(event: LevelUpEvent):
    """等级提升回调"""
    print(f"等级提升: Lv.{event.old_level} -> Lv.{event.new_level}")
    print(f"  解锁: {event.unlocks}")

async def state_listener_usage():
    state_manager = StateManager(...)
    
    # 注册状态变更监听
    state_manager.register_change_listener(on_state_changed)
    
    # 通过事件总线监听特定事件
    event_bus.subscribe("mood_transition", on_mood_transition)
    event_bus.subscribe("level_up", on_level_up)
    
    # 触发状态变化
    state_manager.affinity.add(30, "完成专注任务")
    # -> 触发 on_state_changed
    # -> 如果等级提升，触发 on_level_up
```

---

## 8. 测试要点

### 8.1 单元测试

```python
"""状态系统单元测试要点"""

class TestEmotionStateMachine:
    """情绪状态机测试"""
    
    def test_initial_state(self):
        """测试初始状态"""
        # 默认为 Normal
        
    def test_rule_layer_priority(self):
        """测试规则层优先于LLM层"""
        # energy < 20 时，即使LLM建议Happy也应该是Tired
        
    def test_uncoverridable_states(self):
        """测试不可覆盖状态"""
        # Sleeping 和 Tired_LowEnergy 不可被覆盖
        
    def test_override_conditions(self):
        """测试覆盖条件"""
        # 正面事件强度 >= 0.8 或 连续正面交互 >= 3次
        
    def test_switch_protection(self):
        """测试状态切换保护"""
        # 60秒内不可重复切换到同一状态
        
    def test_inertia(self):
        """测试情绪惯性"""
        # new = current * 0.7 + target * 0.3
        
    def test_decay(self):
        """测试情绪衰减"""
        # Happy 2小时无强化 → Normal


class TestAttributeManagers:
    """属性管理器测试"""
    
    def test_energy_bounds(self):
        """测试能量边界 [0, 100]"""
        
    def test_energy_decay(self):
        """测试能量每小时衰减"""
        
    def test_hunger_increase(self):
        """测试饥饿度每小时增长"""
        
    def test_auto_feed_threshold(self):
        """测试自主觅食阈值 70%"""
        
    def test_affinity_level_thresholds(self):
        """测试好感度等级阈值"""
        
    def test_affinity_min_floor(self):
        """测试好感度下限保护"""
        
    def test_coins_insufficient(self):
        """测试金币不足异常"""


class TestStateStore:
    """状态存储测试"""
    
    def test_single_source_of_truth(self):
        """测试单一数据源"""
        
    def test_change_notification(self):
        """测试变更通知"""
        
    def test_batch_update(self):
        """测试批量更新"""
        
    def test_snapshot_create_restore(self):
        """测试快照创建与恢复"""


class TestCheckpointManager:
    """检查点管理器测试"""
    
    def test_save_on_state_change(self):
        """测试状态变化时保存"""
        
    def test_save_on_conversation_end(self):
        """测试对话结束时保存"""
        
    def test_timer_save(self):
        """测试定时保存"""
        
    def test_crash_recovery(self):
        """测试崩溃恢复"""
        
    def test_backup_restore(self):
        """测试备份恢复"""
```

### 8.2 集成测试

```python
"""状态系统集成测试"""

class TestStateIntegration:
    """状态系统集成测试"""
    
    async def test_emotion_energy_interaction(self):
        """测试情绪与能量联动"""
        # 能量低时情绪应该转换到Tired
        
    async def test_hunger_affinity_interaction(self):
        """测试饥饿与好感度联动"""
        # 自主觅食时好感度应该-3
        
    async def test_full_state_lifecycle(self):
        """测试完整状态生命周期"""
        # 初始化 -> 变化 -> 保存 -> 重启 -> 恢复
        
    async def test_concurrent_state_updates(self):
        """测试并发状态更新"""
        # 多个操作同时修改状态
```

### 8.3 性能测试

| 测试项 | 目标值 |
|--------|--------|
| 状态读取延迟 | <1ms |
| 状态写入延迟 | <5ms |
| 快照创建延迟 | <10ms |
| 检查点保存延迟 | <50ms |
| 状态恢复延迟 | <100ms |
| 内存占用 (状态缓存) | <1MB |

---

## 9. 依赖关系

### 9.1 模块依赖

```
MOD-State
├── MOD-Core (EventBus, ConfigManager, Logger)
├── MOD-Storage (文件持久化)
└── MOD-RustCore (可选: 高性能状态计算)
```

### 9.2 外部依赖

```toml
[dependencies]
pydantic = "^2.10"        # 数据验证
pydantic-settings = "^2.7" # 配置管理
structlog = "^24.4"        # 结构化日志
anyio = "^4.7"             # 异步支持
```

---

## 10. 变更记录

| 版本 | 日期 | 变更说明 |
|------|------|----------|
| v1.0.0 | 2025-12-29 | 初始版本，基于PRD v3.0.3 |

---

> **文档生成**: Claude Opus 4
> **参考来源**: PRD-Rainze.md 0.6a节, TECH-Rainze.md
