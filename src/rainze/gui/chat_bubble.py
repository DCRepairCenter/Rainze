"""
聊天气泡组件
Chat Bubble Component

本模块提供桌宠的对话气泡显示功能。
This module provides chat bubble display for the pet.

Reference:
    - MOD: .github/prds/modules/MOD-GUI.md §3.4
    - PRD: §0.3 混合响应策略

Author: Rainze Team
Created: 2025-12-30
Updated: 2025-12-31 - 使用外部 QSS 样式
"""

from __future__ import annotations

import logging
from typing import Optional

from PySide6.QtCore import QPoint, QPropertyAnimation, Qt, QTimer, Signal
from PySide6.QtGui import QMouseEvent
from PySide6.QtWidgets import (
    QGraphicsOpacityEffect,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from .transparent_widget import TransparentWidget

logger = logging.getLogger(__name__)

__all__ = ["ChatBubble"]


class ChatBubble(TransparentWidget):
    """
    聊天气泡组件
    Chat Bubble Component

    显示桌宠的对话文本，支持打字机效果。
    Displays pet's dialogue text with typewriter effect.

    Attributes:
        _text_label: 文本标签 / Text label
        _typing_timer: 打字机效果定时器 / Typing effect timer
        _auto_hide_timer: 自动隐藏定时器 / Auto hide timer
        _current_text: 当前完整文本 / Current full text
        _displayed_chars: 已显示字符数 / Displayed character count

    Signals:
        typing_started: 开始打字效果 / Typing started
        typing_finished: 打字效果完成 / Typing finished
        feedback_given: 用户给出反馈 (is_positive) / Feedback given
        bubble_clicked: 气泡被点击 / Bubble clicked
        hidden_signal: 气泡隐藏 / Bubble hidden
    """

    # 信号定义 / Signal definitions
    typing_started: Signal = Signal()
    typing_finished: Signal = Signal()
    feedback_given: Signal = Signal(bool)
    bubble_clicked: Signal = Signal()
    hidden_signal: Signal = Signal()

    def __init__(
        self,
        parent: Optional[QWidget] = None,
        *,
        show_feedback_buttons: bool = False,
        auto_hide_ms: int = 10000,
        typing_speed_ms: int = 50,
        max_width: int = 300,
    ) -> None:
        """
        初始化聊天气泡
        Initialize chat bubble

        Args:
            parent: 父窗口 / Parent widget
            show_feedback_buttons: 是否显示反馈按钮 / Show feedback buttons
            auto_hide_ms: 自动隐藏时间 (毫秒)，0 表示不自动隐藏
                          Auto hide time in ms, 0 = no auto hide
            typing_speed_ms: 打字机效果速度 (毫秒/字符)
                             Typing speed in ms per character
            max_width: 最大宽度 / Maximum width
        """
        super().__init__(parent, enable_drag=False, stay_on_top=True)

        # 配置 / Configuration
        self._show_feedback_buttons = show_feedback_buttons
        self._auto_hide_ms = auto_hide_ms
        self._typing_speed_ms = typing_speed_ms
        self._max_width = max_width

        # 状态 / State
        self._current_text: str = ""
        self._displayed_chars: int = 0
        self._is_typing: bool = False

        # UI 组件将在 setup_ui() 中初始化 / UI components will be initialized in setup_ui()
        # 使用占位符避免 None，因为 setup_ui() 会立即调用
        # Use placeholder to avoid None since setup_ui() is called immediately
        self._text_label: QLabel = QLabel()
        self._like_button: QPushButton | None = None
        self._dislike_button: QPushButton | None = None

        # 定时器 / Timers
        self._typing_timer = QTimer(self)
        self._typing_timer.timeout.connect(self._on_typing_tick)

        self._auto_hide_timer = QTimer(self)
        self._auto_hide_timer.setSingleShot(True)
        self._auto_hide_timer.timeout.connect(self._on_auto_hide)

        # 动画效果 / Animation effects
        self._opacity_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self._opacity_effect)
        self._opacity_effect.setOpacity(1.0)

        # 设置 UI / Setup UI
        self.setup_ui()
        self.setup_style()

        # 初始隐藏 / Initially hidden
        self.hide()

    def setup_ui(self) -> None:
        """
        初始化 UI 布局
        Initialize UI layout
        """
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 10, 15, 10)
        layout.setSpacing(8)

        # 文本标签 / Text label
        self._text_label = QLabel(self)
        self._text_label.setWordWrap(True)
        self._text_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self._text_label.setMaximumWidth(self._max_width)
        layout.addWidget(self._text_label)

        # 反馈按钮 / Feedback buttons
        if self._show_feedback_buttons:
            button_layout = QHBoxLayout()
            button_layout.setSpacing(10)

            self._like_button = QPushButton("👍")
            self._like_button.setFixedSize(30, 30)
            self._like_button.clicked.connect(self._on_like_clicked)
            button_layout.addWidget(self._like_button)

            self._dislike_button = QPushButton("👎")
            self._dislike_button.setFixedSize(30, 30)
            self._dislike_button.clicked.connect(self._on_dislike_clicked)
            button_layout.addWidget(self._dislike_button)

            button_layout.addStretch()
            layout.addLayout(button_layout)

        self.adjustSize()

    def setup_style(self) -> None:
        """
        设置气泡样式（从外部 QSS 文件加载）
        Setup bubble style (load from external QSS file)

        配置圆角背景、半透明效果、阴影效果。
        Configure rounded background, translucent effect, shadow.
        """
        try:
            from rainze.gui.styles import load_styles
            style = load_styles("base", "chat_bubble")
            self.setStyleSheet(style)
            logger.debug("ChatBubble 样式加载成功")
        except Exception as e:
            logger.warning(f"加载外部样式失败，使用内联样式: {e}")
            # 内联样式作为后备 / Inline style as fallback
            self.setStyleSheet(
                """
                ChatBubble {
                    background-color: rgba(255, 255, 255, 0.95);
                    border-radius: 15px;
                    border: 1px solid rgba(0, 0, 0, 0.1);
                }
                QLabel {
                    color: #333333;
                    font-size: 14px;
                    background: transparent;
                }
                QPushButton {
                    background-color: transparent;
                    border: none;
                    font-size: 16px;
                }
                QPushButton:hover {
                    background-color: rgba(0, 0, 0, 0.05);
                    border-radius: 15px;
                }
                """
            )

    def show_text(
        self,
        text: str,
        *,
        use_typing_effect: bool = True,
        anchor_point: Optional[QPoint] = None,
    ) -> None:
        """
        显示文本
        Show text

        Args:
            text: 要显示的文本 / Text to show
            use_typing_effect: 是否使用打字机效果 / Use typing effect
            anchor_point: 锚点位置 (气泡尾巴指向的点) / Anchor point
        """
        self._current_text = text
        self._displayed_chars = 0

        # 更新位置 / Update position
        if anchor_point:
            self.update_position(anchor_point)

        # 重置透明度（fade_out 后需要）/ Reset opacity (needed after fade_out)
        self._opacity_effect.setOpacity(1.0)

        # 显示窗口 / Show window
        self.show()
        self.raise_()

        # 开始打字效果 / Start typing effect
        if use_typing_effect and text:
            self._start_typing_effect(text)
        else:
            self._finish_typing()

        # 启动自动隐藏 / Start auto hide
        if self._auto_hide_ms > 0:
            self._start_auto_hide_timer()

    def _start_typing_effect(self, text: str) -> None:
        """
        开始打字机效果
        Start typing effect

        Args:
            text: 完整文本 / Full text
        """
        self._is_typing = True
        self._displayed_chars = 0
        self._text_label.setText("")
        self.typing_started.emit()
        self._typing_timer.start(self._typing_speed_ms)

    def _on_typing_tick(self) -> None:
        """
        打字机效果 tick
        Typing effect tick
        """
        if self._displayed_chars < len(self._current_text):
            self._displayed_chars += 1
            self._text_label.setText(self._current_text[: self._displayed_chars])
            self.adjustSize()
        else:
            self._finish_typing()

    def _finish_typing(self) -> None:
        """
        完成打字效果
        Finish typing effect
        """
        self._typing_timer.stop()
        self._is_typing = False
        self._text_label.setText(self._current_text)
        self.adjustSize()
        self.typing_finished.emit()

    def skip_typing(self) -> None:
        """
        跳过打字效果，直接显示完整文本
        Skip typing effect, show full text immediately
        """
        if self._is_typing:
            self._finish_typing()

    def update_position(self, anchor: QPoint) -> None:
        """
        更新气泡位置
        Update bubble position

        根据锚点位置和屏幕边界调整气泡位置。
        Adjust position based on anchor and screen bounds.

        Args:
            anchor: 锚点位置 / Anchor point
        """
        # 气泡在锚点上方 / Bubble above anchor
        x = anchor.x() - self.width() // 2
        y = anchor.y() - self.height() - 20

        # 确保不超出屏幕 / Ensure within screen
        screen = self.get_screen_geometry()
        x = max(10, min(x, screen.width() - self.width() - 10))
        y = max(10, y)

        self.move(x, y)

    def set_auto_hide(self, duration_ms: int) -> None:
        """
        设置自动隐藏时间
        Set auto hide duration

        Args:
            duration_ms: 毫秒，0 表示不自动隐藏 / Ms, 0 = no auto hide
        """
        self._auto_hide_ms = duration_ms

    def _start_auto_hide_timer(self) -> None:
        """
        启动自动隐藏定时器
        Start auto hide timer
        """
        self._auto_hide_timer.stop()
        if self._auto_hide_ms > 0:
            self._auto_hide_timer.start(self._auto_hide_ms)

    def _on_auto_hide(self) -> None:
        """
        自动隐藏回调
        Auto hide callback
        """
        self.fade_out()

    def _on_like_clicked(self) -> None:
        """
        点赞按钮点击
        Like button clicked
        """
        self.feedback_given.emit(True)

    def _on_dislike_clicked(self) -> None:
        """
        点踩按钮点击
        Dislike button clicked
        """
        self.feedback_given.emit(False)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        """
        鼠标点击事件
        Mouse press event
        """
        if event.button() == Qt.MouseButton.LeftButton:
            if self._is_typing:
                self.skip_typing()
            else:
                self.bubble_clicked.emit()
        super().mousePressEvent(event)

    def fade_in(self, duration_ms: int = 200) -> None:
        """
        淡入动画
        Fade in animation

        Args:
            duration_ms: 动画时长 / Animation duration
        """
        self._opacity_effect.setOpacity(0.0)
        self.show()

        anim = QPropertyAnimation(self._opacity_effect, b"opacity", self)
        anim.setDuration(duration_ms)
        anim.setStartValue(0.0)
        anim.setEndValue(1.0)
        anim.start()

    def fade_out(self, duration_ms: int = 200) -> None:
        """
        淡出动画
        Fade out animation

        Args:
            duration_ms: 动画时长 / Animation duration
        """
        anim = QPropertyAnimation(self._opacity_effect, b"opacity", self)
        anim.setDuration(duration_ms)
        anim.setStartValue(1.0)
        anim.setEndValue(0.0)
        anim.finished.connect(self._on_fade_out_finished)
        anim.start()

    def _on_fade_out_finished(self) -> None:
        """
        淡出完成回调
        Fade out finished callback
        """
        self.hide()
        self.hidden_signal.emit()

    def clear(self) -> None:
        """
        清空文本并隐藏
        Clear text and hide
        """
        self._typing_timer.stop()
        self._auto_hide_timer.stop()
        self._current_text = ""
        self._displayed_chars = 0
        self._text_label.setText("")
        self.hide()
