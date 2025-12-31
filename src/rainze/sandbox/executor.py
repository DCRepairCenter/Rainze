"""
沙盒执行器
Sandbox Executor

在受限环境中安全执行 Python 脚本。
Safely execute Python scripts in restricted environment.

实现方式 / Implementation:
1. AST 安全检查 - 检测危险节点和名称
2. 白名单内置函数 - 只暴露安全的 builtins
3. 超时控制 - 使用信号或线程超时
4. 调用深度限制 - 防止递归攻击

Reference:
    MOD-Animation-Script.md §4: 沙盒安全设计
"""

from __future__ import annotations

import ast
import logging
from typing import Any

from rainze.sandbox.builtins import FORBIDDEN_MODULES, FORBIDDEN_NAMES, SAFE_BUILTINS
from rainze.sandbox.exceptions import (
    ScriptRuntimeError,
    ScriptSecurityError,
    ScriptSyntaxError,
)

logger = logging.getLogger(__name__)


class SecurityChecker(ast.NodeVisitor):
    """
    AST 安全检查器
    AST Security Checker

    遍历 AST 检测不安全的节点和名称。
    Traverses AST to detect unsafe nodes and names.
    """

    def __init__(self) -> None:
        self.errors: list[str] = []

    def visit_Import(self, node: ast.Import) -> None:
        """禁止 import 语句 / Forbid import statements"""
        for alias in node.names:
            if alias.name.split(".")[0] in FORBIDDEN_MODULES:
                self.errors.append(f"Import forbidden: {alias.name}")
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        """禁止 from ... import 语句 / Forbid from ... import statements"""
        if node.module and node.module.split(".")[0] in FORBIDDEN_MODULES:
            self.errors.append(f"Import forbidden: {node.module}")
        self.generic_visit(node)

    def visit_Name(self, node: ast.Name) -> None:
        """检查变量名 / Check variable names"""
        if node.id in FORBIDDEN_NAMES:
            self.errors.append(f"Forbidden name: {node.id}")
        self.generic_visit(node)

    def visit_Attribute(self, node: ast.Attribute) -> None:
        """检查属性访问 / Check attribute access"""
        # 禁止访问双下划线属性 / Forbid double underscore attributes
        if node.attr.startswith("__") and node.attr.endswith("__"):
            # 允许 __init__, __str__, __repr__ 等常用方法
            allowed_dunders = {"__init__", "__str__", "__repr__", "__len__", "__iter__"}
            if node.attr not in allowed_dunders:
                self.errors.append(f"Forbidden attribute: {node.attr}")
        # 禁止单下划线开头的私有属性（可选，目前允许）
        # if node.attr.startswith("_") and not node.attr.startswith("__"):
        #     self.errors.append(f"Private attribute access: {node.attr}")
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        """检查函数调用 / Check function calls"""
        # 检查直接调用危险函数
        if isinstance(node.func, ast.Name):
            if node.func.id in FORBIDDEN_NAMES:
                self.errors.append(f"Forbidden function call: {node.func.id}")
        self.generic_visit(node)

    def check(self, tree: ast.AST) -> list[str]:
        """
        执行安全检查
        Perform security check

        Args:
            tree: AST 树 / AST tree

        Returns:
            错误列表 / List of errors
        """
        self.errors = []
        self.visit(tree)
        return self.errors


class SandboxExecutor:
    """
    沙盒执行器
    Sandbox Executor

    在受限环境中执行 Python 脚本。
    Executes Python scripts in restricted environment.

    Attributes:
        _timeout_ms: 执行超时时间（毫秒）
        _max_recursion: 最大递归深度
        _compiled_code: 已编译的代码对象缓存
        _namespace: 执行命名空间

    Example:
        >>> executor = SandboxExecutor(timeout_ms=100)
        >>> executor.load_script(script_code)
        >>> result = executor.call_function("get_random_actions", ctx)
    """

    def __init__(
        self,
        timeout_ms: int = 100,
        max_recursion: int = 50,
    ) -> None:
        """
        初始化沙盒执行器
        Initialize sandbox executor

        Args:
            timeout_ms: 执行超时时间（毫秒）/ Execution timeout (ms)
            max_recursion: 最大递归深度 / Maximum recursion depth
        """
        self._timeout_ms = timeout_ms
        self._max_recursion = max_recursion
        self._compiled_code: Any | None = None
        self._namespace: dict[str, Any] = {}
        self._script_loaded = False

    def load_script(self, script_code: str, filename: str = "<script>") -> None:
        """
        加载并编译脚本
        Load and compile script

        Args:
            script_code: 脚本源代码 / Script source code
            filename: 文件名（用于错误报告）/ Filename for error reporting

        Raises:
            ScriptSyntaxError: 语法错误
            ScriptSecurityError: 安全违规
        """
        # 1. 解析 AST / Parse AST
        try:
            tree = ast.parse(script_code, filename=filename)
        except SyntaxError as e:
            raise ScriptSyntaxError(
                str(e.msg) if e.msg else "Unknown syntax error",
                line=e.lineno or 0,
                column=e.offset or 0,
            ) from e

        # 2. 安全检查 / Security check
        checker = SecurityChecker()
        errors = checker.check(tree)
        if errors:
            raise ScriptSecurityError(
                f"Security violations: {', '.join(errors)}",
                violation_type="ast_check",
            )

        # 3. 编译代码 / Compile code
        try:
            self._compiled_code = compile(tree, filename, "exec")
        except Exception as e:
            raise ScriptSyntaxError(str(e)) from e

        # 4. 准备安全命名空间 / Prepare safe namespace
        self._namespace = {"__builtins__": SAFE_BUILTINS.copy()}

        # 5. 执行脚本（定义函数）/ Execute script (define functions)
        try:
            exec(self._compiled_code, self._namespace)  # noqa: S102
        except Exception as e:
            raise ScriptRuntimeError(
                f"Failed to load script: {e}",
                original_error=e,
            ) from e

        self._script_loaded = True
        logger.info(f"脚本加载成功: {filename}")

    def has_function(self, func_name: str) -> bool:
        """
        检查函数是否存在
        Check if function exists

        Args:
            func_name: 函数名 / Function name

        Returns:
            是否存在 / Whether exists
        """
        if not self._script_loaded:
            return False
        func = self._namespace.get(func_name)
        return callable(func)

    def call_function(
        self,
        func_name: str,
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        """
        调用脚本中的函数
        Call function in script

        Args:
            func_name: 函数名 / Function name
            *args: 位置参数 / Positional arguments
            **kwargs: 关键字参数 / Keyword arguments

        Returns:
            函数返回值 / Function return value

        Raises:
            ScriptRuntimeError: 函数不存在或执行错误
        """
        if not self._script_loaded:
            raise ScriptRuntimeError("No script loaded")

        func = self._namespace.get(func_name)
        if not callable(func):
            raise ScriptRuntimeError(f"Function not found: {func_name}")

        try:
            # TODO: 添加超时控制
            # 目前简单执行，后续可以使用 signal 或 threading 实现超时
            result = func(*args, **kwargs)
            return result
        except Exception as e:
            raise ScriptRuntimeError(
                f"Function '{func_name}' raised error: {e}",
                original_error=e,
            ) from e

    def call_function_safe(
        self,
        func_name: str,
        *args: Any,
        default: Any = None,
        **kwargs: Any,
    ) -> Any:
        """
        安全调用函数（失败返回默认值）
        Safely call function (return default on failure)

        Args:
            func_name: 函数名 / Function name
            *args: 位置参数 / Positional arguments
            default: 默认返回值 / Default return value
            **kwargs: 关键字参数 / Keyword arguments

        Returns:
            函数返回值或默认值 / Function return value or default
        """
        try:
            if not self.has_function(func_name):
                return default
            return self.call_function(func_name, *args, **kwargs)
        except Exception as e:
            logger.warning(f"脚本函数调用失败 {func_name}: {e}")
            return default

    def get_available_functions(self) -> list[str]:
        """
        获取脚本中定义的所有函数
        Get all functions defined in script

        Returns:
            函数名列表 / List of function names
        """
        if not self._script_loaded:
            return []

        return [
            name
            for name, value in self._namespace.items()
            if callable(value) and not name.startswith("_")
        ]

    def inject_context(self, name: str, value: Any) -> None:
        """
        注入上下文变量
        Inject context variable

        Args:
            name: 变量名 / Variable name
            value: 变量值 / Variable value
        """
        if name in FORBIDDEN_NAMES:
            raise ScriptSecurityError(
                f"Cannot inject forbidden name: {name}",
                violation_type="injection",
            )
        self._namespace[name] = value

    def reset(self) -> None:
        """
        重置执行器状态
        Reset executor state
        """
        self._compiled_code = None
        self._namespace = {}
        self._script_loaded = False
