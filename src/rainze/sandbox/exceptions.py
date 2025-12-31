"""
沙盒异常定义
Sandbox Exception Definitions

定义脚本执行过程中可能发生的各类异常。
Defines exceptions that may occur during script execution.
"""

from __future__ import annotations


class ScriptError(Exception):
    """
    脚本执行错误基类
    Base class for script execution errors
    """

    pass


class ScriptSyntaxError(ScriptError):
    """
    脚本语法错误
    Script syntax error

    在脚本编译阶段检测到的语法问题。
    Syntax issues detected during script compilation.
    """

    def __init__(self, message: str, line: int = 0, column: int = 0) -> None:
        self.line = line
        self.column = column
        super().__init__(f"Syntax error at line {line}, column {column}: {message}")


class ScriptSecurityError(ScriptError):
    """
    脚本安全违规
    Script security violation

    脚本尝试执行被禁止的操作。
    Script attempted forbidden operations.
    """

    def __init__(self, message: str, violation_type: str = "unknown") -> None:
        self.violation_type = violation_type
        super().__init__(f"Security violation ({violation_type}): {message}")


class ScriptTimeoutError(ScriptError):
    """
    脚本执行超时
    Script execution timeout

    脚本执行时间超过限制。
    Script execution exceeded time limit.
    """

    def __init__(self, timeout_ms: int) -> None:
        self.timeout_ms = timeout_ms
        super().__init__(f"Script execution timed out after {timeout_ms}ms")


class ScriptRuntimeError(ScriptError):
    """
    脚本运行时错误
    Script runtime error

    脚本执行过程中发生的错误。
    Error occurred during script execution.
    """

    def __init__(self, message: str, original_error: Exception | None = None) -> None:
        self.original_error = original_error
        super().__init__(f"Runtime error: {message}")
