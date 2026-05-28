# Multimodal RAG OCR Constitution

<!--
Sync Impact Report:
- Version: NEW (initial constitution)
- Added: All 5 principles, Security Requirements, Development Workflow, Governance
- Templates requiring updates: ⚠ pending (.specify/templates/plan-template.md, .specify/templates/spec-template.md, .specify/templates/tasks-template.md)
- Follow-up TODOs: None
-->

## Core Principles

### I. Test-First (NON-NEGOTIABLE)

All code changes MUST be accompanied by tests before implementation. The workflow is:
1. Write tests that describe the expected behavior
2. Verify tests fail (red)
3. Implement the minimum code to make tests pass (green)
4. Refactor with tests as safety net

Pure functions (like the Header-Recursive chunker in `header_recursive.py`) get unit tests.
Service endpoints get integration tests with mocked external dependencies (Embedding API, LLM API).
Critical error paths (API failures, timeout, malformed responses) MUST have explicit test coverage.

**Rationale**: The system interacts with multiple external services (DashScope, Milvus, Redis). Without tests, failures in any dependency can silently corrupt data or produce incorrect results.

### II. No Silent Failures

Every error MUST be handled explicitly. Catch-all exception handlers (`except Exception`, bare `except`) are prohibited unless followed by explicit re-raise or user-visible error response.

For each external service call, the following failure modes MUST be addressed:
- Network timeout / connection refused
- HTTP error responses (4xx, 5xx)
- Malformed or unexpected response bodies
- Empty or nil inputs

**Rationale**: The system has 4 external dependencies. Silent failures lead to data corruption (e.g., random vectors inserted on Embedding API failure) or degraded user experience (white screens on fetch errors).

### III. Explicit Over Clever

Prefer obvious, readable code over abstractions. When a fix requires 10 obvious lines, write 10 lines — don't build a 200-line abstraction layer.

- Duplicate code is acceptable when the duplication is in different services with different error handling needs
- Extract shared logic ONLY when it appears in 3+ places AND the abstraction is clear
- File size is not a sin; unclear responsibilities in a file is

**Rationale**: This is a microservice architecture with 4 independent services. Over-abstraction across service boundaries creates coupling that defeats the purpose of microservices.

### IV. Security-First Defaults

- API keys MUST NEVER appear in Git history, frontend state, or API responses
- CORS MUST be configured to match actual deployment domains — `allow_origins=["*"]` with `allow_credentials=True` is prohibited
- External service credentials MUST be injected via environment variables, never hardcoded
- Error responses MUST NOT leak stack traces or internal paths to clients

**Rationale**: The system handles LLM API keys, embedding keys, and potentially sensitive document content. A single leaked key compromises the entire deployment.

### V. Graceful Degradation

When external services fail, the system MUST degrade gracefully rather than crash:
- Redis unavailable → disable caching, serve directly
- Reranker API fails → fall back to original vector ranking
- Embedding API fails after retries → return explicit error, do NOT insert random data
- Milvus unavailable → return 503 with clear message

Every degradation path MUST be logged at WARNING level or higher.

**Rationale**: The system depends on 4 external services. Any single point of failure turning into a full system crash is unacceptable for production use.

## Security Requirements

- **API Key Management**: All API keys stored in `backend/.env`, never in code. The file MUST be in `.gitignore` and never tracked.
- **Frontend Secrets**: The frontend MUST NOT hold, transmit, or request LLM API keys. All keys are server-side only.
- **Git Hygiene**: Before any commit, verify no secrets appear in the diff. Use `git log -p` to scan history for leaked credentials.
- **Milvus Security**: Docker-compose MUST NOT use default credentials (`minioadmin/minioadmin`). Production passwords injected via environment variables.
- **Milvus Restart Policy**: Milvus docker-compose MUST NOT use `restart: always`. etcd WAL logs will fill disk. Manual start/stop only.

## Development Workflow

- **Branch Strategy**: Feature branches for all changes. Direct commits to `main` only for documentation.
- **Code Review**: All PRs MUST verify against the PRD (`docs/superpowers/specs/`) for scope alignment before merge.
- **Testing Gate**: M-level (Must-have) fixes from the PRD MUST have passing tests before merge. S/C-level fixes may merge with documented test TODOs.
- **Commit Messages**: Descriptive, explaining WHY not WHAT. Reference PRD section or defect number when applicable.
- **Cleanup**: Remove `.backup` files, temporary test HTML files, and `__pycache__` directories before committing.

## Governance

This constitution supersedes all other development practices. Amendments require:
1. Document the change in this file with version increment
2. Update dependent templates (plan, spec, tasks) if principles change
3. Commit with descriptive message referencing the amendment reason

**Versioning Policy**: Semantic versioning (MAJOR.MINOR.PATCH).
- MAJOR: Principle removal or redefinition
- MINOR: New principle or section added
- PATCH: Clarifications, wording fixes

**Compliance Review**: Each PR must verify constitution alignment during code review. New code paths need explicit error handling per Principle II and V.

**Runtime Guidance**: See `CLAUDE.md` for project-specific development guidance and skill routing rules.

**Version**: 1.0.0 | **Ratified**: 2026-04-30 | **Last Amended**: 2026-05-28
