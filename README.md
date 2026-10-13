# AI-Driven Intelligent Surveillance System

Real-time threat detection (fire/smoke, weapons, violence, accidents) from
webcam, configured cameras, uploaded video, or uploaded images, with event
history, review workflows, and Telegram alerts.

## What is included

- YOLO-based fire/smoke, weapon, violence, and accident detection.
- Live webcam and uploaded-media processing with MJPEG streaming.
- JWT authentication with viewer and administrator roles.
- Event persistence, debouncing, review status, analytics, and CSV export.
- Camera registration and activation controls.
- Configurable detection, retention, and alert settings.
- Telegram notifications with optional event screenshots.

## Quick start

The commands below use a local virtual environment. Python 3.11 is recommended.

### 1. Create and activate a virtual environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

> Note: `torch`/`torchvision` installation can take a while and may need a
> CUDA-specific version if you have a GPU.

### 3. Set up environment variables

```bash
cp .env.example .env
```

Edit `.env` with your values. Telegram credentials are only needed for
Telegram alerts.

### 4. Run the server

From the project root:

```bash
python -m uvicorn backend.app:app --host 0.0.0.0 --port 8000
```

### 5. Verify it works

Open your browser to:

- `http://localhost:8000/` — surveillance dashboard
- `http://localhost:8000/health` — server status
- `http://localhost:8000/config-check` — loaded configuration
- `http://localhost:8000/docs` — interactive API documentation

Register the first user at `/register`. New registrations receive the `viewer`
role; an administrator can promote users through the authenticated role API.

## Media ingestion

The application supports live webcam streaming, video upload, image upload,
and AI analysis. Uploaded videos stream via MJPEG, while uploaded images are
processed once and returned as annotated JPEGs.

### Try it

1. Run the server and open `http://localhost:8000/`.
2. Click **Start Webcam Feed** to use a connected webcam.
3. Use **Upload Video or Image** to upload a supported file.

Supported videos: `.mp4`, `.avi`, `.mov`, `.mkv`, `.webm`

Supported images: `.jpg`, `.jpeg`, `.png`, `.bmp`, `.webp`

### Media endpoints

| Endpoint | Method | Purpose |
|---|---|---|
| `/video_feed` | GET | Live webcam MJPEG stream |
| `/upload` | POST | Upload a video or image |
| `/uploads` | GET | List uploaded media |
| `/video_feed/uploaded/{filename}` | GET | Stream video or return a processed image |

## API overview

The complete, interactive API is available at `/docs`. The main route groups are:

| Route | Purpose |
|---|---|
| `/auth` | Registration, login, current-user, password reset, and user administration |
| `/api/events` | Event history, review, analytics, cleanup, and CSV export |
| `/api/cameras` | Camera registration, activation, deletion, and feeds |
| `/api/settings` | Detection, retention, and alert configuration |

Protected routes require a JWT bearer token. Event deletion, user management,
camera administration, and settings updates require the `admin` role.

### Design notes

- `VideoStream` wraps webcam and uploaded video sources.
- Video inference uses frame skipping to reduce processing cost.
- Uploaded images are analyzed once and returned as JPEG.
- Uploads are validated by extension and capped at 500MB by default.
- Accident detection loads the trained model from:

```text
data/Accident_detect/best.pt
```

- Weapon detection loads the single-class (`weapon`) YOLO model from:

```text
data/Weapon_detect/best.pt
```

- Set `WEAPON_MODEL_PATH` in `.env` to override the weapon model path.
- Set `WEAPON_CONFIDENCE_THRESHOLD` in `.env` to adjust the weapon detector
  cutoff.

- Authentication is provided under `/auth` with JWT bearer tokens. Configure
  `JWT_SECRET_KEY` in `.env` before deployment. Public registration creates a
  `viewer`; an existing administrator can promote users through
  `PATCH /auth/users/{user_id}/role`. Event history and review routes require
  authentication, while event deletion and user administration require the
  `admin` role.

- Password reset currently logs the one-time token at INFO level for
  development because no email provider is configured. Connect SMTP, SES, or
  another mail provider before production use.

- Telegram alerts are sent by the synchronous listener in
  `backend/telegram_bot/alert_sender.py`. Set `TELEGRAM_BOT_TOKEN` and
  `TELEGRAM_CHAT_ID` in `.env`; alerts include the event screenshot when it is
  available and fall back to a text message otherwise. Test the credentials
  with:

```bash
python -c "from backend.telegram_bot.alert_sender import send_test_message; send_test_message()"
```

- Stock fallback detectors use `yolo11n.pt`.
- Set `ACCIDENT_MODEL_PATH` in `.env` to override the accident model path.

## Configuration and production notes

Copy `.env.example` to `.env` and review every value before starting the app.
At minimum, replace `JWT_SECRET_KEY` with a strong secret in non-development
environments. The default database is SQLite; set `DATABASE_URL` to use another
SQLAlchemy-supported database.

Password reset currently logs the one-time token at INFO level because no email
provider is configured. Configure SMTP, SES, or another mail provider before
using password reset in production. Keep `.env` and model weights out of source
control unless they are intentionally public.

## Project Structure

```text
surveillance-system/
├── backend/
│   ├── app.py              # FastAPI entrypoint
│   ├── config.py           # Centralized settings
│   ├── models/             # Model weights
│   ├── detection/          # Detection logic
│   ├── telegram_bot/       # Telegram integration
│   ├── database/           # Database models and queries
│   └── utils/              # Shared helpers
├── frontend/
│   └── templates/          # Dashboard templates
├── static/
│   ├── screenshots/        # Captured threat screenshots
│   └── uploads/            # Uploaded videos and images
├── requirements.txt
└── README.md
```

## Project status

- [x] Project setup and environment
- [x] Video and image ingestion
- [x] Detection models
- [x] Event handling and debouncing
- [x] Database
- [x] Telegram bot integration
- [x] Dashboard/frontend
- [x] Authentication and role-based access
- [x] Camera and system-settings APIs
- [ ] Production deployment and external email provider
