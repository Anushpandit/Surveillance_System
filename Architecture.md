# High-Level Design and Structure

## 1. Architecture Overview

### System Design Philosophy

The system is built as a layered pipeline where each stage has a single responsibility and communicates with the next through a well-defined interface. This allows individual layers—such as the YOLO version, database, or notification channel—to be replaced without rewriting surrounding layers.

```text
┌─────────────────────────────────────────────────────────────────┐
│                         CLIENT (Browser)                        │
│              Dashboard: live view, history, analytics           │
└───────────────────────────┬─────────────────────────────────────┘
                            │ HTTP / WebSocket
┌───────────────────────────▼─────────────────────────────────────┐
│                    FASTAPI BACKEND (app.py)                     │
│  ┌───────────────┐  ┌────────────────┐  ┌─────────────────────┐ │
│  │ Video Ingestion│→│ Detector Manager│→│  Event Manager      │ │
│  │ (webcam/upload)│  │ (Fire/Weapon/  │  │ (debounce, screen-  │ │
│  │                │  │  Violence/     │  │ shot, notify)      │ │
│  │                │  │  Accident)     │  │                    │ │
│  └───────────────┘  └────────────────┘  └──────────┬──────────┘ │
└────────────────────────────────────────────────────┼────────────┘
                                                     │
                    ┌────────────────────────────────┼──────────────┐
                    ▼                                ▼              │
         ┌─────────────────────┐          ┌─────────────────────┐  │
         │ Database (SQLite/   │          │ Telegram Bot API    │  │
         │ PostgreSQL)         │          │ (alert delivery)    │  │
         │ Event log storage   │          │                     │  │
         └─────────────────────┘          └─────────────────────┘  │
                                                                    │
                    ┌───────────────────────────────────────────────┘
                    ▼
         Screenshots stored to disk (static/screenshots/)
```

### Component Interaction Flow

1. `VideoStream` captures frames from a webcam or uploaded file and tags every Nth frame for AI processing through a centrally configured frame-skip interval.
2. `DetectorManager` runs the four threat detectors against tagged frames and returns a unified list of `Detection` objects.
3. `EventManager` receives detections, applies debounce logic to prevent alert spam for an ongoing incident, captures a screenshot, and constructs a `SecurityEvent`.
4. Listeners registered with `EventManager` run independently:
   - A database listener persists the event.
   - A Telegram listener sends the alert.
5. Failure of one listener must not crash the detection loop or block other listeners.
6. The dashboard reads from the database through API endpoints to display live status and historical search and filtering.

### Key Architectural Decisions

| Decision | Rationale |
| --- | --- |
| Decoupled listener pattern for events | Database and Telegram concerns remain separate from detection code; new notification channels can be added as listeners. |
| Common `BaseDetector` interface | The detection loop does not need to know which model produced a result. New threat types can be added without changing the pipeline. |
| Frame skipping at the ingestion layer | A shared, centrally configurable cadence prevents each detector from independently deciding how often to run. |
| Screenshot capture in `EventManager` | Detectors remain pure—frame in, detections out—with no side effects, making them easier to test. |
| MJPEG streaming for dashboard video | MJPEG is simple and broadly browser-compatible without the complexity of WebRTC for this use case. |

## 2. Folder and File Structure

```text
surveillance-system/
├── backend/
│   ├── app.py                       # FastAPI entrypoint, route definitions
│   ├── config.py                    # Centralized settings (reads .env)
│   ├── models/                      # YOLO/action-recognition weights (gitignored)
│   │   ├── fire_smoke.pt
│   │   ├── weapons.pt
│   │   └── violence.pt
│   ├── detection/
│   │   ├── base_detector.py         # Shared Detection dataclass + interface
│   │   ├── fire_smoke_detector.py
│   │   ├── weapon_detector.py
│   │   ├── violence_detector.py
│   │   ├── accident_detector.py
│   │   └── detector_manager.py      # Orchestrates all four detectors
│   ├── events/
│   │   ├── event.py                 # SecurityEvent dataclass
│   │   ├── debouncer.py             # Alert cooldown logic
│   │   └── event_manager.py         # Pipeline + listener registry
│   ├── database/
│   │   ├── models.py                # SQLAlchemy ORM models
│   │   ├── database.py              # DB session/engine setup
│   │   └── crud.py                  # Create/read/update/delete operations
│   ├── telegram_bot/
│   │   └── alert_sender.py          # Telegram Bot API integration
│   ├── utils/
│   │   ├── video_stream.py          # VideoStream + WebcamManager
│   │   ├── upload_handler.py        # Upload validation and saving
│   │   └── screenshot.py            # Screenshot capture to disk
│   └── processing_loop.py           # Ingestion → detection → events
├── frontend/
│   ├── templates/
│   │   └── index.html               # Dashboard entry page
│   └── static/
│       ├── css/
│       └── js/
├── static/
│   ├── screenshots/                 # Captured incident screenshots
│   └── uploads/                     # User-uploaded videos
├── docs/
│   ├── PRD.md
│   ├── Architecture.md
│   ├── Rules.md
│   ├── phases.md
│   ├── design.md
│   └── memory.md
├── tests/
│   ├── test_detection/
│   ├── test_events/
│   └── test_api/
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

### Structure Principles

- Each top-level backend folder has one primary concern: detection, events, database, Telegram, or utilities.
- Configuration is centralized in `config.py`; modules should not read environment variables directly.
- Model weights, screenshots, and uploaded videos are generated or binary assets and should remain outside version control through `.gitignore`.

## 3. Technology Stack

### Backend

| Technology | Purpose |
| --- | --- |
| Python 3.11+ | Primary language |
| FastAPI | Web framework, async support, and generated API documentation |
| Uvicorn | ASGI server |
| OpenCV (`opencv-python`) | Video capture, frame processing, and image encoding |
| Ultralytics YOLO26 | Object detection for fire/smoke, weapons, and vehicles |
| PyTorch | Deep-learning runtime for YOLO and action-recognition models |
| SQLAlchemy | ORM for database access |
| SQLite / PostgreSQL | Development / production event storage |
| `python-telegram-bot` | Telegram Bot API integration |

### Frontend

| Technology | Purpose |
| --- | --- |
| HTML/CSS/JavaScript | Dashboard UI; React may be adopted if the application scales |
| Jinja2 | Server-side template rendering |
| Chart.js or Recharts | Analytics visualizations |

### Infrastructure

| Technology | Purpose |
| --- | --- |
| Docker | Containerization for consistent deployment |
| GPU-enabled host | Optional, recommended for real-time inference performance |
| `python-dotenv` | Environment-variable management |

### Development Tools

| Technology | Purpose |
| --- | --- |
| pytest | Unit and integration testing |
| Git | Version control |
| Roboflow | Dataset sourcing and annotation for custom model training |
