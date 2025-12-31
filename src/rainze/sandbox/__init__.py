"""
沙盒执行环境
Sandbox Execution Environment

提供安全的 Python 脚本执行环境，限制危险操作。
Provides safe Python script execution with restricted operations.

安全约束 / Security constraints:
- 禁止文件访问 / No file access
- 禁止网络访问 / No network access
- 禁止系统调用 / No system calls
- 禁止代码执行 / No code execution (exec/eval)
- 超时限制 / Timeout limit
- 调用深度限制 / Call depth limit

Reference:
    MOD-Animation-Script.md §4: 沙盒安全设计
"""

from rainze.sandbox.executor import SandboxExecutor
from rainze.sandbox.exceptions import (
    ScriptError,
    ScriptSyntaxError,
    ScriptSecurityError,
    ScriptTimeoutError,
    ScriptRuntimeError,
)

__all__ = [
    "SandboxExecutor",
    "ScriptError",
    "ScriptSyntaxError",
    "ScriptSecurityError",
    "ScriptTimeoutError",
    "ScriptRuntimeError",
]
