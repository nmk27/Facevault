# FaceVault Frontend (Flutter)

This Flutter app is the UI layer for FaceVault. It currently supports uploading photos, browsing a paginated gallery, and viewing detected face boxes on each photo.

## Quick Context (For New Chat Sessions)

- App role: client for FaceVault backend APIs.
- Current user flow: upload photo -> backend detects faces -> open photo -> see red face boxes.
- Implemented screens: gallery and photo detail.
- Main gap: no People screen (grouped identities) yet.
- API base URL is currently hardcoded to `http://127.0.0.1:8000` in `lib/services/api_service.dart`.

## Current Features

- Infinite-scroll gallery (paginated backend fetch).
- Photo upload via file picker.
- Thumbnail grid rendering.
- Photo detail view with face-box overlay.
- Basic loading, empty-state, and retry error handling.

## App Structure

```text
lib/
|- main.dart
|- models/
|  |- photo.dart
|  |- face.dart
|- services/
|  |- api_service.dart
|- screens/
	 |- gallery_screen.dart
	 |- photo_view_screen.dart
```

## Screen Details

### GalleryScreen
- File: `lib/screens/gallery_screen.dart`
- Loads photos from `/photos/?page=<n>`.
- Uses `ScrollController` to auto-load next page near bottom.
- Upload FAB opens file picker and posts to `/photos/upload/`.
- On successful upload, gallery resets and reloads page 1.

### PhotoViewScreen
- File: `lib/screens/photo_view_screen.dart`
- Fetches faces from `/faces/<photo_id>/`.
- Loads natural image size via `NetworkImage` stream listener.
- Scales image to fit viewport and overlays face rectangles.

## API Contract Expected By Frontend

### GET /photos/?page=1
Expected shape (DRF pagination):

```json
{
	"count": 10,
	"next": "http://127.0.0.1:8000/photos/?page=2",
	"previous": null,
	"results": [
		{
			"id": 1,
			"image": "http://127.0.0.1:8000/media/photos/a.jpg",
			"thumbnail": "http://127.0.0.1:8000/media/photos/thumb_a.jpg",
			"width": 1920,
			"height": 1080,
			"uploaded_at": "2026-03-24T08:00:00Z"
		}
	]
}
```

### POST /photos/upload/
- Multipart form field: `image`.
- Success status: `201`.

### GET /faces/<photo_id>/
Expected list shape:

```json
[
	{"x": 120, "y": 80, "width": 160, "height": 160, "confidence": 0.99}
]
```

## Setup

### Prerequisites
- Flutter SDK (Dart SDK compatible with `sdk: ^3.11.1`)
- Running backend server at `http://127.0.0.1:8000`

### Install

```bash
cd frontend/facevault
flutter pub get
```

### Run

```bash
flutter run -d chrome
```

Optional:

```bash
flutter run -d windows
```

## Main Dependencies

- `http`: REST API calls
- `file_picker`: selecting upload files
- `mime`: MIME utilities for uploads

## Current Limitations

- No auth flow.
- API URL is hardcoded.
- No People/identity grouping UI.
- No delete/edit actions for photos.
- Minimal widget tests (default scaffold only).

## Frontend Roadmap

### Phase 1
- Extract API base URL to environment/config.
- Improve upload error surface and user feedback.

### Phase 2
- Add People screen (cluster/person list).
- Add Person detail screen (photos containing selected person).

### Phase 3
- Add richer gallery controls (filters/sort).
- Add photo actions (delete/select/batch).

## Notes For Contributors

- Keep backend API contracts backward compatible where possible.
- If API changes are required, update:
	- `lib/services/api_service.dart`
	- model parsing in `lib/models/`
	- this README contract section
