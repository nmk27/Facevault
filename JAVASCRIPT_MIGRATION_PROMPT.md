# FaceVault JavaScript Migration Prompt

## Application Overview
FaceVault is a full-stack photo application inspired by Google Photos workflows. It allows users to upload images, automatically detects faces using ML models, generates embeddings, performs person clustering/grouping, and provides a comprehensive UI for browsing photos and identified people.

## Core Functionality Summary

### User Journey
1. User uploads photos through web interface
2. Backend automatically detects faces in uploaded photos using MTCNN
3. System generates 512-dimensional embeddings for each detected face using FaceNet
4. DBSCAN clustering algorithm groups faces by similarity into person identities
5. User can browse photos in gallery view with face overlays
6. User can view "People" section showing grouped identities
7. User can click on a person to see all photos containing that person
8. Dark/light theme support throughout the application

### Technology Architecture

**Original Flutter Frontend:**
- Material 3 design with theming support
- Bottom navigation: Gallery, People, Settings
- Infinite scroll gallery with photo thumbnails
- Photo detail view with face bounding box overlays
- People grid showing identified persons
- Person detail showing all photos containing a specific person
- File upload with progress indication

**Original Django Backend:**
- RESTful API with Django REST Framework
- PostgreSQL database
- Face detection: MTCNN (Multi-task CNN)
- Embeddings: FaceNet with InceptionResnetV1 (pretrained on vggface2)
- Clustering: DBSCAN with cosine distance metric on L2-normalized embeddings
- Automatic thumbnail generation with EXIF orientation correction
- HEIC/HEIF image format support

## Database Schema

### Photos Table
```sql
CREATE TABLE photos (
    id SERIAL PRIMARY KEY,
    image VARCHAR(255) NOT NULL,           -- Original uploaded image path
    thumbnail VARCHAR(255),                -- Auto-generated thumbnail path
    uploaded_at TIMESTAMP DEFAULT NOW(),
    width INTEGER,                         -- Image dimensions
    height INTEGER
);
```

### Faces Table
```sql
CREATE TABLE faces (
    id SERIAL PRIMARY KEY,
    photo_id INTEGER REFERENCES photos(id) ON DELETE CASCADE,
    x INTEGER NOT NULL,                    -- Bounding box coordinates
    y INTEGER NOT NULL,
    width INTEGER NOT NULL,
    height INTEGER NOT NULL,
    confidence FLOAT NOT NULL,             -- Detection confidence (0-1)
    face_image VARCHAR(255),               -- Cropped face image path
    embedding JSON,                        -- 512-dim embedding vector as JSON array
    person_id INTEGER,                     -- Cluster label (-1 for noise/unidentified)
    created_at TIMESTAMP DEFAULT NOW()
);
```

## API Endpoints Required

### Photo Management
- `GET /api/photos/` - Paginated list of photos (newest first)
  - Response: `{count, next, previous, results: [{id, image, thumbnail, width, height, uploaded_at}]}`
- `POST /api/photos/upload/` - Upload new photo with multipart form data
  - Field: `image` (file)
  - Triggers: save photo, detect faces, generate embeddings, auto-cluster, save faces
  - Response: `201 Created` with photo object

### Face Management
- `GET /api/faces/:photo_id/` - Get all faces detected in specific photo
  - Response: `[{id, x, y, width, height, confidence, person_id}]`

### People/Identity Management
- `GET /api/people/` - List all identified people with face counts
  - Response: `[{person_id, face_count}]` (excludes noise faces where person_id = -1)
- `GET /api/people/:person_id/` - Get all faces for specific person
  - Response: `[{id, person_id, x, y, width, height, confidence, embedding, photo: {id, image, thumbnail}, face_image, created_at}]`

## ML Pipeline Implementation

### Face Detection
Use **face-api.js** or **MediaPipe Face Detection** in JavaScript:
```javascript
// Using face-api.js example
const detections = await faceapi.detectAllFaces(image)
    .withFaceLandmarks()
    .withFaceDescriptors();

// Filter by confidence threshold (>=0.95)
const validFaces = detections.filter(d => d.detection.score >= 0.95);
```

### Embedding Generation
Use **face-api.js** FaceNet model or implement with **TensorFlow.js**:
```javascript
// Face descriptors are 128-dim with face-api.js (vs 512-dim FaceNet)
// Alternative: Use TensorFlow.js with pre-trained FaceNet model
const descriptor = detection.descriptor; // 128 or 512 dimensional vector
```

### Clustering Algorithm
Implement DBSCAN clustering in JavaScript:
```javascript
// Configuration (make environment configurable)
const CLUSTER_EPS = parseFloat(process.env.FACE_CLUSTER_EPS || '0.4');
const MIN_SAMPLES = parseInt(process.env.FACE_CLUSTER_MIN_SAMPLES || '2');

function dbscanClustering(embeddings, eps = CLUSTER_EPS, minSamples = MIN_SAMPLES) {
    // Implement DBSCAN with cosine distance metric
    // Return cluster labels (-1 for noise points)
}

function cosineSimilarity(a, b) {
    // Compute cosine similarity between normalized embedding vectors
}
```

## JavaScript Technology Stack Recommendation

### Backend Framework Options
1. **Node.js + Express + Prisma ORM**
2. **Node.js + Fastify + Prisma ORM**
3. **Next.js API Routes + Prisma** (full-stack option)

### Frontend Framework Options
1. **React + Vite** (recommended for performance)
2. **Next.js** (full-stack with API routes)
3. **Vue.js + Vite**

### Required JavaScript Libraries

#### Backend
```json
{
  "dependencies": {
    "@prisma/client": "^5.0.0",
    "express": "^4.18.0",
    "multer": "^1.4.5",
    "cors": "^2.8.5",
    "dotenv": "^16.0.0",
    "sharp": "^0.32.0",
    "@tensorflow/tfjs-node": "^4.0.0",
    "face-api.js": "^0.22.2",
    "ml-matrix": "^6.10.0",
    "ml-dbscan": "^1.0.0"
  }
}
```

#### Frontend
```json
{
  "dependencies": {
    "react": "^18.2.0",
    "react-router-dom": "^6.8.0",
    "@tanstack/react-query": "^4.28.0",
    "@headlessui/react": "^1.7.0",
    "@heroicons/react": "^2.0.0",
    "tailwindcss": "^3.3.0",
    "framer-motion": "^10.0.0",
    "react-dropzone": "^14.2.0",
    "react-infinite-scroll-component": "^6.1.0"
  }
}
```

## Photo Processing Pipeline

### Upload Handler Example (Node.js/Express)
```javascript
const multer = require('multer');
const sharp = require('sharp');
const path = require('path');

const upload = multer({
    storage: multer.memoryStorage(),
    limits: { fileSize: 10 * 1024 * 1024 }, // 10MB limit
});

app.post('/api/photos/upload', upload.single('image'), async (req, res) => {
    try {
        // 1. Save original image
        const photo = await savePhoto(req.file);

        // 2. Generate thumbnail with EXIF handling
        await generateThumbnail(photo);

        // 3. Detect faces
        const detections = await detectFaces(photo.imagePath);

        // 4. Process each face: crop, generate embedding, save
        const faces = await Promise.all(
            detections.map(detection => processFace(detection, photo))
        );

        // 5. Run clustering on all existing face embeddings
        await runClustering();

        res.status(201).json(photo);
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});
```

### Image Processing with Sharp
```javascript
async function generateThumbnail(photo) {
    const thumbnailPath = path.join('uploads/thumbnails', `thumb_${photo.filename}`);

    await sharp(photo.imagePath)
        .rotate() // Auto-rotate based on EXIF
        .resize(300, 300, {
            fit: 'inside',
            withoutEnlargement: true
        })
        .jpeg({ quality: 85 })
        .toFile(thumbnailPath);

    // Update photo record with thumbnail path
    await updatePhoto(photo.id, { thumbnail: thumbnailPath });
}
```

## Frontend Component Architecture

### App Structure (React)
```
src/
├── components/
│   ├── ui/                    # Reusable UI components
│   ├── PhotoGrid.jsx          # Gallery grid with infinite scroll
│   ├── PhotoViewer.jsx        # Photo detail with face overlays
│   ├── PeopleGrid.jsx         # People/identity grid
│   ├── PersonDetail.jsx       # Person's photos view
│   ├── UploadButton.jsx       # File upload with progress
│   └── Navigation.jsx         # Bottom/sidebar navigation
├── hooks/
│   ├── usePhotos.js           # Photos data fetching
│   ├── usePeople.js           # People data fetching
│   └── useTheme.js            # Dark/light theme
├── services/
│   └── api.js                 # API client functions
├── pages/
│   ├── Gallery.jsx
│   ├── People.jsx
│   ├── Settings.jsx
│   └── PhotoDetail.jsx
└── App.jsx
```

### Key Component Examples

#### Photo Grid with Infinite Scroll
```javascript
function PhotoGrid() {
    const {
        data: photos = [],
        fetchNextPage,
        hasNextPage,
        isLoading
    } = useInfiniteQuery(['photos'], fetchPhotos);

    return (
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-2 p-4">
            {photos.map((photo) => (
                <PhotoThumbnail
                    key={photo.id}
                    photo={photo}
                    onClick={() => navigate(`/photos/${photo.id}`)}
                />
            ))}
            {hasNextPage && (
                <div ref={loadMoreRef}>Loading...</div>
            )}
        </div>
    );
}
```

#### Photo Viewer with Face Overlays
```javascript
function PhotoViewer({ photoId }) {
    const { data: photo } = useQuery(['photos', photoId], () => fetchPhoto(photoId));
    const { data: faces = [] } = useQuery(['faces', photoId], () => fetchFaces(photoId));

    return (
        <div className="relative">
            <img
                src={photo?.image}
                alt="Photo"
                onLoad={handleImageLoad}
                className="max-w-full max-h-screen object-contain"
            />
            {faces.map((face) => (
                <div
                    key={face.id}
                    className="absolute border-2 border-red-500 bg-red-500/20"
                    style={{
                        left: `${(face.x / imageWidth) * 100}%`,
                        top: `${(face.y / imageHeight) * 100}%`,
                        width: `${(face.width / imageWidth) * 100}%`,
                        height: `${(face.height / imageHeight) * 100}%`,
                    }}
                />
            ))}
        </div>
    );
}
```

## Configuration & Environment Variables

### Backend Environment (.env)
```env
# Database
DATABASE_URL="postgresql://username:password@localhost:5432/facevault"

# File Storage
UPLOAD_DIR="/uploads"
MAX_FILE_SIZE=10485760

# ML/CV Settings
FACE_CONFIDENCE_THRESHOLD=0.95
FACE_CLUSTER_EPS=0.4
FACE_CLUSTER_MIN_SAMPLES=2

# API
PORT=3001
CORS_ORIGIN="http://localhost:3000"

# Image Processing
THUMBNAIL_SIZE=300
FACE_CROP_SIZE=160
```

### Frontend Environment (.env)
```env
VITE_API_BASE_URL="http://localhost:3001/api"
VITE_MAX_UPLOAD_SIZE=10485760
```

## Performance Considerations

### Backend Optimizations
- Use streaming for large file uploads
- Implement background job queue for ML processing (Bull/Agenda)
- Cache embeddings and avoid recomputing
- Optimize database queries with proper indexing
- Consider using Redis for session/caching

### Frontend Optimizations
- Implement virtual scrolling for large photo grids
- Lazy load images with intersection observer
- Use React.memo for expensive photo components
- Implement service worker for offline caching
- Optimize bundle size with code splitting

## Security Considerations

### File Upload Security
```javascript
const allowedMimeTypes = ['image/jpeg', 'image/png', 'image/webp', 'image/heic'];
const maxFileSize = 10 * 1024 * 1024; // 10MB

function validateUpload(file) {
    if (!allowedMimeTypes.includes(file.mimetype)) {
        throw new Error('Invalid file type');
    }
    if (file.size > maxFileSize) {
        throw new Error('File too large');
    }
}
```

### API Security
- Implement rate limiting
- Validate and sanitize all inputs
- Use CORS properly
- Implement file paths validation to prevent directory traversal
- Consider authentication/authorization for production

## Migration Steps

### Phase 1: Backend Setup
1. Initialize Node.js project with chosen framework
2. Set up PostgreSQL database with Prisma schema
3. Implement photo upload and storage endpoints
4. Add face detection using face-api.js or MediaPipe
5. Implement embedding generation and clustering
6. Create all required API endpoints

### Phase 2: Frontend Setup
1. Initialize React/Vue project with chosen framework
2. Set up routing and navigation structure
3. Implement photo gallery with infinite scroll
4. Create photo detail view with face overlays
5. Build people/identity management screens
6. Add theme support and responsive design

### Phase 3: Integration & Testing
1. Connect frontend to backend APIs
2. Test complete upload-to-clustering pipeline
3. Implement error handling and loading states
4. Add performance optimizations
5. Test clustering accuracy and adjust parameters

### Phase 4: Production Hardening
1. Add authentication/authorization
2. Implement proper error logging
3. Set up monitoring and health checks
4. Configure production deployment
5. Add backup and recovery procedures

## Testing Strategy

### Backend Testing
- Unit tests for ML pipeline functions
- Integration tests for API endpoints
- Performance tests for clustering algorithms
- Load tests for file uploads

### Frontend Testing
- Component unit tests with React Testing Library
- E2E tests with Playwright/Cypress
- Visual regression tests for UI components
- Performance tests for image loading

## Deployment Architecture

### Development
- Frontend: Vite dev server (localhost:3000)
- Backend: Node.js server (localhost:3001)
- Database: Local PostgreSQL
- File storage: Local filesystem

### Production Options
- Frontend: Vercel, Netlify, or static hosting
- Backend: Railway, Render, AWS/GCP/Azure
- Database: Managed PostgreSQL (Supabase, Railway, AWS RDS)
- File storage: AWS S3, Cloudinary, or similar
- CDN: CloudFront, CloudFlare for image optimization

This comprehensive prompt provides all the architectural details, implementation guidance, and technical specifications needed to recreate the FaceVault application in JavaScript while maintaining all core functionality and user experience.