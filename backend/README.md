# FaceVault Backend

Django REST backend for FaceVault. This service handles photo ingestion, media processing, face detection, embedding generation, and face metadata APIs used by the React frontend.

## Overview

- Backend role: receives uploads and runs the ML pipeline (detection, embedding, auto-clustering).
- Main entrypoint: `POST /photos/upload/`.
- Data model core: `Photo`, `Face`, and `Person`.
- Face clustering: auto-runs after each upload. Unclustered faces are first matched against existing `Person` centroids (cosine similarity); leftovers are clustered with DBSCAN and become new `Person` rows. Existing people are never recomputed away, so names persist.
- People endpoints: `GET /faces/people/`, `GET /faces/people/<id>/`, and `PATCH /faces/people/<id>/` (rename).
- Settings are environment-driven (see `.env.example`) with dev-friendly defaults; `DEBUG`, DB credentials, and CORS origins are no longer hardcoded.

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
|  |- clustering.py
|  |- image_utils.py
|  |- dev_utils.py
|- evaluation/
|  |- evaluate_lfw.py
|  |- README.md
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
- `taken_at` (`DateTimeField`, nullable) — EXIF capture time (camera wall-clock time stored as UTC)
- `width` (`IntegerField`, nullable) — size as displayed (EXIF orientation applied)
- `height` (`IntegerField`, nullable)

Ingest (runs once, when the row is first created):
- Opens the uploaded image with PIL and applies EXIF orientation.
- Stores width/height of the oriented image, so they match what browsers display and what face boxes use.
- Reads the EXIF capture date into `taken_at`.
- Converts formats browsers cannot display (e.g. HEIC/HEIF) to JPEG; JPEG/PNG/WebP originals are stored byte-for-byte.
- Generates a JPEG thumbnail (max 300x300) under `thumbnails/thumb_<original_stem>.jpg`.

### Face (`faces.models.Face`)
Fields:
- `id`
- `photo` (FK to `Photo`, cascade delete)
- `x`, `y`, `width`, `height` (bounding box)
- `confidence` (float)
- `face_image` (`ImageField`, upload path `faces/`, nullable)
- `embedding` (`JSONField`, nullable)
- `person` (FK to `Person`, nullable, `on_delete=SET_NULL`) — `null` means not yet matched to anyone
- `created_at` (`DateTimeField`, auto)

### Person (`faces.models.Person`)
Fields:
- `id`
- `name` (`CharField`, blank until renamed — API falls back to `"Person {id}"`)
- `created_at`, `updated_at`

Created only when a fresh cluster of size >= `FACE_CLUSTER_MIN_SAMPLES` emerges; never recreated for an existing identity, so a rename survives future uploads.

## API Endpoints

Root URL registration is in `facevault/urls.py`.

### `GET /photos/`
- View: `photos.views.PhotoListView`
- Behavior:
  - returns photos newest first by capture date (`taken_at`), falling back to `uploaded_at`
  - paginated response via DRF page-number pagination
- Current pagination size: `PAGE_SIZE = 24`

### `GET /photos/<photo_id>/`
- View: `photos.views.PhotoDetailView`
- Returns one serialized photo; `404` if it does not exist

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
  2. Run face detection using MTCNN.
  3. Detect on the oriented image, then iterate detections.
  4. Skip detections where `confidence < 0.95`.
  5. Crop each accepted face and generate embedding via `generate_embedding(cropped_face)`.
  6. Create `Face` record with bbox, confidence, cropped image, embedding.
  7. **Auto-run clustering** to assign each embedded face to a `Person`.

### `GET /faces/<photo_id>/`
- View: `faces.views.get_faces`
- Returns list of faces detected in a specific photo with:
  - `id`, `x`, `y`, `width`, `height`, `confidence`, `person_id`

### `GET /faces/people/`
- View: `faces.views.list_people`
- Returns every `Person` with at least one face
- Response format: `[{id: int, name: string, face_count: int}, ...]`

### `GET /faces/people/<person_id>/`
- View: `faces.views.get_person_faces`
- Returns `{ person: {id, name, face_count}, faces: [...] }`
- Each face includes bbox (x, y, width, height), confidence, `person_id`, photo reference (id, image URL, thumbnail URL), `face_image` URL, `created_at`
- Returns `404` if the person doesn't exist

### `PATCH /faces/people/<person_id>/`
- View: `faces.views.get_person_faces` (same view, method-dispatched)
- Body: `{"name": "..."}` (non-empty, <= 100 chars)
- Renames the person; returns the updated `{id, name, face_count}` summary
- `400` on empty/oversized name

## ML Pipeline Details

### HEIC/HEIF support
- Registered at import time in `ml/__init__.py` with `pillow_heif.register_heif_opener()`.

### Face detection (`ml/detect_faces.py`)
- Detector: `MTCNN()` from facenet-pytorch.
- Input: a PIL image, or an image path (opened with EXIF orientation applied); converted to RGB.
- Boxes are in the pixel space of the image as displayed.
- Output: list of detections with `box` (x1, y1, x2, y2) and `confidence`.
- Detections with confidence < `MIN_FACE_CONFIDENCE` (0.95, defined in `ml/detect_faces.py`) are filtered out in the upload view.

### Embeddings (`ml/generate_embeddings.py`)
- Model: `InceptionResnetV1(pretrained='vggface2').eval()`.
- Preprocessing:
  - convert to RGB
  - resize to 160x160
  - convert to tensor and scale as FaceNet expects, `(pixels - 127.5) / 128` (`STANDARDIZE_EMBEDDINGS` in `ml/defaults.py`; the original `pixels / 255` is still available as `generate_embedding(image, standardize=False)`)
- Output:
  - 512-dimensional embedding as Python list (JSON serializable)

### Clustering (`ml/cluster_faces.py`, decision logic in `ml/clustering.py`)
- **Auto-runs after every upload**, but only ever processes faces with `person=None` — existing people are left untouched, so names never get reshuffled by a later upload.
- Step 1: each unassigned face is compared (cosine similarity on L2-normalized embeddings) against every existing person's centroid; a match >= `1 - FACE_CLUSTER_EPS` attaches it to that person.
- Step 2: anything still unassigned is clustered among itself with DBSCAN (cosine distance); each resulting cluster of size >= `FACE_CLUSTER_MIN_SAMPLES` becomes a brand-new `Person`. Leftover singletons stay `person=None` (same "noise" semantics as DBSCAN's `-1` label before).
- Configurable via environment variables:
  - `FACE_CLUSTER_EPS`: distance threshold (default `0.2`, chosen on LFW held-out people; `0.4` merges unrelated people, see `evaluation/README.md`). A `FACE_CLUSTER_EPS` in your `.env` overrides this default, so update it if you copied an older `.env.example`
  - `FACE_CLUSTER_MIN_SAMPLES`: minimum samples per new cluster (default `2`)
- Returns metadata: `faces_processed`, `existing_person_matches`, `new_persons_created`, `noise_faces`, `eps`, `min_samples`.

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
- Python 3.11–3.12 (the pinned `torch==2.2.2` has no wheels for 3.13+, and pinned packages such as `networkx==3.6.1` need 3.11+)
- PostgreSQL instance (or SQLite via `DB_ENGINE`, see below)

### Install

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### Database and Migrations

Copy `.env.example` to `.env` and adjust the `DB_*` values (settings read them from the environment). To use SQLite instead of PostgreSQL, set `DB_ENGINE=django.db.backends.sqlite3` and `DB_NAME=db.sqlite3`. Then run:

```bash
python manage.py migrate
```

### Run

```bash
python manage.py runserver
```

### Test

```bash
DB_ENGINE=django.db.backends.sqlite3 python manage.py test
```

The tests use synthetic images and mock the ML calls, so they need no model weights or network access.

Backend default development URL:
- `http://127.0.0.1:8000`

## Current Backend Progress

Implemented:
- Photo model with thumbnail generation and metadata capture.
- Face model with bbox, confidence, crop path, embedding, person_id.
- Upload endpoint with integrated detection, embedding generation, and **auto-clustering**.
- Photo list and per-photo face metadata retrieval endpoints.
- **People endpoints**: list all identities, retrieve all faces for a specific person.
- HEIC support registration.
- **Improved clustering**: DBSCAN with cosine distance, configurable thresholds.
- Dev reset command for fast clean-state iteration.
- Automatic clustering after each upload; facial identity grouping.

Not yet implemented:
- Manual clustering trigger endpoint (optional).
- Background/async pipeline execution (currently synchronous).
- Authentication and permissions.
- Comprehensive test coverage.
- Re-identification/re-embedding workflows (e.g. merging two people, splitting a bad cluster).

## Known Risks and Caveats

- Upload pipeline is synchronous (blocks request while running ML inference).
- The face confidence threshold is a constant (`MIN_FACE_CONFIDENCE = 0.95` in `ml/detect_faces.py`), not a setting.
- Clustering may leave valid faces unassigned (`person=None`) if insufficient similar samples exist yet.
- No authentication/authorization; all endpoints are open.
- `SECRET_KEY`, `DEBUG`, DB credentials, and CORS are now environment-driven (see `.env.example`) but the shipped defaults are still dev-oriented — set real values via `.env` before deploying.

## Backend Roadmap

### Phase 1: Clustering Operations ✅
- ✅ Improve clustering algorithm (cosine distance DBSCAN).
- ✅ Auto-trigger clustering after upload.
- ✅ Configurable clustering parameters via env vars.

### Phase 2: People API ✅
- ✅ `GET /faces/people/` to list identities.
- ✅ `GET /faces/people/<person_id>/` to fetch related faces/photos.

### Phase 3: Hardening
- ✅ Move secrets and DB config to env vars (`.env.example`).
- ✅ CORS is now allow-listed via `CORS_ALLOWED_ORIGINS` (opt back into wide-open with `CORS_ALLOW_ALL_ORIGINS=true`).
- ✅ Server-side image file size/type validation on upload.
- Add structured logging and better exception handling.
- Expand automated tests (API + pipeline + serializers).

### Phase 4: Optional Enhancements
- Manual clustering trigger endpoint (`POST /faces/cluster/`).
- Offload ML to async workers (Celery/Redis).
- Bulk/batch ingestion support.
- Re-embedding/re-clustering admin flows.
- Search/filter endpoints for faces by confidence, date range, etc.
