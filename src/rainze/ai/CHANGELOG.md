# Changelog

All notable changes to the AI module will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [Unreleased]

### Added

- Initial AI module structure with LLM client and three-tier response generation

## [0.1.0] - 2025-12-30

### Added

- **Exceptions** (`exceptions.py`)
  - `AIError`: Base exception for AI module
  - `LLMTimeoutError`: LLM call timeout
  - `LLMRateLimitError`: Rate limit exceeded
  - `LLMAPIError`: API error with status code
  - `PromptBuildError`: Prompt building failure
  - `EmbeddingError`: Embedding failure
  - `AllFallbacksFailedError`: All fallback strategies failed
  - `GenerationError`: Response generation failure

- **Configuration Schemas** (`schemas.py`)
  - `AIConfig`: Master configuration model
  - `APIConfig`: Primary API configuration
  - `FallbackAPIConfig`: Fallback API configuration
  - `RateLimitsConfig`: Rate limiting configuration
  - `GenerationConfig`: Generation parameters
  - `EmbeddingConfig`: Embedding service configuration
  - `ResponseCacheConfig`: Response cache configuration
  - `PromptConfig`: Prompt building configuration

- **LLM Client** (`llm/`)
  - `LLMRequest`: Request data structure
  - `LLMResponse`: Response data structure
  - `LLMProvider`: Provider enumeration (ANTHROPIC, OPENAI)
  - `LLMClient`: Abstract base class for LLM clients
  - `LLMClientFactory`: Factory for creating LLM clients
  - `AnthropicClient`: Anthropic Claude API implementation using httpx

- **Response Generation** (`generation/`)
  - `GeneratedResponse`: Response data structure with emotion tag
  - `ResponseGenerator`: Coordinator for all three tiers
  - `Tier1TemplateGenerator`: Template-based responses (<50ms)
  - `Tier2RuleGenerator`: Rule-based responses (<100ms)
  - `Tier3LLMGenerator`: LLM-based responses (500-2000ms)

### Technical Notes

- All shared types imported from `rainze.core.contracts` (EmotionTag, ResponseTier)
- Uses `httpx` for async HTTP requests
- Uses Pydantic for configuration validation
- Full type hints and bilingual docstrings (中英双语)
- Follows PRD §0.3 hybrid response strategy
