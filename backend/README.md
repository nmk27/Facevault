# FaceVault Backend

Django REST backend for FaceVault. This service handles photo ingestion, media processing, face detection, embedding generation, and face metadata APIs used by the React frontend.

## Quick Context (For New Chat Sessions)

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
  2. Run face detection using MTCNN.
  3. Open source image and iterate detections.
  4. Skip detections where `confidence < 0.95`.
  5. Crop each accepted face and generate embedding via `generate_embedding(cropped_face)`.
  6. Create `Face` record with bbox, confidence, cropped image, embedding.
  7. **Auto-run clustering** to update `person_id` for all embedded faces.

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
- Input: PIL image converted to RGB.
- Output: list of detections with `box` (x1, y1, x2, y2) and `confidence`.
- Detections with confidence < 0.95 are filtered out in the upload view.

### Embeddings (`ml/generate_embeddings.py`)
- Model: `InceptionResnetV1(pretrained='vggface2').eval()`.
- Preprocessing:
  - convert to RGB
  - resize to 160x160
  - convert to tensor and normalize by 255
- Output:
  - 512-dimensional embedding as Python list (JSON serializable)

### Clustering (`ml/cluster_faces.py`)
- **Auto-runs after every upload**, but only ever processes faces with `person=None` — existing people are left untouched, so names never get reshuffled by a later upload.
- Step 1: each unassigned face is compared (cosine similarity on L2-normalized embeddings) against every existing person's centroid; a match >= `1 - FACE_CLUSTER_EPS` attaches it to that person.
- Step 2: anything still unassigned is clustered among itself with DBSCAN (cosine distance); each resulting cluster of size >= `FACE_CLUSTER_MIN_SAMPLES` becomes a brand-new `Person`. Leftover singletons stay `person=None` (same "noise" semantics as DBSCAN's `-1` label before).
- Configurable via environment variables:
  - `FACE_CLUSTER_EPS`: distance threshold (default `0.4`)
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
- Confidence threshold is hardcoded at `0.95` in upload view.
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
