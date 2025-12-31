"""
配置 Schema 定义
Configuration Schema Definitions

本模块定义应用配置的 Pydantic 模型。
This module defines Pydantic models for application configuration.

Reference:
    - MOD: .github/prds/modules/MOD-Core.md §5

Author: Rainze Team
Created: 2025-12-30
"""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, Field

__all__ = [
    "LoggingConfig",
    "PerformanceConfig",
    "AppConfig",
    "GUIConfig",
]


class LoggingConfig(BaseModel):
    """
    日志配置
    Logging configuration
    """

    level: str = Field(
        default="INFO",
        pattern="^(DEBUG|INFO|WARNING|ERROR)$",
        description="日志级别 / Log level",
    )
    log_dir: Path = Field(
        default=Path("./data/logs"),
        description="日志文件目录 / Log file directory",
    )
    json_format: bool = Field(
        default=True,
        description="是否使用 JSON 格式 / Whether to use JSON format",
    )
    max_file_size_mb: int = Field(
        default=10,
        ge=1,
        le=100,
        description="单个日志文件最大大小 (MB) / Max file size in MB",
    )
    retention_days: int = Field(
        default=7,
        ge=1,
        le=90,
        description="日志保留天数 / Log retention days",
    )


class PerformanceConfig(BaseModel):
    """
    性能配置
    Performance configuration
    """

    event_queue_size: int = Field(
        default=1000,
        ge=100,
        description="事件队列大小 / Event queue size",
    )
    config_cache_ttl_seconds: int = Field(
        default=300,
        ge=60,
        description="配置缓存 TTL (秒) / Config cache TTL in seconds",
    )
    startup_timeout_seconds: int = Field(
        default=30,
        ge=10,
        description="启动超时 (秒) / Startup timeout in seconds",
    )
    shutdown_timeout_seconds: int = Field(
        default=10,
        ge=5,
        description="关闭超时 (秒) / Shutdown timeout in seconds",
    )


class AppConfig(BaseModel):
    """
    应用全局配置 (app_settings.json)
    Application global configuration
    """

    app_name: str = Field(
        default="Rainze",
        description="应用名称 / Application name",
    )
    version: str = Field(
        default="0.1.0",
        description="应用版本 / Application version",
    )
    debug: bool = Field(
        default=False,
        description="调试模式 / Debug mode",
    )
    data_dir: Path = Field(
        default=Path("./data"),
        description="数据目录 / Data directory",
    )
    config_dir: Path = Field(
        default=Path("./config"),
        description="配置目录 / Config directory",
    )
    logging: LoggingConfig = Field(
        default_factory=LoggingConfig,
        description="日志配置 / Logging config",
    )
    performance: PerformanceConfig = Field(
        default_factory=PerformanceConfig,
        description="性能配置 / Performance config",
    )


class WindowConfig(BaseModel):
    """
    窗口配置
    Window configuration
    """

    default_width: int = Field(default=200, ge=50, le=800)
    default_height: int = Field(default=200, ge=50, le=800)
    default_position: str = Field(default="bottom_right")
    stay_on_top: bool = Field(default=True)
    enable_transparency: bool = Field(default=True)
    opacity: float = Field(default=1.0, ge=0.0, le=1.0)


class PhysicsConfig(BaseModel):
    """
    物理配置
    Physics configuration
    """

    enable_gravity: bool = Field(default=True)
    gravity_acceleration: float = Field(default=9.8)
    fall_animation_ms: int = Field(default=500)
    edge_snap_distance_px: int = Field(default=50)
    edge_snap_enabled: bool = Field(default=True)


class ChatBubbleConfig(BaseModel):
    """
    聊天气泡配置
    Chat bubble configuration
    """

    show_feedback_buttons: bool = Field(default=False)
    auto_hide_ms: int = Field(default=10000)
    typing_speed_ms: int = Field(default=50)
    max_width: int = Field(default=300)
    opacity: float = Field(default=0.95, ge=0.0, le=1.0)


class SystemTrayConfig(BaseModel):
    """
    系统托盘配置
    System tray configuration
    """

    enable: bool = Field(default=True)
    show_notifications: bool = Field(default=True)
    notification_duration_ms: int = Field(default=3000)
    minimize_to_tray_on_close: bool = Field(default=True)


class GUIConfig(BaseModel):
    """
    GUI 配置 (gui_settings.json)
    GUI configuration
    """

    window: WindowConfig = Field(default_factory=WindowConfig)
    physics: PhysicsConfig = Field(default_factory=PhysicsConfig)
    chat_bubble: ChatBubbleConfig = Field(default_factory=ChatBubbleConfig)
    system_tray: SystemTrayConfig = Field(default_factory=SystemTrayConfig)
