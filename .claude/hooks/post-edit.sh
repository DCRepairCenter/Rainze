#!/bin/bash
# Post-edit hook: Run linting on Python files
# 编辑后钩子：对 Python 文件运行 lint 检查

# Read the tool input from stdin
INPUT=$(cat)

# Extract file path from JSON input
FILE_PATH=$(echo "$INPUT" | grep -o '"file_path"[[:space:]]*:[[:space:]]*"[^"]*"' | sed 's/.*"file_path"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/')

# Only process Python files
if [[ "$FILE_PATH" == *.py ]]; then
    # Check if ruff is available
    if command -v ruff &> /dev/null; then
        # Run ruff check on the specific file (non-blocking)
        ruff check "$FILE_PATH" --select=E,W,F --quiet 2>/dev/null || true
    fi
fi

exit 0
