# Project Memory — Progress, Decisions, and Current State

This is a living document. Update it at the end of every work session. Stale or inaccurate entries are worse than no entry; remove anything that is no longer true.

## 1. Key Context and Decisions

### Core Architectural Decisions

- **Decoupled listener pattern:** Database writes and Telegram alerts are independent listeners on `EventManager`. A failing listener must not block the other listener or crash detection.
- **Common detector interface:** All four threat types use `BaseDetector`, so the detection loop does not depend on a specific model. New threat types can be added without changing the pipeline.
- **YOLO26 for stock detection:** Stock/pretrained model calls use YOLO26 rather than YOLOv8 because it is the current Ultralytics model generation and is intended to improve CPU inference performance and small-object detection. This matters because the project may run several models per frame. Custom `fire_smoke.pt` and `weapons.pt` paths are unaffected.
- **Frame skipping at ingestion:** `VideoStream` controls one shared, `.env`-configurable frame cadence instead of allowing each detector to choose its own schedule.
- **Heuristic accident detection:** Accident detection uses stock YOLO vehicle classes with vehicle tracking, sudden-deceleration, and bounding-box-overlap heuristics. It works without custom training but may produce false positives until thresholds are tuned against real footage.
- **Placeholder detectors:** Fire/smoke, weapon, and violence detectors remain placeholders until custom-trained weights are provided. They run without crashing and return empty detection lists, allowing the rest of the pipeline to be developed in parallel with model training.

### Project Settings and Preferences

- Default confidence threshold: `0.6`, configurable through `.env`.
- Default frame skip: process every fifth frame, configurable through `.env`.
- Default alert cooldown: 45 seconds per `(source, event_type)` pair, configurable through `.env`.
- Maximum upload size: 500 MB.
- Allowed video formats: `.mp4`, `.avi`, `.mov`, `.mkv`, `.webm`.

## 2. What Happened

| Date/phase | Change | Notes |
| --- | --- | --- |
| Phase 1 | Project setup complete | FastAPI skeleton, configuration system, and folder structure established. Verified with `/health` and `/config-check`. |
| Phase 2 | Video ingestion complete | `VideoStream` supports webcam and uploaded-file sources through one interface. MJPEG streaming was implemented and tested with synthetic video. Webcam failure is handled gracefully with HTTP 503. Upload type and size validation were tested. |
| Phase 3 | Detection models scaffolded | All four detectors use `BaseDetector`; `DetectorManager` orchestrates them. Accident detection is functional with stock vehicle classes; the other three are placeholders pending custom weights. |
| Phase 3 follow-up | YOLO version updated | Stock loading changed from `yolov8n.pt` to `yolo26n.pt` in the fire/smoke, weapon, and accident detectors. `requirements.txt` now requires `ultralytics>=8.4.0`. |
| Phase 4 | Event handling and debouncing complete | `SecurityEvent`, `Debouncer`, and `EventManager` are implemented with screenshot capture and pluggable listeners. Database and Telegram integration can register without changing this layer. |
| Phase 5 | Database and event-history API complete | Added SQLAlchemy engine/session setup, `EventModel`, CRUD operations, analytics, database listener, startup initialization, and `/api/events` routes. Validated with an isolated SQLite integration test. |
| Documentation | Core documentation created | `PRD.md`, `Architecture.md`, `Rules.md`, `phases.md`, `design.md`, and this `memory.md` define the product, architecture, standards, roadmap, visual system, and project state. |

## 3. Problems Faced and Solutions

- **No real webcam in the development environment:** A synthetic OpenCV test video was generated to validate the upload-to-stream pipeline. Webcam-specific code was confirmed to fail gracefully with HTTP 503. Real webcam testing remains required on a machine with a camera.
- **Jinja2/Starlette version mismatch:** `TemplateResponse("index.html", {"request": request})` raised `TypeError: unhashable type: 'dict'` after a Starlette API change. The call was corrected to `templates.TemplateResponse(request, "index.html", {})`. Check the installed `TemplateResponse` signature after future Starlette upgrades.
- **Background servers did not persist between tool invocations:** Server startup and test requests had to run in the same command execution.
- **YOLO26 checkpoint download in the sandbox:** The YOLO26 sanity check initially failed because sandbox DNS blocked GitHub. After network-enabled execution, Ultralytics 8.4.150 downloaded `yolo26n.pt` and all four detector classes instantiated successfully. The generated checkpoint was removed from the project afterward.

## 4. Current Status

**Status:** Phase 5 is complete. Documentation and database persistence are established. The project is ready to begin Phase 6 (Telegram Bot Integration).

**Current file/module focus:** None actively in progress.

**Recommended next step:** Implement Phase 6 (Telegram Bot Integration). Before production deployment, add Alembic migrations for schema evolution and authentication before exposing the dashboard to real users.

## 5. Update Discipline

- Update this file at the end of every development session, not only at phase boundaries.
- Record partial progress within a phase.
- When a decision changes, update or remove the old entry instead of leaving contradictory information.
- Remove completed entries from the “Currently Working” section and record their outcomes in “What Happened.”
- Delete problem/solution entries that are no longer relevant.
- Keep this document reflective of the current state, not merely a history of every idea considered.

## 6. Purpose

This file exists to:

- Preserve context across sessions so a future contributor or AI assistant can understand what has been built and why.
- Avoid re-litigating settled decisions such as the move from YOLOv8 to YOLO26.
- Prevent rediscovery of solved issues such as the Starlette `TemplateResponse` signature change.
- Keep important limitations visible, especially that three of the four detectors are placeholders and the system is not yet fully capable of detecting all four threat categories.
