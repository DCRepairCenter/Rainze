# Changelog

All notable changes to the Animation module will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [Unreleased]

### Added
- Planned: Concrete layer implementations (Base, Idle, Expression, Action, Effect, LipSync)
- Planned: ResourceLoader for animation asset loading
- Planned: ExpressionManager for emotion-to-expression mapping
- Planned: LipSyncManager for audio/text-based mouth animation
- Planned: AnimationStateMachine for state transitions

## [0.1.0] - 2025-12-30

### Added
- Initial module structure following MOD-Animation.md design
- `AnimationState` enum defining animation states (IDLE, TALKING, REACTING, etc.)
- `AnimationFrame` dataclass for frame data with pixmap and duration
- `BlendMode` enum for layer compositing modes
- `AnimationLayer` abstract base class with:
  - `get_current_frame()` abstract method
  - `update(delta_ms)` abstract method
  - `reset()` abstract method
  - Visibility, opacity, and blend mode properties
- `FrameSequence` class for managing animation frame sequences:
  - Time-based frame lookup
  - Loop support
  - Factory method from QPixmap list
- `FramePlayer` class for frame playback control:
  - Play/pause/stop/seek controls
  - Playback speed adjustment
  - Qt signals for frame_changed, playback_finished, loop_completed
- `AnimationController` main controller with:
  - 6-layer management system
  - Expression control via `set_expression()`
  - Action control via `play_action()`
  - Effect control via `play_effect()`
  - Lip sync stubs for future implementation
  - EmotionTag parsing from response text
  - Qt signals for frame_ready, state_changed, action_completed
  - Render loop with configurable FPS
- Module `__init__.py` with all public exports
- README.md documentation
- TODO.md task tracking
- CHANGELOG.md (this file)

### Technical Notes
- Uses `EmotionTag` from `rainze.core.contracts` (no duplicate definitions)
- PySide6 for Qt functionality (QPixmap, QTimer, Signal)
- Full type hints on all public APIs
- Bilingual docstrings (Chinese/English)
- Windows-compatible path handling via `pathlib.Path`
