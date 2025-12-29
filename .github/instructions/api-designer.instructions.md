```instructions
---
applyTo: ".github/apis/**/*.md"
---

# API Design Instructions

When user asks to design, document, or review APIs:

1. **READ** [.github/agents/api-designer.agent.md](.github/agents/api-designer.agent.md) for the complete protocol
2. **OUTPUT** to `.github/apis/API-[Name].md` for design documents
3. **OUTPUT** to `.github/apis/specs/[name].openapi.yaml` for OpenAPI specs

## Key Principles

- **Language Agnostic**: Design contracts, not code
- **API-First**: Design before implementation
- **RESTful**: Follow REST best practices
- **Documented**: Every endpoint with examples

## Design Checklist

### Naming
- Resources: plural nouns (`/users`, `/orders`)
- Endpoints: lowercase, hyphen-separated
- Consistent parameter naming (camelCase or snake_case)

### HTTP Methods
- GET: Read resources (safe, idempotent)
- POST: Create resources
- PUT: Full update (idempotent)
- PATCH: Partial update
- DELETE: Remove resources (idempotent)

### Response Structure
```json
{
  "data": { },
  "meta": { "page": 1, "total": 100 },
  "errors": [ ]
}
```

### Error Handling
- Use semantic HTTP status codes (400, 401, 403, 404, 422, 500)
- Include error code, message, and details
- Add request ID for tracing

### Security
- Define authentication method (OAuth 2.0, JWT, API Key)
- Specify rate limits
- Document required permissions

## Self-Reflection

Before finalizing, always output:
> "wait，我要反思我的 API 设计决策"

Then verify:
1. Intuitive for developers?
2. Comprehensive error handling?
3. Scalable for future needs?
4. Consistent patterns throughout?

## Quick Commands

| Trigger | Action |
|---------|--------|
| "design API", "create API" | New API specification |
| "review API", "analyze API" | Review existing API |
| "document API" | Generate documentation |
| "mock API" | Create mock server spec |

## Output Locations

- Design Documents: `.github/apis/API-[Name].md`
- OpenAPI Specs: `.github/apis/specs/[name].openapi.yaml`
- Mock Configs: `.github/apis/mocks/[name].mock.json`

```
