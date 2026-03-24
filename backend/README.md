# FaceVault Backend

Django REST backend for FaceVault. This service handles photo ingestion, media processing, face detection, embedding generation, and face metadata APIs used by the Flutter frontend.

## Quick Context (For New Chat Sessions)

- Backend role: receives uploads and runs the ML pipeline.
- Main entrypoint: `POST /photos/upload/`.
- Data model core: `Photo` and `Face`.
- Face clustering logic exists (`ml/cluster_faces.py`) but is not wired into an API or scheduled workflow yet.
- Current environment is development-focused (debug enabled, open CORS, hardcoded DB credentials).

## Responsibilities

- Store uploaded images and generated thumbnails.
- Detect faces in photos.
- Save cropped face images.
- Generate and store FaceNet embeddings.
- Serve photo list and per-photo face metadata via REST endpoints.

## Tech Stack

Framework and API:
- Django 5.2.12
- Django REST Framework 3.16.1
- django-cors-headers

Database:
- PostgreSQL (via `psycopg2-binary`)

ML and image processing:
- facenet-pytorch
- torch / torchvision
- scikit-learn
- numpy
- Pillow
- pillow-heif (HEIC/HEIF support)

## Backend Structure

```text
backend/
|- facevault/
|  |- settings.py
|  |- urls.py
|  |- asgi.py
|  |- wsgi.py
|- photos/
|  |- models.py
|  |- serializers.py
|  |- views.py
|  |- urls.py
|- faces/
|  |- models.py
|  |- views.py
|  |- urls.py
|  |- migrations/
|- ml/
|  |- __init__.py
|  |- detect_faces.py
|  |- generate_embeddings.py
|  |- cluster_faces.py
|  |- dev_utils.py
|- users/
|  |- management/commands/dev_reset.py
|- media/
|  |- photos/
|  |- faces/
|- manage.py
|- requirements.txt
```

## Data Model

### Photo (`photos.models.Photo`)
Fields:
- `id`
- `image` (`ImageField`, upload path `photos/`)
- `thumbnail` (`ImageField`, nullable)
- `uploaded_at` (`DateTimeField`, auto)
- `width` (`IntegerField`, nullable)
- `height` (`IntegerField`, nullable)

Save behavior:
- Opens uploaded image with PIL.
- Stores width/height.
- Applies EXIF orientation correction.
- Generates thumbnail with max size 300x300.
- Saves thumbnail path as `photos/thumb_<original_name>`.

### Face (`faces.models.Face`)
Fields:
- `id`
- `photo` (FK to `Photo`, cascade delete)
- `x`, `y`, `width`, `height` (bounding box)
- `confidence` (float)
- `face_image` (`ImageField`, upload path `faces/`, nullable)
- `embedding` (`JSONField`, nullable)
- `person_id` (`IntegerField`, nullable)
- `created_at` (`DateTimeField`, auto)

## API Endpoints

Root URL registration is in `facevault/urls.py`.

### `GET /photos/`
- View: `photos.views.PhotoListView`
- Behavior:
  - returns photos ordered by `-uploaded_at`
  - paginated response via DRF page-number pagination
- Current pagination size: `PAGE_SIZE = 2`

### `POST /photos/upload/`
- View: `photos.views.upload_photo`
- Request:
  - multipart/form-data
  - file field: `image`
- Success response:
  - `201 Created`
  - serialized `Photo`
- Processing pipeline:
  1. Save photo via serializer.
  2. Run `detect_faces(image_path)`.
  3. Open source image and iterate detections.
  4. Skip detections where `confidence < 0.95`.
  5. Crop each accepted face.
  6. Generate embedding via `generate_embedding(cropped_face)`.
  7. Create `Face` record with bbox, confidence, cropped image, embedding.

### `GET /faces/<photo_id>/`
- View: `faces.views.get_faces`
- Returns list of objects with:
  - `x`, `y`, `width`, `height`, `confidence`

## ML Pipeline Details

### HEIC/HEIF support
- Registered at import time in `ml/__init__.py` with `pillow_heif.register_heif_opener()`.

### Face detection (`ml/detect_faces.py`)
- Detector: `MTCNN()` from facenet-pytorch.
- Input: PIL image converted to RGB and numpy array.
- Output: list of detections containing `box` and `confidence`.

### Embeddings (`ml/generate_embeddings.py`)
- Model: `InceptionResnetV1(pretrained='vggface2').eval()`.
- Preprocessing:
  - convert to RGB
  - resize to 160x160
  - convert to tensor and normalize by 255
- Output:
  - 512-dimensional embedding as Python list (JSON serializable)

### Clustering (`ml/cluster_faces.py`)
- Collects all faces with non-null embeddings.
- Runs DBSCAN with:
  - `eps=0.6`
  - `min_samples=2`
- Writes DBSCAN label to `Face.person_id`.

Status:
- Implemented as callable function.
- Not integrated into API endpoints or automation yet.

## Development Commands

Run server:

```bash
cd backend
python manage.py runserver
```

Apply migrations:

```bash
python manage.py migrate
```

Create admin user:

```bash
python manage.py createsuperuser
```

## Development Reset Command

```bash
python manage.py dev_reset
```

What it does:
- Deletes all `Face` and `Photo` rows.
- Attempts PostgreSQL sequence reset.
- Includes SQLite sequence reset fallback.
- Recreates `media/photos` and `media/faces` folders.

## Optional Utility Functions (`ml/dev_utils.py`)

Useful from Django shell for local experiments:
- `clear_faces(delete_files=True)`
- `clear_embeddings()`
- `reset_clustering()`
- `reset_db_sequences()`
- `clear_everything(delete_files=True)`
- `face_count()`
- `photo_count()`

## Setup

### Prerequisites
- Python 3.10+
- PostgreSQL instance

### Install

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### Database and Migrations

Update database settings in `facevault/settings.py` if needed, then run:

```bash
python manage.py migrate
```

### Run

```bash
python manage.py runserver
```

Backend default development URL:
- `http://127.0.0.1:8000`

## Current Backend Progress

Implemented:
- Photo model with thumbnail generation and metadata capture.
- Face model with bbox, confidence, crop path, embedding, person_id.
- Upload endpoint with integrated detection and embedding generation.
- Photo list and per-photo faces retrieval endpoints.
- HEIC support registration.
- Clustering function with DBSCAN.
- Dev reset command for fast clean-state iteration.

Not yet implemented:
- People endpoints based on `person_id`.
- Auto-triggered clustering workflow.
- Background/async pipeline execution.
- Authentication and permissions.
- Comprehensive test coverage.

## Known Risks and Caveats

- Upload pipeline is synchronous and may be slow on large images or many faces.
- Confidence threshold is hardcoded at `0.95`.
- CORS currently allows all origins.
- `DEBUG=True` in settings.
- Database credentials are currently hardcoded.
- No explicit image validation/retry safeguards around ML calls.

## Backend Roadmap

### Phase 1: Clustering Operations
- Add management command to run clustering.
- Optionally trigger clustering after upload (or on schedule).

### Phase 2: People API
- `GET /people/` to list identities.
- `GET /people/<person_id>/` to fetch related faces/photos.

### Phase 3: Hardening
- Move secrets and DB config to env vars.
- Restrict CORS and allowed hosts.
- Add structured logging and better exception handling.
- Expand automated tests (API + pipeline + serializers).

### Phase 4: Scale Path (Optional)
- Offload ML to async workers (Celery/Redis).
- Add bulk/batch ingestion support.
- Add re-embedding/re-clustering admin flows.
