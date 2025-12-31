"""
安全内置函数白名单
Safe Builtins Whitelist

定义脚本可以访问的安全内置函数。
Defines safe builtin functions accessible to scripts.

Reference:
    MOD-Animation-Script.md §4.2: 白名单内置函数
"""

from __future__ import annotations

from typing import Any

# 安全的内置函数白名单 / Safe builtin function whitelist
SAFE_BUILTINS: dict[str, Any] = {
    # 类型 / Types
    "int": int,
    "float": float,
    "str": str,
    "bool": bool,
    "list": list,
    "dict": dict,
    "tuple": tuple,
    "set": set,
    # 数学 / Math
    "abs": abs,
    "min": min,
    "max": max,
    "sum": sum,
    "round": round,
    "pow": pow,
    "divmod": divmod,
    # 序列操作 / Sequence operations
    "len": len,
    "range": range,
    "enumerate": enumerate,
    "zip": zip,
    "sorted": sorted,
    "reversed": reversed,
    "filter": filter,
    "map": map,
    # 条件 / Conditions
    "all": all,
    "any": any,
    "isinstance": isinstance,
    "issubclass": issubclass,
    # 字符串 / String
    "chr": chr,
    "ord": ord,
    "repr": repr,
    # 特殊常量 / Special constants
    "True": True,
    "False": False,
    "None": None,
    # 异常（只读）/ Exceptions (read-only)
    "Exception": Exception,
    "ValueError": ValueError,
    "TypeError": TypeError,
    "KeyError": KeyError,
    "IndexError": IndexError,
    "AttributeError": AttributeError,
}

# 禁止的名称（即使在白名单中也不允许）
# Forbidden names (not allowed even if in whitelist)
FORBIDDEN_NAMES: set[str] = {
    # 代码执行 / Code execution
    "__import__",
    "exec",
    "eval",
    "compile",
    "globals",
    "locals",
    "vars",
    # 文件访问 / File access
    "open",
    "file",
    "input",
    # 危险属性 / Dangerous attributes
    "__builtins__",
    "__class__",
    "__bases__",
    "__subclasses__",
    "__mro__",
    "__dict__",
    "__code__",
    "__globals__",
    "__closure__",
    "__func__",
    "__self__",
    "__module__",
    "__name__",
    "__qualname__",
    "__annotations__",
    # 系统 / System
    "exit",
    "quit",
    "help",
    "license",
    "copyright",
    "credits",
}

# 禁止的模块 / Forbidden modules
FORBIDDEN_MODULES: set[str] = {
    "os",
    "sys",
    "subprocess",
    "socket",
    "urllib",
    "requests",
    "http",
    "ftplib",
    "telnetlib",
    "smtplib",
    "poplib",
    "imaplib",
    "nntplib",
    "pathlib",
    "shutil",
    "tempfile",
    "glob",
    "fnmatch",
    "pickle",
    "shelve",
    "marshal",
    "dbm",
    "sqlite3",
    "ctypes",
    "multiprocessing",
    "threading",
    "concurrent",
    "asyncio",
    "signal",
    "importlib",
    "builtins",
    "__builtin__",
}
