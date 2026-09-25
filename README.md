# AI-Driven Intelligent Surveillance System

Real-time threat detection (fire/smoke, weapons, violence, accidents) from
webcam, uploaded video, or uploaded images, with instant Telegram alerts.

## Phase 1: Environment Setup ✅

This phase sets up the project skeleton, dependencies, configuration, and a
minimal running server. The application now includes AI/video processing and
accident detection using the trained YOLO weights.

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
./venv311/bin/python -m uvicorn backend.app:app --host 0.0.0.0 --port 8000
```

### 5. Verify it works

Open your browser to:

- `http://localhost:8000/` — surveillance dashboard
- `http://localhost:8000/health` — server status
- `http://localhost:8000/config-check` — loaded configuration
- `http://localhost:8000/docs` — interactive API documentation

## Phase 2: Video and Image Ingestion ✅

The application supports live webcam streaming, video upload, image upload,
and AI analysis. Uploaded videos stream via MJPEG, while uploaded images are
processed once and returned as annotated JPEGs.

### Try it

1. Run the server and open `http://localhost:8000/`.
2. Click **Start Webcam Feed** to use a connected webcam.
3. Use **Upload Video or Image** to upload a supported file.

Supported videos: `.mp4`, `.avi`, `.mov`, `.mkv`, `.webm`

Supported images: `.jpg`, `.jpeg`, `.png`, `.bmp`, `.webp`

### Endpoints

| Endpoint | Method | Purpose |
|---|---|---|
| `/video_feed` | GET | Live webcam MJPEG stream |
| `/upload` | POST | Upload a video or image |
| `/uploads` | GET | List uploaded media |
| `/video_feed/uploaded/{filename}` | GET | Stream video or return a processed image |

### Design notes

- `VideoStream` wraps webcam and uploaded video sources.
- Video inference uses frame skipping to reduce processing cost.
- Uploaded images are analyzed once and returned as JPEG.
- Uploads are validated by extension and capped at 500MB by default.
- Accident detection loads the trained model from:

```text
data/Accident_detect_dataset/runs/detect/training_runs/yolo_100_epochs/weights/best.pt
```

- Stock fallback detectors use `yolo11n.pt`.
- Set `ACCIDENT_MODEL_PATH` in `.env` to override the accident model path.

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

## Roadmap

- [x] Project setup and environment
- [x] Video and image ingestion
- [x] Detection models
- [x] Event handling and debouncing
- [x] Database
- [ ] Telegram bot integration
- [x] Dashboard/frontend
- [ ] Deployment
