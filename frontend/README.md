# FaceVault frontend

The React single-page app for FaceVault: upload photos, browse them by day, open them full screen with the detected face boxes, and manage the people the backend has grouped.

## Stack

React 19, TypeScript, Vite, Tailwind CSS (light and dark mode), TanStack Query for server state, React Router, `react-dropzone` for uploads, `lucide-react` icons.

## Run it

```bash
npm install
cp .env.example .env     # optional: set the backend URL
npm run dev              # http://localhost:5173
```

The backend must be running (see the [main README](../README.md)); by default the app calls `http://127.0.0.1:8000`.

| Script | What it does |
|---|---|
| `npm run dev` | Vite dev server with hot reload |
| `npm run build` | Production build into `dist/` |
| `npm run typecheck` | `tsc --noEmit` |
| `npm run lint` | ESLint |
| `npm run preview` | Serve the production build locally |

## Configuration

| Variable | Default | Meaning |
|---|---|---|
| `VITE_API_BASE_URL` | `http://127.0.0.1:8000` | Where the Django API lives |
| `VITE_ENABLE_MOCKS` | `false` | `true` runs the UI on generated sample data without a backend (the sample photos are loaded from picsum.photos, so it needs internet access) |

## Structure

```text
src/
  pages/        Gallery, People, Person and Photo (full-screen viewer) routes
  components/   gallery/ (grid, cards, viewer, face overlay), people/, upload/, layout/, shared/, ui/
  hooks/        TanStack Query hooks: usePhotos, usePeople, useFaces
  services/     api.ts, the only module that talks to the backend
  theme/        light/dark mode provider
  utils/        grouping photos by day, date formatting
  types/        shared TypeScript types
```

## Notes

* The gallery groups photos by the day they were **taken** (EXIF capture date), falling back to the upload time. Capture times are camera wall-clock times, so the calendar day is read in UTC and does not shift with the viewer's time zone.
* Face boxes are drawn in the pixel space of the photo as displayed (EXIF orientation applied), which is the space the backend stores them in.
* HEIC photos are converted to JPEG by the backend on upload, so every browser can show them.
