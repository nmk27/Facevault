# FaceVault

FaceVault is a full-stack photo application inspired by Google Photos workflows. It lets users upload images, automatically detects faces, generates embeddings, stores cropped face data, and displays results in a Flutter UI.

The project is currently a strong portfolio-stage prototype with a complete upload-to-detection pipeline, basic gallery UX, and face overlays. Person-level grouping and production hardening are the next major steps.

## Quick Context (For New Chat Sessions)

If you are reading this in a fresh chat, this is the fastest way to understand the project:

- Product goal: Google Photos-style app with face detection and person grouping.
- Current state: upload + detection + embeddings + gallery + face overlay are working.
- Key gap: person grouping exists only as backend utility logic, not exposed as feature.
- Backend root: `backend/`
- Frontend root: `frontend/facevault/`
- Critical pipeline entrypoint: `POST /photos/upload/`
- Most important next deliverable: People API + People UI built on `Face.person_id`.

## Documentation Map

- Root overview: [README.md](README.md)
- Backend deep dive: [backend/README.md](backend/README.md)
- Frontend deep dive: [frontend/facevault/README.md](frontend/facevault/README.md)

## What This Project Does Today

- Upload photos from Flutter to Django REST API.
- Store original images and generated thumbnails.
- Detect faces in uploaded images.
- Crop and save detected faces as separate files.
- Generate 512-dimensional FaceNet embeddings per detected face.
- Persist detection metadata and embeddings in PostgreSQL.
- View a paginated gallery of uploaded photos.
- Open a photo and render detected face bounding boxes.

## Current Progress Snapshot

Current completion is approximately 60-70% toward a portfolio-ready "People clustering" product.

Completed core milestones:
- Backend photo upload and retrieval APIs
- Face detection and cropped-face persistence
- Embedding generation pipeline
- Frontend upload + gallery + photo detail overlay
- HEIC/HEIF image support
- Development reset tooling

Partially complete / pending milestones:
- Clustering exists as utility logic, but not exposed via API/automation
- No People endpoints yet (`/people/`, `/people/<id>/`)
- No frontend People tab/screens yet
- No authentication/authorization layer
- No production deployment/security hardening

## Architecture Overview

### Frontend
- Flutter app in `frontend/facevault/`
- Main screen: gallery with infinite scroll + upload FAB
- Photo detail screen: full image with face bounding boxes overlay

### Backend
- Django + Django REST Framework in `backend/`
- PostgreSQL database
- Media files served in development from `backend/media/`

### ML Pipeline
- Face detection: MTCNN
- Embeddings: FaceNet (`InceptionResnetV1`, pretrained on `vggface2`)
- Clustering: DBSCAN (utility function, manual invocation)

## Tech Stack (Verified)

Backend:
- Django 5.2.12
- Django REST Framework 3.16.1
- django-cors-headers 4.9.0
- PostgreSQL via `psycopg2-binary`

ML / CV:
- `facenet-pytorch`
- `torch`, `torchvision`
- `scikit-learn`
- `numpy`
- `pillow`
- `pillow-heif`

Frontend:
- Flutter (Dart)
- `http`
- `file_picker`
- `mime`

## Project Structure

```text
FaceVault/
|- backend/
|  |- facevault/              # Django settings, URLs, ASGI/WSGI
|  |- photos/                 # Photo model, serializers, upload/list API
|  |- faces/                  # Face model + face retrieval API
|  |- ml/                     # Detection, embeddings, clustering, dev utils
|  |- users/                  # Django app + custom dev command(s)
|  |- media/                  # Uploaded photos, thumbnails, face crops
|  |- manage.py
|  |- requirements.txt
|- frontend/
|  |- facevault/
|     |- lib/
|     |  |- models/
|     |  |- services/
|     |  |- screens/
|     |- pubspec.yaml
|- README.md
```

## Data Model

### Photo (`backend/photos/models.py`)
- `id`
- `image` (uploaded original)
- `thumbnail` (auto-generated)
- `width`
- `height`
- `uploaded_at`

Behavior:
- On save, image metadata is extracted.
- EXIF orientation is handled.
- Thumbnail (max 300x300) is generated and stored.

### Face (`backend/faces/models.py`)
- `id`
- `photo` (FK to `Photo`)
- `x`, `y`, `width`, `height` (bounding box)
- `confidence`
- `face_image` (cropped face)
- `embedding` (JSON vector, 512 dims)
- `person_id` (cluster label, nullable)
- `created_at`

## API Reference (Current)

Base URL in frontend is currently hardcoded as:
- `http://127.0.0.1:8000`

### 1) List Photos
- Endpoint: `GET /photos/`
- Behavior: paginated photo list, newest first
- Pagination: DRF page-number pagination, `PAGE_SIZE = 2`

### 2) Upload Photo
- Endpoint: `POST /photos/upload/`
- Content type: multipart/form-data
- File field: `image`
- Behavior:
	- saves photo
	- detects faces
	- filters out low-confidence detections (`confidence < 0.95`)
	- crops and stores faces
	- generates and stores embeddings
	- returns serialized photo

### 3) Get Faces for One Photo
- Endpoint: `GET /faces/<photo_id>/`
- Returns list of face boxes and confidence:
	- `x`, `y`, `width`, `height`, `confidence`

## End-to-End Upload Pipeline

1. User selects an image in Flutter gallery screen.
2. Frontend uploads to `POST /photos/upload/`.
3. Django stores the image and generates a thumbnail.
4. MTCNN runs face detection.
5. Each valid face is cropped and saved in `media/faces/`.
6. FaceNet embedding is generated per crop.
7. Face record is saved with bbox, confidence, crop path, embedding.
8. User opens photo detail and sees face rectangles overlaid.

## Clustering Status

Implemented utility:
- `backend/ml/cluster_faces.py` contains `cluster_faces()`
- Uses DBSCAN with:
	- `eps=0.6`
	- `min_samples=2`
- Writes labels to `Face.person_id`

Current limitation:
- Not auto-triggered after uploads
- No API endpoint/management command exposed yet

## Frontend Features (Current)

In `frontend/facevault/lib/`:

- `screens/gallery_screen.dart`
	- Infinite scrolling grid of thumbnails
	- Upload button using file picker
	- Error and empty states

- `screens/photo_view_screen.dart`
	- Fetches faces for selected photo
	- Renders image with scaled bounding boxes

- `services/api_service.dart`
	- `fetchPhotos(page)`
	- `uploadPhoto(bytes, filename)`
	- `fetchFaces(photoId)`

## Development Setup

### Prerequisites
- Python 3.10+
- PostgreSQL
- Flutter SDK

### Backend Setup

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

### Frontend Setup

```bash
cd frontend/facevault
flutter pub get
flutter run -d chrome
```

### Dev Utilities

### Reset all dev data

```bash
cd backend
python manage.py dev_reset
```

This command:
- deletes all `Face` and `Photo` records
- resets ID sequences (PostgreSQL with SQLite fallback logic)
- recreates `media/photos` and `media/faces`

### Manual clustering (current workflow)

```bash
cd backend
python manage.py shell
```

Then:

```python
from ml.cluster_faces import cluster_faces
cluster_faces()
```

## Configuration Notes

Current settings are development-oriented:
- `DEBUG = True`
- `CORS_ALLOW_ALL_ORIGINS = True`
- database credentials are hardcoded in settings
- frontend API URL is hardcoded to localhost

For production, move sensitive and environment-specific values to environment variables.

## Known Limitations

- Clustering is not automated or exposed via API.
- No People endpoints yet (grouped identities by `person_id`).
- No People UI in Flutter.
- No authentication/authorization.
- No delete/edit flows for photos or faces.
- Minimal automated tests (placeholder test files).
- Upload pipeline is synchronous (can become slow for heavy images/many faces).

## Roadmap (Recommended Next Steps)

### Phase 1: Operationalize Clustering
- Trigger clustering after upload or via scheduled/background job.
- Add management command and/or API endpoint for clustering runs.

### Phase 2: People APIs
- `GET /people/` -> list detected identities
- `GET /people/<person_id>/` -> photos/faces for one identity

### Phase 3: Flutter People Experience
- Add People grid screen
- Add Person detail screen (all photos containing that person)

### Phase 4: Product Hardening
- Auth (JWT/session)
- Better error handling/logging
- Config via env vars
- Security and CORS restrictions
- Optional async processing queue (Celery/Redis)

## Portfolio Summary

FaceVault demonstrates practical full-stack + ML integration:
- Computer vision pipeline integration in a web app backend
- Face representation learning with embeddings
- Unsupervised clustering for identity grouping
- API-first backend and Flutter frontend interaction

In short: a simplified Google Photos-style system with face detection and the foundation for person-level grouping.

