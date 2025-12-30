# MOD-Animation - 动画系统模块

> **模块版本**: v1.0.0
> **创建时间**: 2025-12-30
> **关联PRD**: PRD-Rainze.md v3.1.0 §0.14
> **关联技术栈**: TECH-Rainze.md v1.0.1
> **模块层级**: 应用层 (Application Layer)
> **优先级**: P0 (核心必需)
> **依赖模块**: Core, State

---

## 1. 模块概述

### 1.1 职责定义

| 维度 | 说明 |
|------|------|
| **核心职责** | 管理桌宠的6层动画系统，包括动画资源加载、状态机、帧渲染、表情控制、口型同步 |
| **技术栈** | PySide6 QPropertyAnimation、QStateMachine、帧动画 |
| **对外接口** | AnimationController、ExpressionManager、LipSyncManager |
| **依赖模块** | Core (事件总线)、State (情绪状态) |
| **被依赖于** | GUI (渲染层)、AI (情感标签) |

### 1.2 6层动画架构

```
┌─────────────────────────────────────────────────────────┐
│ Layer 5: LipSync (口型层)                               │
│   - 嘴型动画 (A, I, U, E, O, 闭嘴)                      │
│   - 优先级: 最高，覆盖Layer 2嘴部                       │
├─────────────────────────────────────────────────────────┤
│ Layer 4: Effect (特效层)                                │
│   - 粒子效果 (星星、爱心、汗滴)                         │
│   - 优先级: 高，可与任何状态叠加                        │
├─────────────────────────────────────────────────────────┤
│ Layer 3: Action (动作层)                                │
│   - 肢体动作 (挥手、跳跃、拥抱)                         │
│   - 事件触发，结束后返回Idle                            │
├─────────────────────────────────────────────────────────┤
│ Layer 2: Expression (表情层)                            │
│   - 眼睛、眉毛、嘴巴表情                                │
│   - 根据emotion_tag切换                                 │
├─────────────────────────────────────────────────────────┤
│ Layer 1: Idle (待机层)                                  │
│   - 待机动画循环 (呼吸、微动)                           │
│   - 持续播放                                            │
├─────────────────────────────────────────────────────────┤
│ Layer 0: Base (基础层)                                  │
│   - 角色主体、服装                                      │
│   - 换装时变化                                          │
└─────────────────────────────────────────────────────────┘
```

### 1.3 PRD映射

| PRD章节 | 内容概要 | 本模块覆盖 |
|---------|----------|------------|
| §0.14 动画系统架构 | 6层动画、情感映射、口型同步 | ✅ 完整覆盖 |
| §0.5c 输出格式 | 情感标签解析 [EMOTION:tag:intensity] | 表情触发 |
| §0.6a 状态系统 | 情绪状态 → 表情映射 | 表情层控制 |
| 第一部分 §15 | 昼夜作息系统 | 睡眠动画 |
| 第一部分 §12 | 基础物理与交互 | 拖拽/边缘动画 |

---

## 2. 目录结构

```
src/rainze/animation/
├── __init__.py
├── controller.py           # AnimationController 动画主控制器
├── state_machine.py        # AnimationStateMachine 动画状态机
├── layers/                 # 动画层实现
│   ├── __init__.py
│   ├── base_layer.py       # AnimationLayer 基类
│   ├── base.py             # BaseLayer 基础层 (Layer 0)
│   ├── idle.py             # IdleLayer 待机层 (Layer 1)
│   ├── expression.py       # ExpressionLayer 表情层 (Layer 2)
│   ├── action.py           # ActionLayer 动作层 (Layer 3)
│   ├── effect.py           # EffectLayer 特效层 (Layer 4)
│   └── lipsync.py          # LipSyncLayer 口型层 (Layer 5)
├── resources/              # 资源管理
│   ├── __init__.py
│   ├── loader.py           # ResourceLoader 资源加载器
│   ├── cache.py            # AnimationCache 动画缓存
│   └── manifest.py         # AnimationManifest 动画清单
├── frames/                 # 帧动画处理
│   ├── __init__.py
│   ├── sequence.py         # FrameSequence 帧序列
│   ├── player.py           # FramePlayer 帧播放器
│   └── blender.py          # LayerBlender 图层混合
├── expression/             # 表情系统
│   ├── __init__.py
│   ├── manager.py          # ExpressionManager 表情管理器
│   └── mapping.py          # EmotionMapping 情感映射
├── lipsync/                # 口型同步
│   ├── __init__.py
│   ├── manager.py          # LipSyncManager 口型管理器
│   ├── analyzer.py         # AudioAnalyzer 音频分析
│   └── phoneme.py          # PhonemeMapper 音素映射
└── models/                 # 数据模型
    ├── __init__.py
    ├── animation.py        # 动画数据模型
    ├── frame.py            # 帧数据模型
    └── config.py           # 动画配置模型
```

---

## 3. 核心类设计

### 3.1 AnimationController - 动画主控制器

```python
"""动画主控制器

职责:
- 统一管理6个动画层
- 处理层间优先级和混合
- 响应情感标签和状态变化
- 提供给GUI的渲染接口

PRD映射: §0.14 动画系统架构
"""

from typing import TYPE_CHECKING, Optional, Dict, List, Callable
from enum import Enum, auto
from dataclasses import dataclass
from PySide6.QtCore import QObject, Signal, QTimer
from PySide6.QtGui import QPixmap

if TYPE_CHECKING:
    from rainze.core import EventBus
    from rainze.state import StateManager


class AnimationState(Enum):
    """动画状态机状态"""
    IDLE = auto()           # 待机
    TALKING = auto()        # 说话中
    REACTING = auto()       # 表情反应
    ACTING = auto()         # 执行动作
    TRANSITIONING = auto()  # 状态过渡
    SLEEPING = auto()       # 睡眠状态


@dataclass
class AnimationFrame:
    """动画帧数据"""
    pixmap: QPixmap
    duration_ms: int
    metadata: Dict[str, any]


# ⭐ 从 core.contracts 导入统一类型，禁止本模块重复定义
from rainze.core.contracts.emotion import EmotionTag
from rainze.core.observability import Tracer


class AnimationController(QObject):
    """动画主控制器
    
    统一管理6个动画层的渲染和状态转换。
    
    Attributes:
        _layers: 6个动画层实例
        _state_machine: 动画状态机
        _current_state: 当前动画状态
        _event_bus: 事件总线引用
        _state_manager: 状态管理器引用
        _render_timer: 渲染定时器
        _fps: 目标帧率
        
    Signals:
        frame_ready: 新帧准备完成 (QPixmap)
        state_changed: 动画状态变化 (AnimationState)
        action_completed: 动作播放完成 (action_name)
    """
    
    # 信号定义
    frame_ready = Signal(QPixmap)
    state_changed = Signal(AnimationState)
    action_completed = Signal(str)
    
    def __init__(
        self,
        event_bus: "EventBus",
        state_manager: "StateManager",
        resource_path: str,
        fps: int = 30,
    ) -> None:
        """初始化动画控制器
        
        Args:
            event_bus: 事件总线实例
            state_manager: 状态管理器实例
            resource_path: 动画资源根目录
            fps: 目标帧率，默认30
        """
        ...
    
    async def initialize(self) -> None:
        """异步初始化
        
        加载动画资源清单、初始化各层、启动渲染循环
        """
        ...
    
    # ==================== 层控制 ====================
    
    def get_layer(self, layer_index: int) -> "AnimationLayer":
        """获取指定层
        
        Args:
            layer_index: 层索引 (0-5)
            
        Returns:
            动画层实例
        """
        ...
    
    def set_layer_visible(self, layer_index: int, visible: bool) -> None:
        """设置层可见性
        
        Args:
            layer_index: 层索引
            visible: 是否可见
        """
        ...
    
    # ==================== 状态控制 ====================
    
    def get_current_state(self) -> AnimationState:
        """获取当前动画状态"""
        ...
    
    def transition_to(
        self,
        target_state: AnimationState,
        transition_duration_ms: int = 200,
    ) -> None:
        """执行状态转换
        
        Args:
            target_state: 目标状态
            transition_duration_ms: 过渡时长(毫秒)
        """
        ...
    
    # ==================== 表情控制 ====================
    
    def set_expression(
        self,
        emotion_tag: str,
        intensity: float = 0.5,
        duration_ms: Optional[int] = None,
    ) -> None:
        """设置表情
        
        Args:
            emotion_tag: 情感标签 (happy, sad, angry, shy, surprised, etc.)
            intensity: 强度 (0.0-1.0)
            duration_ms: 持续时间，None表示持续到下次变更
        """
        ...
    
    def parse_emotion_tag(self, response_text: str) -> Optional[EmotionTag]:
        """从响应文本中解析情感标签
        
        解析格式: [EMOTION:tag:intensity]
        
        Args:
            response_text: AI响应文本
            
        Returns:
            解析后的情感标签，未找到返回None
        """
        ...
    
    def apply_emotion_tag(self, tag: EmotionTag) -> None:
        """应用情感标签到动画系统
        
        根据intensity自动选择:
        - intensity < 0.3 → 轻微表情
        - 0.3 <= intensity < 0.7 → 标准表情
        - intensity >= 0.7 → 夸张表情 + 特效
        
        Args:
            tag: 解析后的情感标签
        """
        ...
    
    # ==================== 动作控制 ====================
    
    def play_action(
        self,
        action_name: str,
        on_complete: Optional[Callable[[], None]] = None,
    ) -> bool:
        """播放动作
        
        动作播放完成后自动返回Idle状态。
        
        Args:
            action_name: 动作名称 (wave, jump, eat, sleep, etc.)
            on_complete: 完成回调
            
        Returns:
            是否成功开始播放
        """
        ...
    
    def stop_action(self) -> None:
        """停止当前动作，返回Idle"""
        ...
    
    # ==================== 特效控制 ====================
    
    def play_effect(
        self,
        effect_name: str,
        duration_ms: int = 2000,
    ) -> None:
        """播放特效
        
        Args:
            effect_name: 特效名称 (sparkle, heart, tear_drop, anger_mark, etc.)
            duration_ms: 持续时间
        """
        ...
    
    # ==================== 口型同步 ====================
    
    def start_lipsync(self, audio_data: bytes) -> None:
        """开始口型同步
        
        分析音频振幅，实时控制嘴型。
        
        Args:
            audio_data: 音频数据 (WAV格式)
        """
        ...
    
    def start_text_lipsync(self, text: str, duration_ms: int) -> None:
        """基于文本的口型同步
        
        不使用TTS时，根据文本长度模拟口型动画。
        
        Args:
            text: 说话文本
            duration_ms: 预估持续时间
        """
        ...
    
    def stop_lipsync(self) -> None:
        """停止口型同步"""
        ...
    
    # ==================== 渲染 ====================
    
    def render_frame(self) -> QPixmap:
        """渲染当前帧
        
        合成6层动画，返回最终图像。
        
        Returns:
            合成后的帧图像
        """
        ...
    
    def start_render_loop(self) -> None:
        """启动渲染循环"""
        ...
    
    def stop_render_loop(self) -> None:
        """停止渲染循环"""
        ...
    
    # ==================== 资源管理 ====================
    
    def preload_animations(self, categories: List[str]) -> None:
        """预加载动画资源
        
        Args:
            categories: 要预加载的类别列表 (idle, expressions, actions, etc.)
        """
        ...
    
    def change_outfit(self, outfit_name: str) -> bool:
        """切换服装
        
        Args:
            outfit_name: 服装名称
            
        Returns:
            是否成功切换
        """
        ...


### 3.2 AnimationLayer - 动画层基类

```python
"""动画层基类

提供动画层的通用功能:
- 帧序列管理
- 播放控制
- 混合模式设置
"""

from abc import ABC, abstractmethod
from typing import Optional, List
from enum import Enum, auto
from PySide6.QtGui import QPixmap


class BlendMode(Enum):
    """图层混合模式"""
    NORMAL = auto()         # 正常覆盖
    OVERLAY = auto()        # 叠加混合
    ADDITIVE = auto()       # 加法混合


class AnimationLayer(ABC):
    """动画层抽象基类
    
    Attributes:
        _name: 层名称
        _index: 层索引 (0-5)
        _visible: 是否可见
        _blend_mode: 混合模式
        _current_frame: 当前帧
        _frame_sequence: 帧序列
    """
    
    def __init__(
        self,
        name: str,
        index: int,
        blend_mode: BlendMode = BlendMode.NORMAL,
    ) -> None:
        """初始化动画层
        
        Args:
            name: 层名称
            index: 层索引
            blend_mode: 混合模式
        """
        ...
    
    @property
    def name(self) -> str:
        """层名称"""
        ...
    
    @property
    def index(self) -> int:
        """层索引"""
        ...
    
    @property
    def visible(self) -> bool:
        """是否可见"""
        ...
    
    @visible.setter
    def visible(self, value: bool) -> None:
        ...
    
    @abstractmethod
    def get_current_frame(self) -> Optional[QPixmap]:
        """获取当前帧图像
        
        Returns:
            当前帧图像，无有效帧返回None
        """
        ...
    
    @abstractmethod
    def update(self, delta_ms: int) -> None:
        """更新动画状态
        
        Args:
            delta_ms: 距上次更新的毫秒数
        """
        ...
    
    @abstractmethod
    def reset(self) -> None:
        """重置到初始状态"""
        ...
    
    def set_blend_mode(self, mode: BlendMode) -> None:
        """设置混合模式
        
        Args:
            mode: 混合模式
        """
        ...


### 3.3 ExpressionLayer - 表情层 (Layer 2)

```python
"""表情层

管理眼睛、眉毛、嘴巴的表情动画。

PRD映射: §0.14 情感标签映射
"""

from typing import Dict, Optional, List
from dataclasses import dataclass


@dataclass
class ExpressionConfig:
    """表情配置"""
    expression_name: str        # 表情名称
    eye_sprite: str             # 眼睛精灵
    eyebrow_sprite: str         # 眉毛精灵
    mouth_sprite: str           # 嘴巴精灵
    transition_ms: int          # 过渡时间
    

@dataclass  
class ExpressionSet:
    """表情集合"""
    idle: ExpressionConfig
    smile: ExpressionConfig
    sad: ExpressionConfig
    angry: ExpressionConfig
    shy: ExpressionConfig
    surprised: ExpressionConfig
    sleepy: ExpressionConfig
    thinking: ExpressionConfig


class ExpressionLayer(AnimationLayer):
    """表情层实现
    
    Attributes:
        _current_expression: 当前表情
        _target_expression: 目标表情(过渡中)
        _expression_set: 表情集合
        _transition_progress: 过渡进度(0.0-1.0)
        _intensity: 表情强度(影响幅度)
    """
    
    # 情感标签到表情的映射
    EMOTION_MAPPING: Dict[str, str] = {
        "happy": "smile",
        "excited": "smile",  # 使用smile + 特效
        "sad": "sad",
        "angry": "angry",
        "shy": "shy",
        "surprised": "surprised",
        "tired": "sleepy",
        "anxious": "thinking",
        "neutral": "idle",
    }
    
    def __init__(self) -> None:
        """初始化表情层"""
        ...
    
    def set_expression(
        self,
        expression_name: str,
        intensity: float = 0.5,
        transition_ms: int = 200,
    ) -> None:
        """设置表情
        
        Args:
            expression_name: 表情名称
            intensity: 强度 (0.0-1.0)
            transition_ms: 过渡时间
        """
        ...
    
    def set_by_emotion_tag(self, emotion_tag: str, intensity: float) -> None:
        """根据情感标签设置表情
        
        Args:
            emotion_tag: 情感标签
            intensity: 强度
        """
        ...
    
    def get_current_expression(self) -> str:
        """获取当前表情名称"""
        ...
    
    def start_blink(self) -> None:
        """开始眨眼动画"""
        ...
    
    def get_current_frame(self) -> Optional["QPixmap"]:
        """获取当前帧"""
        ...
    
    def update(self, delta_ms: int) -> None:
        """更新表情状态"""
        ...
    
    def reset(self) -> None:
        """重置到默认表情"""
        ...


### 3.4 LipSyncManager - 口型同步管理器

```python
"""口型同步管理器

支持两种口型同步模式:
1. amplitude: 基于音频振幅
2. phoneme: 基于音素分析
3. text_based: 基于文本模拟

PRD映射: §0.14 LipSync配置
"""

from typing import Optional, Callable, List
from enum import Enum, auto
from dataclasses import dataclass


class LipSyncMode(Enum):
    """口型同步模式"""
    AMPLITUDE = auto()      # 振幅模式
    PHONEME = auto()        # 音素模式
    TEXT_BASED = auto()     # 文本模拟


class MouthShape(Enum):
    """嘴型枚举"""
    CLOSED = "closed"
    A = "A"
    I = "I"
    U = "U"
    E = "E"
    O = "O"


@dataclass
class LipSyncConfig:
    """口型同步配置"""
    mode: LipSyncMode
    amplitude_threshold: float      # 振幅阈值
    sample_rate_ms: int             # 采样间隔(毫秒)
    smoothing_factor: float         # 平滑因子


class LipSyncManager:
    """口型同步管理器
    
    Attributes:
        _config: 口型同步配置
        _mode: 当前模式
        _is_active: 是否激活
        _current_shape: 当前嘴型
        _on_shape_change: 嘴型变化回调
    """
    
    def __init__(self, config: LipSyncConfig) -> None:
        """初始化口型同步管理器
        
        Args:
            config: 配置对象
        """
        ...
    
    def start_amplitude_sync(
        self,
        audio_data: bytes,
        on_shape_change: Callable[[MouthShape], None],
    ) -> None:
        """开始振幅模式同步
        
        分析音频数据的振幅，实时触发嘴型变化。
        
        Args:
            audio_data: WAV音频数据
            on_shape_change: 嘴型变化回调
        """
        ...
    
    def start_text_sync(
        self,
        text: str,
        duration_ms: int,
        on_shape_change: Callable[[MouthShape], None],
    ) -> None:
        """开始文本模式同步
        
        根据文本内容和持续时间模拟口型动画。
        
        Args:
            text: 说话文本
            duration_ms: 持续时间
            on_shape_change: 嘴型变化回调
        """
        ...
    
    def stop(self) -> None:
        """停止口型同步"""
        ...
    
    def get_current_shape(self) -> MouthShape:
        """获取当前嘴型"""
        ...
    
    def analyze_amplitude(self, samples: List[float]) -> MouthShape:
        """分析振幅，返回对应嘴型
        
        Args:
            samples: 音频采样数据
            
        Returns:
            对应的嘴型
        """
        ...


### 3.5 EffectLayer - 特效层 (Layer 4)

```python
"""特效层

管理粒子特效动画，可与任何状态叠加。

PRD映射: §0.14 Layer 4 Effect层
"""

from typing import Optional, Dict, List
from dataclasses import dataclass
from enum import Enum, auto


class EffectType(Enum):
    """特效类型"""
    SPARKLE = "sparkle"         # 星星闪烁
    STARS = "stars"             # 星星环绕
    HEART = "heart"             # 爱心
    TEAR_DROP = "tear_drop"     # 泪滴
    ANGER_MARK = "anger_mark"   # 怒气符号
    QUESTION_MARK = "question_mark"  # 问号
    SWEAT = "sweat"             # 汗滴
    ZZZZZ = "zzzzz"             # 睡眠Z字


@dataclass
class EffectConfig:
    """特效配置"""
    effect_type: EffectType
    sprite_sheet: str           # 精灵图路径
    frame_count: int            # 帧数
    loop: bool                  # 是否循环
    default_duration_ms: int    # 默认持续时间


class EffectLayer(AnimationLayer):
    """特效层实现
    
    Attributes:
        _active_effects: 当前激活的特效列表
        _effect_configs: 特效配置映射
    """
    
    # 情感到特效的映射
    EMOTION_EFFECT_MAPPING: Dict[str, EffectType] = {
        "happy": EffectType.SPARKLE,
        "excited": EffectType.STARS,
        "sad": EffectType.TEAR_DROP,
        "angry": EffectType.ANGER_MARK,
        "shy": EffectType.HEART,
        "confused": EffectType.QUESTION_MARK,
        "anxious": EffectType.SWEAT,
    }
    
    def __init__(self) -> None:
        """初始化特效层"""
        ...
    
    def play_effect(
        self,
        effect_type: EffectType,
        duration_ms: Optional[int] = None,
        position: Optional[tuple[int, int]] = None,
    ) -> None:
        """播放特效
        
        Args:
            effect_type: 特效类型
            duration_ms: 持续时间，None使用默认值
            position: 相对位置，None使用默认位置
        """
        ...
    
    def stop_effect(self, effect_type: EffectType) -> None:
        """停止指定特效
        
        Args:
            effect_type: 特效类型
        """
        ...
    
    def stop_all_effects(self) -> None:
        """停止所有特效"""
        ...
    
    def get_active_effects(self) -> List[EffectType]:
        """获取当前激活的特效列表"""
        ...
    
    def get_current_frame(self) -> Optional["QPixmap"]:
        """获取当前帧（合成所有激活特效）"""
        ...
    
    def update(self, delta_ms: int) -> None:
        """更新特效状态"""
        ...
    
    def reset(self) -> None:
        """清除所有特效"""
        ...


### 3.6 ResourceLoader - 资源加载器

```python
"""动画资源加载器

负责加载和缓存动画资源。

职责:
- 加载动画清单 (animation.json)
- 加载帧序列 (PNG)
- 管理资源缓存
"""

from typing import Dict, List, Optional
from pathlib import Path
from dataclasses import dataclass


@dataclass
class AnimationManifest:
    """动画清单"""
    version: str
    animations: Dict[str, "AnimationDefinition"]


@dataclass
class AnimationDefinition:
    """单个动画定义"""
    name: str
    category: str               # idle, expressions, actions, effects
    frames: List[str]           # 帧文件列表
    frame_duration_ms: int      # 每帧时长
    loop: bool                  # 是否循环
    anchor: tuple[int, int]     # 锚点位置


class ResourceLoader:
    """资源加载器
    
    Attributes:
        _resource_path: 资源根目录
        _manifest: 动画清单
        _cache: 已加载资源缓存
        _max_cache_size: 最大缓存大小
    """
    
    def __init__(
        self,
        resource_path: Path,
        max_cache_size_mb: int = 100,
    ) -> None:
        """初始化资源加载器
        
        Args:
            resource_path: 资源根目录
            max_cache_size_mb: 最大缓存大小(MB)
        """
        ...
    
    def load_manifest(self) -> AnimationManifest:
        """加载动画清单
        
        Returns:
            动画清单对象
        """
        ...
    
    def load_animation(
        self,
        animation_name: str,
    ) -> "FrameSequence":
        """加载动画帧序列
        
        Args:
            animation_name: 动画名称
            
        Returns:
            帧序列对象
        """
        ...
    
    def preload_category(self, category: str) -> None:
        """预加载指定类别的所有动画
        
        Args:
            category: 类别名称 (idle, expressions, actions, effects)
        """
        ...
    
    def get_available_animations(self) -> Dict[str, List[str]]:
        """获取所有可用动画，按类别分组
        
        Returns:
            {category: [animation_names]}
        """
        ...
    
    def clear_cache(self) -> None:
        """清空缓存"""
        ...
    
    def get_cache_stats(self) -> Dict[str, any]:
        """获取缓存统计信息"""
        ...


---

## 4. 配置模型

### 4.1 动画配置 (animation_settings.json)

```python
"""动画配置Pydantic模型"""

from pydantic import BaseModel, Field
from typing import Dict, List, Optional


class LayerConfig(BaseModel):
    """单层配置"""
    name: str
    enabled: bool = True
    blend_mode: str = "overlay"


class EmotionMappingConfig(BaseModel):
    """情感映射配置"""
    expression: str
    effect: Optional[str] = None
    action: Optional[str] = None
    intensity_threshold: float = 0.5


class LipSyncConfig(BaseModel):
    """口型同步配置"""
    enable: bool = True
    mode: str = "amplitude"  # amplitude | phoneme | text_based
    amplitude_threshold: float = 0.3
    sample_rate_ms: int = 50
    mouth_shapes: List[str] = ["closed", "A", "I", "U", "E", "O"]


class TimingConfig(BaseModel):
    """时序配置"""
    expression_transition_ms: int = 200
    action_duration_ms: int = 1000
    effect_duration_ms: int = 2000
    idle_blink_interval_ms: int = 3000


class AnimationSettings(BaseModel):
    """动画系统完整配置"""
    layer_system: Dict[str, LayerConfig]
    emotion_mapping: Dict[str, EmotionMappingConfig]
    lipsync: LipSyncConfig
    timing: TimingConfig
    state_machine: Dict[str, any]


---

## 5. 事件定义

### 5.1 动画相关事件

```python
"""动画系统事件定义"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class AnimationStateChangedEvent:
    """动画状态变化事件"""
    previous_state: "AnimationState"
    current_state: "AnimationState"
    trigger: str


@dataclass
class ExpressionChangedEvent:
    """表情变化事件"""
    previous_expression: str
    current_expression: str
    intensity: float
    source: str  # "emotion_tag" | "state_change" | "manual"


@dataclass
class ActionStartedEvent:
    """动作开始事件"""
    action_name: str
    duration_ms: int


@dataclass
class ActionCompletedEvent:
    """动作完成事件"""
    action_name: str
    was_interrupted: bool


@dataclass
class EffectStartedEvent:
    """特效开始事件"""
    effect_name: str
    duration_ms: int


@dataclass  
class LipSyncStartedEvent:
    """口型同步开始事件"""
    mode: "LipSyncMode"
    duration_ms: Optional[int]


@dataclass
class LipSyncEndedEvent:
    """口型同步结束事件"""
    mode: "LipSyncMode"
```

---

## 6. 依赖与接口

### 6.1 依赖模块

| 模块 | 用途 |
|------|------|
| Core | 事件总线、配置加载 |
| State | 情绪状态订阅 |

### 6.2 对外接口

```python
# 模块导出
from rainze.animation import (
    # 主控制器
    AnimationController,
    AnimationState,
    
    # 表情
    ExpressionLayer,
    ExpressionConfig,
    
    # 口型
    LipSyncManager,
    LipSyncMode,
    MouthShape,
    
    # 特效
    EffectLayer,
    EffectType,
    
    # 资源
    ResourceLoader,
    AnimationManifest,
    
    # 事件
    AnimationStateChangedEvent,
    ExpressionChangedEvent,
    ActionCompletedEvent,
)
```

---

## 7. 使用示例

### 7.1 基本使用

```python
# 初始化
controller = AnimationController(
    event_bus=app.event_bus,
    state_manager=app.state_manager,
    resource_path="./assets/animations",
)
await controller.initialize()

# 设置表情
controller.set_expression("smile", intensity=0.8)

# 播放动作
controller.play_action("wave", on_complete=lambda: print("挥手完成"))

# 播放特效
controller.play_effect("sparkle", duration_ms=3000)

# 开始口型同步
controller.start_text_lipsync("你好，主人！", duration_ms=2000)
```

### 7.2 处理AI响应

```python
# AI响应文本
response_text = "今天天气真好呢~ [EMOTION:happy:0.8]"

# 解析情感标签
tag = controller.parse_emotion_tag(response_text)
if tag:
    # 应用到动画系统
    controller.apply_emotion_tag(tag)
    
# 显示纯文本（不含标签）
clean_text = response_text.replace(tag.raw_text, "").strip() if tag else response_text
```

---

**文档版本历史**:

| 版本 | 日期 | 变更说明 |
|------|------|----------|
| v1.0.0 | 2025-12-30 | 初始版本 |
