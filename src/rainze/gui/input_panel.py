"""
输入面板组件
Input Panel Component

本模块提供用户文本输入功能，支持历史记录浏览。
This module provides text input with history navigation.

Reference:
    - MOD: .github/prds/modules/MOD-GUI.md §3.6
    - PRD: §0.5b 用户主动对话场景

Author: Rainze Team
Created: 2025-12-30
"""

from __future__ import annotations

from typing import TYPE_CHECKING, List, Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QWidget,
)

if TYPE_CHECKING:
    from PySide6.QtCore import QPoint

__all__ = ["InputPanel"]


class InputPanel(QWidget):
    """
    输入面板组件
    Input Panel Component

    提供文本输入框，支持快捷键发送和输入历史浏览。
    Provides text input with hotkey submission and history navigation.

    Attributes:
        _input_field: 输入框 / Input field
        _send_button: 发送按钮 / Send button
        _history: 输入历史 / Input history
        _history_index: 历史索引 / History index
        _max_history: 最大历史记录数 / Max history size
        _temp_input: 临时保存当前输入 / Temporarily saved current input

    Signals:
        message_submitted: 消息提交 (text) / Message submitted
        input_changed: 输入内容变化 (text) / Input changed
        panel_shown: 面板显示 / Panel shown
        panel_hidden: 面板隐藏 / Panel hidden

    Reference:
        PRD §0.5b: 用户主动对话场景
    """

    # 信号定义 / Signal definitions
    message_submitted: Signal = Signal(str)
    input_changed: Signal = Signal(str)
    panel_shown: Signal = Signal()
    panel_hidden: Signal = Signal()

    def __init__(
        self,
        parent: Optional[QWidget] = None,
        *,
        max_history: int = 50,
        placeholder: str = "和我聊聊吧~",
        max_length: int = 500,
        show_send_button: bool = True,
    ) -> None:
        """
        初始化输入面板
        Initialize input panel

        Args:
            parent: 父窗口 / Parent widget
            max_history: 最大历史记录数 / Max history entries
            placeholder: 占位文本 / Placeholder text
            max_length: 最大输入长度 / Max input length
            show_send_button: 是否显示发送按钮 / Show send button
        """
        super().__init__(parent)

        # 配置 / Configuration
        self._max_history = max_history
        self._placeholder = placeholder
        self._max_length = max_length
        self._show_send_button = show_send_button

        # 状态 / State
        self._history: List[str] = []
        self._history_index: int = -1
        self._temp_input: str = ""

        # UI 组件 / UI components
        self._input_field: Optional[QLineEdit] = None
        self._send_button: Optional[QPushButton] = None

        # 设置 UI / Setup UI
        self.setup_ui()
        self.setup_style()

    def setup_ui(self) -> None:
        """
        初始化 UI 布局
        Initialize UI layout
        """
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(8)

        # 输入框 / Input field
        self._input_field = QLineEdit(self)
        self._input_field.setPlaceholderText(self._placeholder)
        self._input_field.setMaxLength(self._max_length)
        self._input_field.textChanged.connect(self._on_text_changed)
        self._input_field.returnPressed.connect(self._submit_message)
        layout.addWidget(self._input_field)

        # 发送按钮 / Send button
        if self._show_send_button:
            self._send_button = QPushButton("发送", self)
            self._send_button.setFixedWidth(60)
            self._send_button.clicked.connect(self._on_send_clicked)
            layout.addWidget(self._send_button)

        self.setFixedHeight(50)

    def setup_style(self) -> None:
        """
        设置样式
        Setup style
        """
        self.setStyleSheet(
            """
            InputPanel {
                background-color: rgba(255, 255, 255, 0.95);
                border-radius: 10px;
                border: 1px solid rgba(0, 0, 0, 0.1);
            }
            QLineEdit {
                background-color: rgba(245, 245, 245, 0.9);
                border: 1px solid rgba(0, 0, 0, 0.1);
                border-radius: 6px;
                padding: 6px 10px;
                font-size: 14px;
                font-family: "Microsoft YaHei", "Segoe UI", sans-serif;
                color: #333333;
            }
            QLineEdit:focus {
                border: 1px solid #4A90D9;
                background-color: white;
            }
            QLineEdit::placeholder {
                color: #999999;
            }
            QPushButton {
                background-color: #4A90D9;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 6px 12px;
                font-size: 13px;
                font-family: "Microsoft YaHei", "Segoe UI", sans-serif;
            }
            QPushButton:hover {
                background-color: #3A7FC8;
            }
            QPushButton:pressed {
                background-color: #2A6EB7;
            }
            QPushButton:disabled {
                background-color: #CCCCCC;
            }
            """
        )

    def set_placeholder(self, text: str) -> None:
        """
        设置占位文本
        Set placeholder text

        Args:
            text: 占位文本 / Placeholder text
        """
        self._placeholder = text
        if self._input_field:
            self._input_field.setPlaceholderText(text)

    def set_max_length(self, length: int) -> None:
        """
        设置最大输入长度
        Set max input length

        Args:
            length: 最大字符数 / Max character count
        """
        self._max_length = length
        if self._input_field:
            self._input_field.setMaxLength(length)

    def get_text(self) -> str:
        """
        获取输入文本
        Get input text

        Returns:
            当前输入的文本 / Current input text
        """
        if self._input_field:
            return self._input_field.text()
        return ""

    def set_text(self, text: str) -> None:
        """
        设置输入文本
        Set input text

        Args:
            text: 文本内容 / Text content
        """
        if self._input_field:
            self._input_field.setText(text)

    def clear(self) -> None:
        """
        清空输入框
        Clear input field
        """
        if self._input_field:
            self._input_field.clear()
        self._history_index = -1
        self._temp_input = ""

    def focus(self) -> None:
        """
        聚焦输入框
        Focus input field
        """
        if self._input_field:
            self._input_field.setFocus()

    def _on_text_changed(self, text: str) -> None:
        """
        文本变化回调
        Text changed callback

        Args:
            text: 当前文本 / Current text
        """
        self.input_changed.emit(text)

    def _on_send_clicked(self) -> None:
        """
        发送按钮点击处理
        Send button click handler
        """
        self._submit_message()

    def _submit_message(self) -> None:
        """
        提交消息
        Submit message

        验证输入 -> 添加到历史 -> 发射信号 -> 清空输入框
        Validate -> Add to history -> Emit signal -> Clear input
        """
        text = self.get_text().strip()

        # 验证非空 / Validate non-empty
        if not text:
            return

        # 添加到历史 / Add to history
        self._add_to_history(text)

        # 发射信号 / Emit signal
        self.message_submitted.emit(text)

        # 清空输入框 / Clear input
        self.clear()

    def keyPressEvent(self, event: QKeyEvent) -> None:
        """
        键盘事件处理
        Keyboard event handler

        - Enter: 提交 / Submit
        - Up/Down: 浏览历史 / Navigate history
        - Escape: 隐藏面板 / Hide panel
        """
        key = event.key()

        # Up 键 - 浏览更早的历史 / Up key - earlier history
        if key == Qt.Key.Key_Up:
            self._navigate_history(-1)
            event.accept()
            return

        # Down 键 - 浏览更近的历史 / Down key - more recent history
        if key == Qt.Key.Key_Down:
            self._navigate_history(1)
            event.accept()
            return

        # Escape 键 - 隐藏面板 / Escape key - hide panel
        if key == Qt.Key.Key_Escape:
            self.hide_panel()
            event.accept()
            return

        super().keyPressEvent(event)

    def _navigate_history(self, direction: int) -> None:
        """
        浏览历史记录
        Navigate history

        Args:
            direction: -1 向上 (更早)，1 向下 (更近)
                       -1 = earlier, 1 = more recent
        """
        if not self._history:
            return

        # 首次进入历史浏览，保存当前输入
        # On first history access, save current input
        if self._history_index == -1 and direction == -1:
            self._temp_input = self.get_text()

        # 计算新索引 / Calculate new index
        new_index = self._history_index + direction

        # Up 方向: 从 -1 到 len-1，Down 方向: 从 len-1 到 -1
        # Up: from -1 to len-1, Down: from len-1 to -1
        if direction == -1:
            # 向上，索引从 -1 变为 0，然后增加到 len-1
            # Going up, index goes from -1 to 0, then up to len-1
            if new_index < 0:
                new_index = 0
            elif new_index >= len(self._history):
                return  # 已经是最早的记录 / Already at oldest
        else:
            # 向下，索引减少，回到 -1 时恢复临时输入
            # Going down, index decreases, restore temp at -1
            if new_index < -1:
                return
            elif new_index >= len(self._history):
                new_index = -1

        self._history_index = new_index

        # 设置文本 / Set text
        if self._history_index == -1:
            # 恢复临时保存的输入 / Restore saved input
            self.set_text(self._temp_input)
        else:
            # 显示历史记录 (倒序，索引 0 是最近的)
            # Show history (reversed, index 0 is most recent)
            history_text = self._history[-(self._history_index + 1)]
            self.set_text(history_text)

        # 移动光标到末尾 / Move cursor to end
        if self._input_field:
            self._input_field.setCursorPosition(len(self.get_text()))

    def _add_to_history(self, text: str) -> None:
        """
        添加到历史记录
        Add to history

        Args:
            text: 输入的文本 / Input text
        """
        # 避免重复添加相同的最近记录 / Avoid duplicate recent entries
        if self._history and self._history[-1] == text:
            return

        self._history.append(text)

        # 限制历史记录数量 / Limit history size
        if len(self._history) > self._max_history:
            self._history = self._history[-self._max_history :]

        # 重置索引 / Reset index
        self._history_index = -1
        self._temp_input = ""

    def get_history(self) -> List[str]:
        """
        获取历史记录
        Get history

        Returns:
            历史记录列表 (最旧到最新) / History list (oldest to newest)
        """
        return self._history.copy()

    def clear_history(self) -> None:
        """
        清空历史记录
        Clear history
        """
        self._history.clear()
        self._history_index = -1
        self._temp_input = ""

    def show_panel(self, anchor: Optional["QPoint"] = None) -> None:
        """
        显示输入面板
        Show input panel

        Args:
            anchor: 锚点位置 (可选) / Anchor point (optional)
        """
        if anchor:
            # 在锚点下方显示 / Show below anchor
            x = anchor.x() - self.width() // 2
            y = anchor.y() + 10
            self.move(x, y)

        self.show()
        self.raise_()
        self.focus()
        self.panel_shown.emit()

    def hide_panel(self) -> None:
        """
        隐藏输入面板
        Hide input panel
        """
        self.hide()
        self.panel_hidden.emit()

    def toggle_panel(self) -> None:
        """
        切换面板显示状态
        Toggle panel visibility
        """
        if self.isVisible():
            self.hide_panel()
        else:
            self.show_panel()
