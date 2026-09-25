# Project Rules, Standards, and Guidelines

## 1. Approved Technologies

| Category | Approved | Notes |
| --- | --- | --- |
| Language | Python 3.11+ | Type hints are required on all new functions. |
| Web framework | FastAPI | Async-first; use `async def` for I/O-bound routes. |
| Video/CV | OpenCV | Use for capture, encoding, and frame manipulation. |
| Detection models | Ultralytics YOLO26 | YOLOv11 is acceptable only if compatibility issues arise. Do not use YOLOv8 or older for new training. |
| ORM | SQLAlchemy 2.0+ | Use declarative models, not raw SQL except for complex analytics queries. |
| Database | SQLite for development; PostgreSQL for production | Never include production credentials in `.env.example` or comments. |
| Bot integration | `python-telegram-bot` | Use the async API. |
| Configuration | `python-dotenv` and centralized `config.py` | Modules must not read `os.environ` directly. |
| Testing | pytest | Every new feature requires at least one test before merging. |
| Containerization | Docker | Use multi-stage builds to reduce image size. |

### Approved Patterns

- Use dataclasses for data-transfer objects such as `Detection` and `SecurityEvent`.
- Use the listener/observer pattern for independent database and Telegram event handling.
- Use constructor dependency injection for detectors and managers; avoid global mutable singletons except the intentionally shared `WebcamManager`.
- Use factory-style manager classes such as `DetectorManager` and `EventManager` to orchestrate components behind one interface.

## 2. What to Avoid

| Avoid | Reason |
| --- | --- |
| YOLOv8 for new model training | Superseded by YOLO26. Existing YOLOv8 checkpoints may be reused only when no YOLO26 equivalent exists. |
| Synchronous blocking calls inside async FastAPI routes | They block the event loop; use async APIs or a thread pool. |
| Global mutable state | It makes testing unreliable and creates race conditions for multi-camera scenarios. |
| Secrets in code or committed files | Telegram tokens and database passwords must come from `.env`, never source control. |
| `localStorage` or `sessionStorage` in browser dashboard components | These are not reliably supported across all project deployment and embedding contexts. |
| Raw SQL string concatenation | Use SQLAlchemy parameterized queries to prevent injection. |
| Detection on every frame | Respect centralized `FRAME_SKIP` configuration to control compute cost. |
| Tight coupling between detectors and events/notifications | Detectors must only return `Detection` objects. |
| Committing model weights | Keep `.pt` files out of Git and document how to obtain or train them. |

## 3. Dependencies

| Library | Purpose | Version guidance |
| --- | --- | --- |
| `fastapi` | Web framework | `>=0.115.0` |
| `uvicorn[standard]` | ASGI server | `>=0.30.0` |
| `opencv-python` | Video and image processing | `>=4.10.0` |
| `ultralytics` | YOLO detection models | Latest release supporting YOLO26; verify at implementation time |
| `torch` / `torchvision` | Deep-learning backend | Match the CUDA version for GPU deployments; CPU builds are acceptable for development |
| `sqlalchemy` | ORM | `>=2.0.0`; use 2.0 syntax |
| `python-telegram-bot` | Telegram integration | `>=21.0`; use the async API |
| `python-dotenv` | Environment configuration | `>=1.0.0` |
| `pytest` | Testing | `>=8.0.0` |
| `python-multipart` | FastAPI file uploads | Required for the upload endpoint |

### Dependency Policy

- Pin exact versions in `requirements.txt` for reproducible deployments; use minimum versions here only as guidance.
- Justify every new dependency in the pull request description.
- Do not add libraries speculatively.
- Avoid dependencies with restrictive licenses for commercially distributed components. Verify Ultralytics licensing before commercial deployment.

## 4. Error Handling

### Principles

- Never let one failure crash the whole pipeline.
- A Telegram failure must not stop database writes.
- A detector failure must not stop the video stream.
- Log internal errors with full stack traces, but show generic and actionable messages to users.

### Layer Rules

| Layer | Handling approach |
| --- | --- |
| Detectors | Wrap inference in `try/except`; log failures and return an empty detection list so the frame loop continues. |
| Event listeners | Wrap each listener independently; one listener must not block others. |
| Video ingestion | Raise a clear `RuntimeError` with source information when a webcam or file cannot be opened; convert it to HTTP 503/400 at the API layer. |
| Telegram alerts | Retry once on transient network failure, then log and continue without blocking detection. |
| Database writes | Roll back on failure, log the failed event data, and avoid silent loss. |
| API routes | Use appropriate `HTTPException` status codes; never expose stack traces or internal paths. |

Dashboard errors must be actionable, such as “Could not connect to webcam — check camera connection.” Failed uploads must identify the actual issue, such as unsupported type, size limit, or corruption.

### Logging

Use Python's `logging` module rather than bare `print()` once the project moves beyond early prototyping.

- `DEBUG`: frame-level details.
- `INFO`: confirmed events.
- `WARNING`: degraded operation, such as an unreachable Telegram service.
- `ERROR`: failures requiring attention.

## 5. AI Boundaries

### What AI Can Do

- Detect and classify fire/smoke, weapons, violence, and accidents.
- Provide a confidence score for each detection.
- Track vehicle movement across frames for accident heuristics.
- Draw bounding boxes and annotations from model output.

### Hard Limits

- AI cannot make final human-safety decisions or autonomously trigger physical responses without an explicitly approved safety-critical design and fail-safes.
- AI is not 100% accurate. False positives and false negatives are possible and must be disclosed.
- The system cannot perform biometric identification, facial recognition, or individual identification.
- The system must not be used for general employee monitoring or productivity tracking without separate legal and ethical review.
- The system must not silently degrade. Missing or placeholder model weights must clearly mark that detector as inactive.

### Production Guardrails

- Require human review for automated escalation beyond Telegram alerts.
- Disclose camera surveillance as required by applicable law.
- Document false-positive and false-negative rates before claiming operational readiness.
- Never claim guaranteed threat prevention in user-facing material.

## 6. Code Style and Formatting

- Follow PEP 8.
- Use Black with a line length of 100.
- Add type hints to all function signatures.
- Add Google-style docstrings to all public classes and functions.

### Naming

- Files and modules: `snake_case.py`.
- Classes: `PascalCase`.
- Functions and variables: `snake_case`.
- Constants: `UPPER_SNAKE_CASE`.
- Database tables: plural `snake_case`, such as `events` and `users`.
- API routes: kebab-case or lowercase, such as `/video-feed` and `/uploads`.

### Commit Messages

Use Conventional Commits:

```text
<type>(<scope>): <short description>

[optional body]
```

Allowed types include `feat`, `fix`, `docs`, `refactor`, `test`, `chore`, and `perf`.

Examples:

```text
feat(detection): add weapon detector with YOLO26
fix(telegram): retry on transient network failure
docs(architecture): update folder structure diagram
```

## 7. Security and Data Privacy

- Never commit `.env` files or secrets.
- Screenshots and event data may contain identifiable people; define a retention policy before production use.
- Treat Telegram bot tokens as credentials and rotate them immediately if exposed.
- Use least-privilege database credentials; the application user must not be a database administrator.
- Comply with applicable surveillance and data-protection laws, including GDPR and local CCTV regulations.

## 8. Performance and Scalability

- Respect `FRAME_SKIP`; do not process every frame for AI inference.
- Run inference without blocking the video-streaming response, using background tasks or worker threads.
- Index database columns used for dashboard filtering, especially `event_type` and `timestamp`.
- Design multiple camera sources so they do not share blocking state beyond explicitly shared components such as `WebcamManager`.
- Monitor and log inference time per frame and flag operation that exceeds the real-time budget.

## 9. Documentation and Comments

- Every module must have a top-of-file docstring describing its purpose.
- Comments should explain why, not what; code should express the what clearly.
- Update `Architecture.md` and `phases.md` whenever structure changes. Documentation drift is treated as a bug.

## 10. Testing Rules

- Add unit tests for detector logic, event debouncing, and API responses.
- Add integration tests for the ingestion → detection → event → listener pipeline using synthetic video.
- No feature is complete without at least one passing test demonstrating its core behavior.
- Mock Telegram and camera hardware so tests run in CI without real network access or hardware.

## 11. Project-Specific Rules

- Placeholder or stub detectors must log their placeholder status at startup and never fail silently.
- All confidence thresholds must be configurable through `.env`, never hardcoded in detection logic.
- Every new threat type must implement `BaseDetector` and register with `DetectorManager`; no exceptions may bypass the common interface.
