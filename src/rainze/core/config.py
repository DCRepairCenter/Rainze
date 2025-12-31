"""
配置管理器
Configuration Manager

本模块提供配置文件的加载、验证、缓存和热重载功能。
This module provides config loading, validation, caching, and hot-reload.

Reference:
    - MOD: .github/prds/modules/MOD-Core.md §3.2

Author: Rainze Team
Created: 2025-12-30
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable, Dict, Optional, Type, TypeVar

from pydantic import BaseModel, ValidationError

from .exceptions import ConfigError

__all__ = ["ConfigManager"]

T = TypeVar("T", bound=BaseModel)


class ConfigManager:
    """
    配置管理器
    Configuration Manager

    负责加载、验证、缓存配置文件。
    Responsible for loading, validating, caching config files.

    Attributes:
        config_dir: 配置文件目录 / Config file directory
        _cache: 已加载的配置缓存 / Loaded config cache
        _watchers: 文件监视回调 / File watcher callbacks

    Example:
        >>> config = ConfigManager(Path("./config"))
        >>> app_config = config.load("app_settings.json", AppConfig)
        >>> print(app_config.app_name)
        Rainze
    """

    def __init__(self, config_dir: Path) -> None:
        """
        初始化配置管理器
        Initialize config manager

        Args:
            config_dir: 配置文件根目录 / Config file root directory
        """
        self.config_dir = config_dir
        self._cache: Dict[str, Any] = {}
        self._raw_cache: Dict[str, Dict[str, Any]] = {}
        self._watchers: Dict[str, list[Callable[[str], None]]] = {}

    def load(
        self,
        filename: str,
        model: Type[T],
        use_cache: bool = True,
    ) -> T:
        """
        加载并验证配置文件
        Load and validate config file

        Args:
            filename: 配置文件名 / Config filename (e.g., "api_settings.json")
            model: Pydantic 模型类 / Pydantic model class
            use_cache: 是否使用缓存 / Whether to use cache

        Returns:
            验证后的配置对象 / Validated config object

        Raises:
            ConfigError: 文件不存在或验证失败 / File not found or validation failed
        """
        cache_key = f"{filename}:{model.__name__}"

        # 检查缓存 / Check cache
        if use_cache and cache_key in self._cache:
            return self._cache[cache_key]

        # 加载原始数据 / Load raw data
        raw_data = self.get_raw(filename)

        # 验证数据 / Validate data
        try:
            config = model.model_validate(raw_data)
        except ValidationError as e:
            raise ConfigError(
                f"Validation failed: {e}",
                filename=filename,
            ) from e

        # 缓存结果 / Cache result
        if use_cache:
            self._cache[cache_key] = config

        return config

    def reload(self, filename: str) -> None:
        """
        强制重新加载配置文件
        Force reload config file

        清除缓存并通知所有监视器。
        Clear cache and notify all watchers.

        Args:
            filename: 配置文件名 / Config filename
        """
        # 清除相关缓存 / Clear related cache
        keys_to_remove = [k for k in self._cache if k.startswith(f"{filename}:")]
        for key in keys_to_remove:
            del self._cache[key]

        if filename in self._raw_cache:
            del self._raw_cache[filename]

        # 通知监视器 / Notify watchers
        if filename in self._watchers:
            for callback in self._watchers[filename]:
                try:
                    callback(filename)
                except Exception:
                    pass  # 忽略回调错误 / Ignore callback errors

    def watch(
        self,
        filename: str,
        callback: Callable[[str], None],
    ) -> Callable[[], None]:
        """
        监视配置文件变化
        Watch config file changes

        Args:
            filename: 配置文件名 / Config filename
            callback: 变化时的回调函数 / Callback on change

        Returns:
            取消监视的函数 / Unwatch function
        """
        if filename not in self._watchers:
            self._watchers[filename] = []

        self._watchers[filename].append(callback)

        def unwatch() -> None:
            if filename in self._watchers:
                self._watchers[filename] = [
                    c for c in self._watchers[filename] if c != callback
                ]

        return unwatch

    def get_raw(self, filename: str) -> Dict[str, Any]:
        """
        获取原始 JSON 数据（不经过 Pydantic 验证）
        Get raw JSON data (without Pydantic validation)

        Args:
            filename: 配置文件名 / Config filename

        Returns:
            原始字典数据 / Raw dict data

        Raises:
            ConfigError: 文件不存在或解析失败 / File not found or parse failed
        """
        # 检查缓存 / Check cache
        if filename in self._raw_cache:
            return self._raw_cache[filename]

        # 构建路径 / Build path
        file_path = self.config_dir / filename

        if not file_path.exists():
            raise ConfigError(
                f"Config file not found: {file_path}",
                filename=filename,
            )

        # 读取并解析 / Read and parse
        try:
            with open(file_path, encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            raise ConfigError(
                f"JSON parse error: {e}",
                filename=filename,
            ) from e

        # 缓存 / Cache
        self._raw_cache[filename] = data
        return data

    def save(self, filename: str, data: BaseModel) -> None:
        """
        保存配置到文件
        Save config to file

        Args:
            filename: 配置文件名 / Config filename
            data: Pydantic 模型实例 / Pydantic model instance
        """
        file_path = self.config_dir / filename

        # 确保目录存在 / Ensure directory exists
        file_path.parent.mkdir(parents=True, exist_ok=True)

        # 写入文件 / Write file
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(
                data.model_dump(),
                f,
                ensure_ascii=False,
                indent=2,
            )

        # 更新缓存 / Update cache
        self._raw_cache[filename] = data.model_dump()
        cache_key = f"{filename}:{type(data).__name__}"
        self._cache[cache_key] = data

    def exists(self, filename: str) -> bool:
        """
        检查配置文件是否存在
        Check if config file exists

        Args:
            filename: 配置文件名 / Config filename

        Returns:
            是否存在 / Whether exists
        """
        return (self.config_dir / filename).exists()

    def get_or_default(
        self,
        filename: str,
        model: Type[T],
        default_factory: Optional[Callable[[], T]] = None,
    ) -> T:
        """
        获取配置或返回默认值
        Get config or return default

        Args:
            filename: 配置文件名 / Config filename
            model: Pydantic 模型类 / Pydantic model class
            default_factory: 默认值工厂函数 / Default value factory

        Returns:
            配置对象或默认值 / Config object or default
        """
        try:
            return self.load(filename, model)
        except ConfigError:
            if default_factory:
                return default_factory()
            return model()  # type: ignore[call-arg]
