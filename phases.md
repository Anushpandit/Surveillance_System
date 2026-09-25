# Project Build Phases

This project follows a threat-detection-first build order rather than the usual CRUD-first sequence. The detection pipeline is the product's core value, so ingestion, detection, and event handling are established before authentication and dashboard features are layered on top.

Phases 1–4 are complete. The remaining phases build persistence, alerting, access control, user-facing workflows, testing, and deployment around that foundation.

## Phase 1 — Project Foundation and Configuration

**Status: Complete**

- Establish the project folder structure.
- Create the FastAPI backend skeleton.
- Add health-check and configuration-verification endpoints.
- Centralize configuration in `backend/config.py`, reading from `.env`.
- Establish dependency management in `requirements.txt`.

## Phase 2 — Video Ingestion

**Status: Complete**

- Capture live webcam video through OpenCV.
- Stream webcam frames as MJPEG.
- Validate uploaded video type and size limits.
- Stream uploaded videos at a throttled playback rate.
- Establish frame-skip logic for downstream AI processing.
- Use a shared `WebcamManager` handle to support multiple dashboard viewers.

## Phase 3 — Detection Pipeline

**Status: Complete**

- Define the shared `BaseDetector` interface and `Detection` data structure.
- Add the fire and smoke detector using YOLO; keep it as a placeholder until custom weights are trained.
- Add the weapon detector using YOLO; keep it as a placeholder until custom weights are trained.
- Add the violence detector using temporal or clip-based inference; keep it as a placeholder until an action-recognition model is trained.
- Add the accident detector using vehicle tracking and collision heuristics. It works out of the box with stock YOLO vehicle classes.
- Add `DetectorManager` to orchestrate all four detectors through one call.

## Phase 4 — Event Pipeline

**Status: Complete**

- Define the `SecurityEvent` data structure.
- Capture screenshots for confirmed detections.
- Add a debouncer to prevent alert spam per source and event type.
- Make cooldown duration configurable.
- Add `EventManager` with a pluggable listener pattern.
- Keep database and Telegram listeners independent so either can fail without breaking the detection pipeline.

## Phase 5 — Database and Persistence

**Status: Complete**

- Define SQLAlchemy models for `Event` with:
  - `event_type`
  - `confidence`
  - `timestamp`
  - `screenshot_path`
  - `source`
  - `reviewed`
- Set up the database session and engine.
- Support SQLite for development and PostgreSQL for production.
- Implement CRUD operations:
  - Create an event.
  - Query by date range, event type, and confidence.
  - Retrieve an event by ID.
  - Mark an event as reviewed.
- Register a database-write listener on `EventManager`.
- Define an Alembic migration strategy for schema evolution.

Implemented in `backend/database/` with SQLite/PostgreSQL-compatible session setup, event CRUD, analytics, FastAPI routes, and an `EventManager` persistence listener. The initial schema is created with `create_all`; Alembic remains required before production schema evolution.

## Phase 6 — Telegram Alerts

**Status: Planned**

- Create a Telegram bot through BotFather.
- Configure the bot token and recipient chat IDs through environment configuration.
- Implement `send_alert(image, event_type, confidence, timestamp)` using the Telegram Bot API `sendPhoto` operation.
- Retry once on transient network failure.
- Register the Telegram listener on `EventManager`.
- Test alert delivery in isolation before connecting it to the live pipeline.

Phase 6 is independent of Phase 5 and may be developed in parallel with database persistence.

## Phase 7 — Authentication and Authorization

**Status: Planned**

This phase is adapted from the standard login and authentication phase. It is intentionally placed after the detection pipeline because authentication protects the dashboard and stored data rather than enabling initial detector development.

- Add registration for authorized dashboard users, including administrators and security personnel.
- Add login and logout using session-based or token-based authentication.
- Add a password-reset flow.
- Add role-based authorization:
  - Administrators can configure thresholds and delete events.
  - Viewers can view live feeds and event history.
- Add Telegram recipient management for authenticated users.

Phase 7 must be complete before Phase 8 is deployed to real users. An unauthenticated dashboard exposing live camera feeds creates a privacy and security risk.

## Phase 8 — Dashboard

**Status: Planned**

This phase is adapted from the standard dashboard phase.

- Add a live monitoring view embedding the webcam or uploaded-video MJPEG stream.
- Add statistic cards for:
  - Total events today.
  - Breakdown by threat type.
  - System uptime.
- Add navigation for Live View, History, Analytics, and Settings.
- Add basic visualizations:
  - Detections per day.
  - Event-type breakdown.

## Phase 9 — History, Search, and Event Management

**Status: Planned**

This phase is adapted from the standard CRUD phase. The primary entity is a security event rather than a typical user-created record.

- Add a paginated event list.
- Add an event detail view with the full screenshot, metadata, and timestamp.
- Search and filter by date range, event type, confidence range, and source.
- Mark events as reviewed or false positives.
- Delete or archive old events according to the data-retention policy in `Rules.md`.
- Expose alert cooldown configuration in the Settings UI.
- Support multiple simultaneous camera sources.
- Add notification preferences for selecting which event types trigger Telegram alerts.
- Support CSV or PDF export of incidents over a selected date range.

Phase 5 must be complete before Phase 9 because history and search require persisted events.

## Phase 10 — Testing and Quality Assurance

**Status: Planned; begin incrementally during Phases 5–9**

- Add unit tests for detector logic.
- Test debouncer behavior.
- Test event-manager listener isolation.
- Add integration tests for the full pipeline using synthetic test video through webcam and upload paths.
- Add API tests for all FastAPI routes, including invalid uploads and missing webcams.
- Add performance tests for frame-processing latency under load and multiple simultaneous streams.
- Complete a bug-fixing pass based on test results.

Testing is not a one-time final gate. Unit tests should be written alongside Phases 5–9 rather than deferred entirely to this phase.

## Phase 11 — Deployment and Operations

**Status: Planned**

- Dockerize the backend and database.
- Deploy to a staging environment for real-world camera testing.
- Deploy to production, preferably on a GPU-enabled host for real-time inference.
- Add monitoring and alerting for system health, not only threat alerts.
- Verify that operators can tell when the surveillance system itself is degraded or offline.

## Phase 12 — Feedback and Continuous Improvement

**Status: Planned**

- Establish a feedback loop with security personnel using the dashboard.
- Fix issues found in actual deployments.
- Retrain custom models as labeled incident data accumulates.
- Maintain the future-enhancement backlog described in `PRD.md`, especially its Could-Have section.

## Dependency Map

```text
Phase 1 ─┬─> Phase 2 ─> Phase 3 ─> Phase 4 ─┬─> Phase 5 ─> Phase 9
         │                                  └─> Phase 6
         └────────────────────────────────────> Phase 7 ─> Phase 8

Phases 5–9 ─> Phase 10 ─> Phase 11 ─> Phase 12
```

- Phase 5 is a prerequisite for Phase 9.
- Phase 6 may proceed in parallel with Phase 5.
- Phase 7 must precede any real deployment of Phase 8.
- Phase 10 begins alongside implementation and continues through later phases.
