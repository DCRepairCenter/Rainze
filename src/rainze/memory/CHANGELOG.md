# Changelog

All notable changes to the Memory module will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Planned
- Vector search (FAISS integration)
- Identity Layer (Layer 1) implementation
- Importance auto-evaluation
- Memory decay mechanism
- Conflict detection

## [0.1.0] - 2025-12-30

### Added
- Initial Memory module implementation
- **Data Models**:
  - `MemoryType` enum (FACT, EPISODE, RELATION, REFLECTION)
  - `MemoryItem` dataclass with full serialization support
  - `FactItem` for structured fact storage (subject-predicate-object)
  - `EpisodeItem` for episodic memories
  - `RankedMemory` for retrieval results
  - `RetrievalResult` with metadata
  - `MemoryIndexItem` for Prompt injection
  - `TimeWindow` for time-based filtering
- **Working Memory (Layer 2)**:
  - `WorkingMemory` class with conversation history management
  - `ConversationTurn` dataclass
  - Token estimation support
- **FTS5 Retrieval**:
  - `FTSSearcher` with SQLite FTS5 full-text search
  - Async database operations via aiosqlite
  - Automatic FTS5 triggers for index sync
- **Memory Manager**:
  - `MemoryManager` main entry class
  - `create_memory()`, `create_fact()`, `create_episode()` methods
  - `search()` with threshold gating
  - `get_memory_index()` for Prompt injection
  - `get_conversation_history()`, `add_conversation_turn()`, `clear_conversation()`
  - Statistics via `get_stats()`
- **Exceptions**:
  - `MemoryError` base exception
  - `MemoryNotFoundError`
  - `RetrievalError`
  - `VectorizeError`
  - `StorageError`
  - `MemoryQuotaExceededError`
- **Documentation**:
  - README.md with usage examples
  - TODO.md task tracking
  - This CHANGELOG.md

### Technical Details
- All functions have complete type annotations
- Google-style docstrings with bilingual comments (中英双语)
- KISS/YAGNI/DRY/SOLID principles applied
- FTS5 uses unicode61 tokenizer for Chinese support
