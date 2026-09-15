# FaceVault

FaceVault is a full-stack photo app inspired by Google Photos / Apple Photos: upload images, automatically detect faces, generate embeddings, group faces into people, and browse everything in a gallery and a People section.

## Stack

- **Frontend**: React 19 + Vite + TypeScript + Tailwind CSS (`frontend/`), with light/dark mode and an Apple-Photos-style UI.
- **Backend**: Django + Django REST Framework (`backend/`), PostgreSQL.
- **ML pipeline**: MTCNN for face detection, FaceNet (`InceptionResnetV1`, `vggface2`) for 512-dim embeddings, DBSCAN for clustering.

The original prototype used a Flutter frontend; it was fully replaced by the React app (`frontend/`) — see git history for the migration.

## What works today

- Upload photos (drag-and-drop or file picker), with HEIC/HEIF support.
- Automatic face detection, cropping, and embedding generation on upload.
- **Stable person identity**: faces are matched against existing people by embedding similarity before falling back to clustering, so a person's identity (and name) survives new uploads instead of being recomputed from scratch every time.
- People can be renamed (`PATCH /faces/people/<id>/`), and the gallery/person pages reflect the name everywhere.
- Gallery grouped by day, with a full-screen photo viewer (keyboard arrow navigation, face bounding-box overlay).
- People grid with circular avatar cards and a per-person photo timeline.

## Project structure

```text
FaceVault/
|- backend/
|  |- facevault/     # Django settings, URLs
|  |- photos/        # Photo model, upload/list API
|  |- faces/         # Face + Person models, people API
|  |- ml/            # Detection, embeddings, clustering
|  |- users/         # Custom dev management command(s)
|  |- manage.py
|  |- requirements.txt
|  |- .env.example
|- frontend/
|  |- src/
|  |  |- components/ # gallery/, people/, layout/, upload/, shared/, ui/
|  |  |- pages/
|  |  |- hooks/
|  |  |- services/    # api.ts - backend client
|  |  |- theme/       # dark mode provider
|  |- package.json
|- README.md
```

## Data model

### Photo (`backend/photos/models.py`)
`id`, `image`, `thumbnail` (auto-generated, EXIF-corrected), `width`, `height`, `uploaded_at`.

### Face (`backend/faces/models.py`)
`id`, `photo` (FK), `x`/`y`/`width`/`height` (bounding box), `confidence`, `face_image` (crop), `embedding` (512-dim JSON vector), `person` (FK to `Person`, nullable — null means not yet clustered with anyone).

### Person (`backend/faces/models.py`)
`id`, `name` (blank until renamed, falls back to `"Person {id}"` in API responses), `created_at`, `updated_at`. Created automatically by clustering; never recreated once it exists, so a name sticks across future uploads.

## API reference

Base URL for the frontend is `VITE_API_BASE_URL` (defaults to `http://127.0.0.1:8000`).

- `GET /photos/` — paginated photo list, newest first.
- `POST /photos/upload/` — multipart upload (field `image`); runs detection, embedding, and clustering synchronously; validates content-type and a 10MB size limit server-side.
- `GET /faces/<photo_id>/` — faces detected in one photo.
- `GET /faces/people/` — list of people with face counts and names.
- `GET /faces/people/<id>/` — `{ person: {id, name, face_count}, faces: [...] }` for one person.
- `PATCH /faces/people/<id>/` — body `{"name": "..."}`, renames a person.

## Clustering

`backend/ml/cluster_faces.py::cluster_faces()` runs after every upload:

1. Faces without a `person` are compared (cosine similarity on L2-normalized embeddings) against the centroid of each existing person; a good match attaches the face to that person.
2. Anything left over is clustered among itself with DBSCAN (`FACE_CLUSTER_EPS`, `FACE_CLUSTER_MIN_SAMPLES`); a resulting cluster of size >= `min_samples` becomes a brand-new `Person`. Leftover singletons stay unassigned (`person=None`), same as DBSCAN's "noise" label before.

This means existing people (and their names) are never recomputed away — only genuinely new faces get evaluated.

## Development setup

### Prerequisites
- Python 3.10+, PostgreSQL, Node.js 20+

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # .venv\Scripts\activate on Windows
pip install -r requirements.txt
cp .env.example .env       # adjust DB credentials etc.
python manage.py migrate
python manage.py runserver
```

### Frontend

```bash
cd frontend
cp .env.example .env       # optional: VITE_API_BASE_URL, VITE_ENABLE_MOCKS
npm install
npm run dev
```

Set `VITE_ENABLE_MOCKS=true` to run the UI against generated mock data without a backend.

### Dev utilities

```bash
cd backend
python manage.py dev_reset   # wipes Face/Photo records and media/, resets sequences
```

## Configuration

Backend settings (`backend/facevault/settings.py`) read from environment variables (see `backend/.env.example`): `DJANGO_SECRET_KEY`, `DJANGO_DEBUG`, `DJANGO_ALLOWED_HOSTS`, `DB_*`, `CORS_ALLOWED_ORIGINS` / `CORS_ALLOW_ALL_ORIGINS`, `FACE_CLUSTER_EPS`, `FACE_CLUSTER_MIN_SAMPLES`. Sensible local-dev defaults are baked in, so the app still runs without a `.env` file.

## Known limitations

- No authentication/authorization layer.
- No delete/edit flows for photos or faces.
- Upload pipeline is synchronous (detection + embeddings run inline; can be slow for large images or many faces).
- Minimal automated tests.

## Roadmap ideas

- Background job queue (Celery/Redis) for the upload pipeline instead of synchronous processing.
- Auth (session or JWT).
- Delete/merge people, delete photos.

## JavaScript migration reference

`JAVASCRIPT_MIGRATION_PROMPT.md` was written as a spec for migrating the original Flutter app to a JS stack. That migration is complete (this README describes the resulting app); the file is kept only as historical/architectural reference.
