# Changelog

All notable changes to the State module will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [Unreleased]

### Added
- Initial State module implementation
- `MoodState` and `MoodSubState` enums for emotion states
- `EmotionStateMachine` with hybrid-driven architecture (rule + LLM layers)
- `AttributeManager` abstract base class for numerical attributes
- `EnergyManager` for energy management (0-100 range)
- `AffinityManager` for affinity/relationship management (0-999, 5 levels)
- `StateManager` as unified state coordinator
- State change event models (`StateChangedEvent`, `MoodTransitionEvent`, etc.)
- State snapshot and restore functionality
- Prompt and behavior modifiers based on current state

### Technical Details
- Uses `EmotionTag` from `rainze.core.contracts` (cross-module contract)
- Follows PRD §0.6a state priority matrix
- Rule layer takes priority over LLM layer for state transitions
- State switch protection (60s cooldown for same state)
- Emotion inertia for smooth transitions

## [0.1.0] - 2025-12-30

### Added
- Initial module structure based on MOD-State.md design
- Core emotion state machine implementation
- Energy and affinity attribute managers
- State event notification system
