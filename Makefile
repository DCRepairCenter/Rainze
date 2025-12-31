# Rainze Makefile
# AI 桌面宠物应用构建脚本 / AI Desktop Pet Build Script
#
# Usage / 使用方式:
#   make help       - 显示帮助 / Show help
#   make setup      - 初始化环境 / Initialize environment
#   make build      - 构建项目 / Build project
#   make run        - 运行应用 / Run application
#   make test       - 运行测试 / Run tests
#   make clean      - 清理构建 / Clean build artifacts
#
# Requirements / 依赖:
#   - Python 3.12+
#   - Rust 1.92+
#   - uv (Python package manager)
#   - MinGW (for Rust GNU target on Windows)

# ============================================================================
# 配置 / Configuration
# ============================================================================

SHELL := powershell.exe
.SHELLFLAGS := -NoProfile -Command

# 路径 / Paths
VENV := .venv
PYTHON := $(VENV)\Scripts\python.exe
UV := uv
MATURIN := $(VENV)\Scripts\maturin.exe
RUFF := $(VENV)\Scripts\ruff.exe
MYPY := $(VENV)\Scripts\mypy.exe
PYTEST := $(VENV)\Scripts\pytest.exe

# Rust 配置 / Rust configuration
RUST_TARGET := rainze_core
RUST_WHEEL := $(RUST_TARGET)\target\wheels\rainze_core-0.1.0-cp312-cp312-win_amd64.whl

# MinGW 路径 (根据系统调整) / MinGW path (adjust for your system)
MINGW_PATH := C:\msys64\mingw64\bin

# ============================================================================
# 默认目标 / Default target
# ============================================================================

.PHONY: help
help:
	@Write-Host "Rainze Makefile - AI Desktop Pet" -ForegroundColor Cyan
	@Write-Host "=================================" -ForegroundColor Cyan
	@Write-Host ""
	@Write-Host "Setup / 环境配置:" -ForegroundColor Yellow
	@Write-Host "  make setup      - 完整环境初始化 / Full environment setup"
	@Write-Host "  make venv       - 创建虚拟环境 / Create virtual environment"
	@Write-Host "  make deps       - 安装 Python 依赖 / Install Python dependencies"
	@Write-Host ""
	@Write-Host "Build / 构建:" -ForegroundColor Yellow
	@Write-Host "  make build      - 构建所有组件 / Build all components"
	@Write-Host "  make build-rust - 构建 Rust 模块 / Build Rust module"
	@Write-Host "  make build-dev  - 开发模式构建 / Development build"
	@Write-Host ""
	@Write-Host "Run / 运行:" -ForegroundColor Yellow
	@Write-Host "  make run        - 运行应用 / Run application"
	@Write-Host "  make verify     - 验证环境 / Verify environment"
	@Write-Host ""
	@Write-Host "Quality / 质量:" -ForegroundColor Yellow
	@Write-Host "  make test       - 运行测试 / Run tests"
	@Write-Host "  make lint       - 代码检查 / Lint code"
	@Write-Host "  make format     - 格式化代码 / Format code"
	@Write-Host "  make typecheck  - 类型检查 / Type check"
	@Write-Host "  make check      - 运行所有检查 / Run all checks"
	@Write-Host ""
	@Write-Host "Clean / 清理:" -ForegroundColor Yellow
	@Write-Host "  make clean      - 清理构建产物 / Clean build artifacts"
	@Write-Host "  make clean-all  - 完全清理 / Full clean (including venv)"
	@Write-Host ""

# ============================================================================
# 环境配置 / Environment Setup
# ============================================================================

.PHONY: setup
setup: venv deps build-rust
	@Write-Host "✅ 环境配置完成 / Setup complete!" -ForegroundColor Green

.PHONY: venv
venv:
	@Write-Host "📦 创建虚拟环境 / Creating virtual environment..." -ForegroundColor Cyan
	@$(UV) venv

.PHONY: deps
deps:
	@Write-Host "📥 安装依赖 / Installing dependencies..." -ForegroundColor Cyan
	@$(UV) sync --all-extras

# ============================================================================
# 构建 / Build
# ============================================================================

.PHONY: build
build: build-rust install-rust
	@Write-Host "✅ 构建完成 / Build complete!" -ForegroundColor Green

.PHONY: build-rust
build-rust:
	@Write-Host "🦀 构建 Rust 模块 / Building Rust module..." -ForegroundColor Cyan
	@$$env:PATH = "$(MINGW_PATH);$$env:PATH"; $$env:PYO3_PYTHON = (Resolve-Path "$(PYTHON)").Path; $$maturin = (Resolve-Path "$(MATURIN)").Path; Push-Location $(RUST_TARGET); & $$maturin build --release; Pop-Location

.PHONY: build-dev
build-dev:
	@Write-Host "🔧 开发模式构建 / Development build..." -ForegroundColor Cyan
	@$$env:PATH = "$(MINGW_PATH);$$env:PATH"; $$env:PYO3_PYTHON = (Resolve-Path "$(PYTHON)").Path; $$maturin = (Resolve-Path "$(MATURIN)").Path; Push-Location $(RUST_TARGET); & $$maturin develop; Pop-Location

.PHONY: install-rust
install-rust:
	@Write-Host "📦 安装 Rust wheel / Installing Rust wheel..." -ForegroundColor Cyan
	@$(UV) pip install $(RUST_WHEEL) --force-reinstall

# ============================================================================
# 运行 / Run
# ============================================================================

.PHONY: run
run:
	@Write-Host "🚀 启动 Rainze / Starting Rainze..." -ForegroundColor Cyan
	@& "$(PYTHON)" -m rainze.main

.PHONY: verify
verify:
	@Write-Host "🔍 验证环境 / Verifying environment..." -ForegroundColor Cyan
	@& "$(PYTHON)" -c "import rainze_core; import rainze; print('rainze:', rainze.__version__); m = rainze_core.SystemMonitor(); print('rainze_core: OK'); print(f'CPU: {m.get_cpu_usage():.1f}%%'); print(f'Memory: {m.get_memory_usage():.1f}%%')"

# ============================================================================
# 质量检查 / Quality Checks
# ============================================================================

.PHONY: test
test:
	@Write-Host "🧪 运行测试 / Running tests..." -ForegroundColor Cyan
	@& "$(PYTEST)" tests/ -v

.PHONY: lint
lint:
	@Write-Host "🔎 代码检查 / Linting..." -ForegroundColor Cyan
	@& "$(RUFF)" check src/ tests/

.PHONY: format
format:
	@Write-Host "✨ 格式化代码 / Formatting..." -ForegroundColor Cyan
	@& "$(RUFF)" format src/ tests/
	@& "$(RUFF)" check src/ tests/ --fix

.PHONY: typecheck
typecheck:
	@Write-Host "📝 类型检查 / Type checking..." -ForegroundColor Cyan
	@& "$(MYPY)" src/rainze --ignore-missing-imports

.PHONY: check
check: lint typecheck test
	@Write-Host "✅ 所有检查通过 / All checks passed!" -ForegroundColor Green

.PHONY: rust-check
rust-check:
	@Write-Host "🦀 Rust 检查 / Rust check..." -ForegroundColor Cyan
	@$$env:PATH = "$(MINGW_PATH);$$env:PATH"; $$env:PYO3_PYTHON = (Resolve-Path "$(PYTHON)").Path; Push-Location $(RUST_TARGET); cargo check; cargo clippy; Pop-Location

# ============================================================================
# 清理 / Clean
# ============================================================================

.PHONY: clean
clean:
	@Write-Host "🧹 清理构建产物 / Cleaning build artifacts..." -ForegroundColor Cyan
	@Remove-Item -Recurse -Force -ErrorAction SilentlyContinue $(RUST_TARGET)\target, dist, build, *.egg-info, .pytest_cache, .mypy_cache, .ruff_cache, __pycache__
	@Get-ChildItem -Recurse -Directory -Filter "__pycache__" | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
	@Write-Host "✅ 清理完成 / Clean complete!" -ForegroundColor Green

.PHONY: clean-all
clean-all: clean
	@Write-Host "🧹 完全清理 / Full clean..." -ForegroundColor Cyan
	@Remove-Item -Recurse -Force -ErrorAction SilentlyContinue $(VENV)
	@Write-Host "✅ 完全清理完成 / Full clean complete!" -ForegroundColor Green

# ============================================================================
# 开发辅助 / Development Helpers
# ============================================================================

.PHONY: pre-commit
pre-commit:
	@Write-Host "🪝 安装 pre-commit hooks / Installing pre-commit hooks..." -ForegroundColor Cyan
	@& "$(VENV)\Scripts\pre-commit.exe" install

.PHONY: update
update:
	@Write-Host "📦 更新依赖 / Updating dependencies..." -ForegroundColor Cyan
	@$(UV) lock --upgrade
	@$(UV) sync --all-extras

# ============================================================================
# 打包 / Packaging
# ============================================================================

.PHONY: package
package: build
	@Write-Host "📦 打包应用 / Packaging application..." -ForegroundColor Cyan
	@Write-Host "⚠️  TODO: 实现打包逻辑 / TODO: Implement packaging" -ForegroundColor Yellow
