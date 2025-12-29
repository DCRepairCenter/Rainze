# MOD-AI: AI服务层模块

> **模块ID**: `rainze.ai`
> **版本**: v1.0.0
> **优先级**: P0
> **依赖**: Core, Storage, RustCore
> **关联PRD**: [PRD-Rainze.md](../PRD-Rainze.md) 0.3, 0.5, 0.5b, 0.5c, 0.6节

---

## 1. 模块概述

### 1.1 职责定义

AI模块是Rainze的智能核心，提供：

- **Prompt构建**: 3层上下文组装、Token预算管理
- **LLM调用**: API调用、重试、超时处理
- **响应策略**: Tier1模板/Tier2规则/Tier3 LLM
- **场景分类**: 事件到响应Tier的映射
- **降级链**: Fallback 1-5级降级策略
- **Embedding**: 文本向量化服务

### 1.2 响应策略架构

```
[用户输入/事件] → [场景分类器] → [Tier判断]
                                    │
        ┌───────────────────────────┼───────────────────────────┐
        ↓                           ↓                           ↓
   [Tier 1]                    [Tier 2]                    [Tier 3]
   模板响应                     规则生成                    LLM生成
   <50ms                       <100ms                     500-2000ms
        │                           │                           │
        └───────────────────────────┴───────────────────────────┘
                                    ↓
                            [降级链 (失败时)]
                    API超时 → Cache → LocalLLM → 规则 → 兜底
```

---

## 2. 目录结构

```
src/rainze/ai/
├── __init__.py
├── prompt/
│   ├── __init__.py
│   ├── builder.py            # Prompt构建器
│   ├── templates.py          # Prompt模板管理
│   └── budget.py             # Token预算管理
├── llm/
│   ├── __init__.py
│   ├── client.py             # LLM客户端抽象
│   ├── providers/
│   │   ├── __init__.py
│   │   ├── anthropic.py      # Anthropic API
│   │   └── openai.py         # OpenAI API
│   └── response_cache.py     # 响应缓存
├── generation/
│   ├── __init__.py
│   ├── strategy.py           # 响应策略管理
│   ├── tier1_template.py     # Tier1模板响应
│   ├── tier2_rule.py         # Tier2规则生成
│   ├── tier3_llm.py          # Tier3 LLM生成
│   └── fallback.py           # 降级链管理
├── scene/
│   ├── __init__.py
│   ├── classifier.py         # 场景分类器
│   └── types.py              # 场景类型定义
├── embedding/
│   ├── __init__.py
│   ├── service.py            # 向量化服务
│   └── providers.py          # Embedding提供者
└── schemas.py                # 配置Schema
```

---

## 3. 类设计

### 3.1 PromptBuilder (Prompt构建器)

```python
# src/rainze/ai/prompt/builder.py

from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from enum import Enum

class PromptMode(Enum):
    """Prompt模式。"""
    LITE = "lite"           # 16k tokens
    STANDARD = "standard"   # 32k tokens
    DEEP = "deep"           # 64k tokens

@dataclass
class PromptContext:
    """Prompt上下文。"""
    # Layer 1: Identity
    system_prompt: str
    user_profile: Dict[str, Any]
    
    # Layer 2: Working Memory
    conversation_history: List[Dict[str, str]]
    current_state: Dict[str, Any]
    environment: Dict[str, Any]
    
    # Layer 3: Long-term Memory
    memory_index: List[Dict[str, Any]]
    memory_fulltext: List[str]
    facts_summary: str
    
    # Scene specific
    scene_type: str
    scene_context: Dict[str, Any]
    
    # Control
    user_input: Optional[str] = None
    inferred_mood: Optional[str] = None

@dataclass
class BuiltPrompt:
    """构建完成的Prompt。"""
    system: str
    messages: List[Dict[str, str]]
    total_tokens: int
    mode: PromptMode

class PromptBuilder:
    """
    增量式Prompt构建器。
    
    支持:
    - 3层上下文组装
    - Token预算管理
    - 场景模板注入
    - 记忆索引策略
    
    Attributes:
        config: 配置管理器
        budget_manager: Token预算管理器
        template_manager: 模板管理器
    """
    
    def __init__(
        self,
        config_manager,
        budget_manager: "TokenBudgetManager",
        template_manager: "PromptTemplateManager"
    ) -> None:
        """初始化Prompt构建器。"""
        ...
    
    async def build(
        self,
        scene_type: str,
        scene_context: Dict[str, Any],
        mode: PromptMode = PromptMode.STANDARD,
        user_input: Optional[str] = None,
        memory_results: Optional[List[Dict]] = None
    ) -> BuiltPrompt:
        """
        构建完整Prompt。
        
        Args:
            scene_type: 场景类型
            scene_context: 场景上下文
            mode: Prompt模式
            user_input: 用户输入
            memory_results: 检索到的记忆
            
        Returns:
            构建完成的Prompt
        """
        ...
    
    async def _load_identity_layer(self) -> tuple[str, Dict[str, Any]]:
        """加载身份层 (Layer 1)。"""
        ...
    
    async def _build_working_memory(
        self,
        scene_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """构建工作记忆 (Layer 2)。"""
        ...
    
    async def _build_memory_index(
        self,
        memory_results: List[Dict]
    ) -> tuple[List[Dict], List[str]]:
        """构建记忆索引 (Layer 3)。"""
        ...
    
    def _inject_scene_instructions(
        self,
        scene_type: str,
        scene_context: Dict[str, Any]
    ) -> str:
        """注入场景指令。"""
        ...
```

### 3.2 TokenBudgetManager (Token预算管理)

```python
# src/rainze/ai/prompt/budget.py

from typing import Dict
from enum import Enum

class TokenBudgetManager:
    """
    Token预算管理器。
    
    根据模式分配各层Token预算，支持动态调整。
    
    Attributes:
        mode: 当前模式
        budgets: 各层预算配置
    """
    
    # 预算配置 (tokens)
    BUDGETS = {
        "lite": {
            "total": 16000,
            "identity": 1500,
            "working_memory": 4000,
            "environment": 500,
            "semantic_summary": 1500,
            "memory_index": 1500,
            "memory_fulltext": 1500,
            "instructions": 500,
            "reserved_output": 5000
        },
        "standard": {
            "total": 32000,
            "identity": 2500,
            "working_memory": 8000,
            "environment": 1000,
            "semantic_summary": 2500,
            "memory_index": 3000,
            "memory_fulltext": 5000,
            "instructions": 1000,
            "reserved_output": 9000
        },
        "deep": {
            "total": 64000,
            "identity": 4000,
            "working_memory": 16000,
            "environment": 2000,
            "semantic_summary": 4000,
            "memory_index": 6000,
            "memory_fulltext": 10000,
            "instructions": 2000,
            "reserved_output": 20000
        }
    }
    
    def __init__(self, mode: str = "standard") -> None:
        """初始化预算管理器。"""
        ...
    
    def get_budget(self, layer: str) -> int:
        """
        获取指定层的Token预算。
        
        Args:
            layer: 层名称
            
        Returns:
            Token预算
        """
        ...
    
    def estimate_tokens(self, text: str) -> int:
        """
        估算文本Token数量。
        
        Args:
            text: 文本内容
            
        Returns:
            估算Token数
        """
        ...
    
    def truncate_to_budget(
        self, 
        text: str, 
        layer: str,
        preserve_end: bool = False
    ) -> str:
        """
        按预算截断文本。
        
        Args:
            text: 原始文本
            layer: 层名称
            preserve_end: 是否保留末尾
            
        Returns:
            截断后的文本
        """
        ...
```

### 3.3 LLMClient (LLM客户端)

```python
# src/rainze/ai/llm/client.py

from typing import Optional, Dict, Any, List, AsyncIterator
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum

class LLMProvider(Enum):
    """LLM提供商。"""
    ANTHROPIC = "anthropic"
    OPENAI = "openai"

@dataclass
class LLMRequest:
    """LLM请求。"""
    system: str
    messages: List[Dict[str, str]]
    model: str
    temperature: float = 0.8
    max_tokens: int = 150
    timeout_seconds: float = 30

@dataclass
class LLMResponse:
    """LLM响应。"""
    content: str
    model: str
    usage: Dict[str, int]
    finish_reason: str
    latency_ms: float

class LLMClient(ABC):
    """
    LLM客户端抽象基类。
    
    定义统一的LLM调用接口。
    """
    
    @abstractmethod
    async def generate(self, request: LLMRequest) -> LLMResponse:
        """
        生成响应。
        
        Args:
            request: LLM请求
            
        Returns:
            LLM响应
            
        Raises:
            LLMTimeoutError: 超时
            LLMRateLimitError: 限流
            LLMAPIError: API错误
        """
        ...
    
    @abstractmethod
    async def generate_stream(
        self, 
        request: LLMRequest
    ) -> AsyncIterator[str]:
        """
        流式生成响应。
        
        Args:
            request: LLM请求
            
        Yields:
            响应文本片段
        """
        ...


class LLMClientFactory:
    """
    LLM客户端工厂。
    
    根据配置创建对应的LLM客户端。
    """
    
    @staticmethod
    def create(
        provider: LLMProvider,
        api_key: str,
        base_url: Optional[str] = None,
        **kwargs
    ) -> LLMClient:
        """
        创建LLM客户端。
        
        Args:
            provider: 提供商
            api_key: API密钥
            base_url: 自定义API地址
            **kwargs: 额外参数
            
        Returns:
            LLM客户端实例
        """
        ...
```

### 3.4 ResponseGenerator (响应生成器)

```python
# src/rainze/ai/generation/strategy.py

from typing import Optional, Dict, Any
from dataclasses import dataclass
from enum import Enum

class ResponseTier(Enum):
    """响应层级。"""
    TIER1_TEMPLATE = 1    # 模板响应
    TIER2_RULE = 2        # 规则生成
    TIER3_LLM = 3         # LLM生成

@dataclass
class GeneratedResponse:
    """生成的响应。"""
    text: str
    emotion_tag: Optional[str] = None
    emotion_intensity: float = 0.5
    action_hint: Optional[str] = None
    tier_used: ResponseTier = ResponseTier.TIER3_LLM
    latency_ms: float = 0
    from_cache: bool = False

class ResponseGenerator:
    """
    响应生成器。
    
    统一管理3个Tier的响应生成策略。
    
    Attributes:
        tier1: Tier1模板生成器
        tier2: Tier2规则生成器
        tier3: Tier3 LLM生成器
        fallback_manager: 降级链管理器
    """
    
    def __init__(
        self,
        tier1: "Tier1TemplateGenerator",
        tier2: "Tier2RuleGenerator",
        tier3: "Tier3LLMGenerator",
        fallback_manager: "FallbackManager"
    ) -> None:
        """初始化响应生成器。"""
        ...
    
    async def generate(
        self,
        scene_type: str,
        scene_context: Dict[str, Any],
        forced_tier: Optional[ResponseTier] = None,
        user_input: Optional[str] = None
    ) -> GeneratedResponse:
        """
        生成响应。
        
        根据场景分类决定使用哪个Tier，
        失败时自动降级。
        
        Args:
            scene_type: 场景类型
            scene_context: 场景上下文
            forced_tier: 强制使用指定Tier
            user_input: 用户输入
            
        Returns:
            生成的响应
        """
        ...
    
    def _determine_tier(self, scene_type: str) -> ResponseTier:
        """根据场景类型确定响应Tier。"""
        ...


class Tier1TemplateGenerator:
    """
    Tier1 模板响应生成器。
    
    用于简单即时交互：点击、拖拽、简单反馈。
    延迟 <50ms，无API调用。
    """
    
    def __init__(self, templates_path: str) -> None:
        """初始化模板生成器。"""
        ...
    
    async def generate(
        self,
        scene_type: str,
        context: Dict[str, Any]
    ) -> GeneratedResponse:
        """
        从模板生成响应。
        
        Args:
            scene_type: 场景类型
            context: 上下文变量
            
        Returns:
            生成的响应
        """
        ...


class Tier2RuleGenerator:
    """
    Tier2 规则生成器。
    
    用于状态驱动场景：整点报时、系统警告。
    延迟 <100ms，无API调用。
    """
    
    def __init__(self, rules_path: str) -> None:
        """初始化规则生成器。"""
        ...
    
    async def generate(
        self,
        scene_type: str,
        context: Dict[str, Any]
    ) -> GeneratedResponse:
        """
        根据规则生成响应。
        
        Args:
            scene_type: 场景类型
            context: 上下文变量
            
        Returns:
            生成的响应
        """
        ...


class Tier3LLMGenerator:
    """
    Tier3 LLM生成器。
    
    用于复杂场景：自由对话、情感分析。
    延迟 500-2000ms，需API调用。
    """
    
    def __init__(
        self,
        llm_client: LLMClient,
        prompt_builder: PromptBuilder,
        response_cache: "ResponseCache"
    ) -> None:
        """初始化LLM生成器。"""
        ...
    
    async def generate(
        self,
        scene_type: str,
        context: Dict[str, Any],
        user_input: Optional[str] = None
    ) -> GeneratedResponse:
        """
        调用LLM生成响应。
        
        Args:
            scene_type: 场景类型
            context: 上下文
            user_input: 用户输入
            
        Returns:
            生成的响应
        """
        ...
    
    def _parse_emotion_tag(self, text: str) -> tuple[str, Optional[str], float]:
        """
        解析情感标签。
        
        格式: [EMOTION:tag:intensity]
        
        Returns:
            (clean_text, emotion_tag, intensity)
        """
        ...
```

### 3.5 FallbackManager (降级链管理)

```python
# src/rainze/ai/generation/fallback.py

from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from enum import Enum

class FallbackLevel(Enum):
    """降级级别。"""
    RESPONSE_CACHE = 1
    LOCAL_LLM = 2
    RULE_GENERATION = 3
    TEMPLATE = 4
    EMERGENCY = 5

@dataclass
class FallbackResult:
    """降级结果。"""
    response: "GeneratedResponse"
    fallback_level: FallbackLevel
    original_error: Optional[Exception] = None

class FallbackManager:
    """
    降级链管理器。
    
    管理Fallback 1-5级降级策略：
    1. Response Cache - 复用历史响应
    2. Local LLM - 本地模型（可选插件）
    3. Rule Generation - 规则生成
    4. Template - 模板响应
    5. Emergency - 预设兜底文本
    
    Attributes:
        response_cache: 响应缓存
        local_llm: 本地LLM（可选）
        tier2: Tier2规则生成器
        tier1: Tier1模板生成器
        emergency_fallbacks: 紧急兜底文本
    """
    
    def __init__(
        self,
        response_cache: "ResponseCache",
        local_llm: Optional["LocalLLMClient"],
        tier2: "Tier2RuleGenerator",
        tier1: "Tier1TemplateGenerator",
        emergency_path: str
    ) -> None:
        """初始化降级链管理器。"""
        ...
    
    async def fallback(
        self,
        scene_type: str,
        context: Dict[str, Any],
        original_error: Exception,
        start_level: FallbackLevel = FallbackLevel.RESPONSE_CACHE
    ) -> FallbackResult:
        """
        执行降级。
        
        按顺序尝试各级降级策略，直到成功。
        
        Args:
            scene_type: 场景类型
            context: 上下文
            original_error: 原始错误
            start_level: 起始降级级别
            
        Returns:
            降级结果
        """
        ...
    
    async def _try_cache(
        self, 
        scene_type: str, 
        context: Dict[str, Any]
    ) -> Optional["GeneratedResponse"]:
        """尝试从缓存获取响应。"""
        ...
    
    async def _try_local_llm(
        self, 
        scene_type: str, 
        context: Dict[str, Any]
    ) -> Optional["GeneratedResponse"]:
        """尝试本地LLM生成。"""
        ...
    
    def _get_emergency_fallback(
        self, 
        scene_type: str
    ) -> "GeneratedResponse":
        """获取紧急兜底响应。"""
        ...
```

### 3.6 SceneClassifier (场景分类器)

```python
# src/rainze/ai/scene/classifier.py

from typing import Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum

class SceneComplexity(Enum):
    """场景复杂度。"""
    SIMPLE = "simple"     # → Tier 1
    MEDIUM = "medium"     # → Tier 2
    COMPLEX = "complex"   # → Tier 3

@dataclass
class ClassifiedScene:
    """分类后的场景。"""
    scene_type: str
    complexity: SceneComplexity
    suggested_tier: int
    context: Dict[str, Any]
    requires_memory: bool = False
    requires_emotion_analysis: bool = False

class SceneClassifier:
    """
    场景分类器。
    
    在调用LLM前判断场景复杂度，
    决定使用哪个响应Tier。
    
    Attributes:
        rules: 分类规则配置
    """
    
    # 场景分类规则
    SCENE_RULES = {
        # SIMPLE场景 → Tier 1
        "click": SceneComplexity.SIMPLE,
        "drag": SceneComplexity.SIMPLE,
        "hover": SceneComplexity.SIMPLE,
        "release": SceneComplexity.SIMPLE,
        "ui_feedback": SceneComplexity.SIMPLE,
        
        # MEDIUM场景 → Tier 2
        "hourly_chime": SceneComplexity.MEDIUM,
        "system_warning": SceneComplexity.MEDIUM,
        "focus_warning": SceneComplexity.MEDIUM,
        "weather_update": SceneComplexity.MEDIUM,
        
        # COMPLEX场景 → Tier 3
        "conversation": SceneComplexity.COMPLEX,
        "idle_chat": SceneComplexity.COMPLEX,
        "random_event": SceneComplexity.COMPLEX,
        "feed_response": SceneComplexity.COMPLEX,
    }
    
    def __init__(self, custom_rules: Optional[Dict] = None) -> None:
        """初始化场景分类器。"""
        ...
    
    def classify(
        self,
        event_type: str,
        context: Dict[str, Any]
    ) -> ClassifiedScene:
        """
        分类场景。
        
        Args:
            event_type: 事件类型
            context: 事件上下文
            
        Returns:
            分类结果
        """
        ...
    
    def _check_memory_required(
        self, 
        context: Dict[str, Any]
    ) -> bool:
        """检查是否需要记忆检索。"""
        ...
    
    def _check_emotion_required(
        self, 
        context: Dict[str, Any]
    ) -> bool:
        """检查是否需要情感分析。"""
        ...
```

### 3.7 EmbeddingService (向量化服务)

```python
# src/rainze/ai/embedding/service.py

from typing import List, Optional
import numpy as np
from abc import ABC, abstractmethod

class EmbeddingProvider(ABC):
    """Embedding提供者抽象基类。"""
    
    @abstractmethod
    async def embed(self, texts: List[str]) -> np.ndarray:
        """
        批量向量化文本。
        
        Args:
            texts: 文本列表
            
        Returns:
            向量数组 (N, dimension)
        """
        ...
    
    @property
    @abstractmethod
    def dimension(self) -> int:
        """向量维度。"""
        ...


class EmbeddingService:
    """
    向量化服务。
    
    管理Embedding提供者，支持降级。
    
    Attributes:
        primary: 主Embedding提供者
        fallback: 降级提供者（本地）
    """
    
    def __init__(
        self,
        primary: EmbeddingProvider,
        fallback: Optional[EmbeddingProvider] = None
    ) -> None:
        """初始化向量化服务。"""
        ...
    
    async def embed_single(self, text: str) -> np.ndarray:
        """
        向量化单个文本。
        
        Args:
            text: 文本
            
        Returns:
            向量 (1, dimension)
        """
        ...
    
    async def embed_batch(
        self, 
        texts: List[str],
        batch_size: int = 32
    ) -> np.ndarray:
        """
        批量向量化。
        
        Args:
            texts: 文本列表
            batch_size: 批次大小
            
        Returns:
            向量数组 (N, dimension)
        """
        ...
    
    @property
    def dimension(self) -> int:
        """当前向量维度。"""
        ...


class OpenAIEmbeddingProvider(EmbeddingProvider):
    """OpenAI Embedding提供者。"""
    
    def __init__(
        self, 
        api_key: str,
        model: str = "text-embedding-3-small"
    ) -> None:
        ...
    
    async def embed(self, texts: List[str]) -> np.ndarray:
        ...
    
    @property
    def dimension(self) -> int:
        return 768


class LocalEmbeddingProvider(EmbeddingProvider):
    """本地Embedding提供者 (Sentence-Transformers)。"""
    
    def __init__(
        self, 
        model_name: str = "all-MiniLM-L6-v2"
    ) -> None:
        ...
    
    async def embed(self, texts: List[str]) -> np.ndarray:
        ...
    
    @property
    def dimension(self) -> int:
        return 384
```

---

## 4. 配置Schema

```python
# src/rainze/ai/schemas.py

from pydantic import BaseModel, Field
from typing import Optional, Dict, List
from enum import Enum

class APIConfig(BaseModel):
    """API配置。"""
    provider: str = "anthropic"
    base_url: Optional[str] = None
    api_key_env: str = "ANTHROPIC_API_KEY"
    default_model: str = "claude-sonnet-4-20250514"
    timeout_seconds: int = Field(default=30, ge=5)

class FallbackAPIConfig(BaseModel):
    """备用API配置。"""
    enable: bool = False
    provider: str = "openai"
    api_key_env: str = "OPENAI_API_KEY"
    default_model: str = "gpt-4o-mini"
    trigger_on: List[str] = ["timeout", "rate_limit", "server_error"]

class RateLimitsConfig(BaseModel):
    """速率限制配置。"""
    requests_per_minute: int = 60
    requests_per_hour: int = 1000
    tokens_per_day: int = 500000
    enable_queue: bool = True
    queue_max_size: int = 10

class GenerationConfig(BaseModel):
    """生成配置。"""
    default_temperature: float = Field(default=0.8, ge=0, le=2)
    default_max_tokens: int = Field(default=150, ge=10)
    tier3_timeout_seconds: int = Field(default=3, ge=1)
    retry_attempts: int = Field(default=2, ge=0)

class EmbeddingConfig(BaseModel):
    """Embedding配置。"""
    provider: str = "openai"
    model: str = "text-embedding-3-small"
    dimension: int = 768
    batch_size: int = 32
    enable_local_fallback: bool = True
    local_model: str = "sentence-transformers/all-MiniLM-L6-v2"

class ResponseCacheConfig(BaseModel):
    """响应缓存配置。"""
    enable: bool = True
    max_entries: int = 100
    similarity_threshold: float = 0.8
    ttl_days: int = 7

class PromptConfig(BaseModel):
    """Prompt配置。"""
    mode: str = Field(default="standard", pattern="^(lite|standard|deep)$")
    memory_index_count: int = 30
    memory_fulltext_count: int = 3
    conversation_history_turns: int = 10

class AIConfig(BaseModel):
    """AI模块总配置 (api_settings.json)。"""
    primary_api: APIConfig = Field(default_factory=APIConfig)
    fallback_api: FallbackAPIConfig = Field(default_factory=FallbackAPIConfig)
    rate_limits: RateLimitsConfig = Field(default_factory=RateLimitsConfig)
    generation: GenerationConfig = Field(default_factory=GenerationConfig)
    embedding: EmbeddingConfig = Field(default_factory=EmbeddingConfig)
    response_cache: ResponseCacheConfig = Field(default_factory=ResponseCacheConfig)
    prompt: PromptConfig = Field(default_factory=PromptConfig)
```

---

## 5. 异常定义

```python
# src/rainze/ai/exceptions.py

from rainze.core.exceptions import RainzeError

class AIError(RainzeError):
    """AI模块基础异常。"""
    pass

class LLMTimeoutError(AIError):
    """LLM调用超时。"""
    pass

class LLMRateLimitError(AIError):
    """LLM限流错误。"""
    pass

class LLMAPIError(AIError):
    """LLM API错误。"""
    def __init__(self, message: str, status_code: int = 0):
        super().__init__(message)
        self.status_code = status_code

class PromptBuildError(AIError):
    """Prompt构建错误。"""
    pass

class EmbeddingError(AIError):
    """向量化错误。"""
    pass

class AllFallbacksFailedError(AIError):
    """所有降级策略都失败。"""
    pass
```

---

## 6. 使用示例

```python
# 响应生成示例
from rainze.ai import ResponseGenerator, SceneClassifier

async def handle_user_input(user_input: str):
    classifier = SceneClassifier()
    generator = ResponseGenerator(...)
    
    # 分类场景
    scene = classifier.classify("conversation", {"user_input": user_input})
    
    # 生成响应
    response = await generator.generate(
        scene_type=scene.scene_type,
        scene_context=scene.context,
        user_input=user_input
    )
    
    return response.text, response.emotion_tag
```

---

## 7. 测试要点

| 测试类型 | 测试内容 |
|---------|---------|
| 单元测试 | PromptBuilder各层构建 |
| 单元测试 | SceneClassifier分类准确性 |
| 单元测试 | 降级链各级触发 |
| 集成测试 | LLM调用端到端 |
| 性能测试 | Tier1响应 <50ms |
| 性能测试 | Tier2响应 <100ms |

---

## 8. 依赖清单

```toml
anthropic = ">=0.40"
openai = ">=1.58"
httpx = ">=0.28"
sentence-transformers = ">=3.3"
tiktoken = ">=0.8"  # Token估算
```

---

## 9. 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| v1.0.0 | 2025-12-29 | 初始版本 |
