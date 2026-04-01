import { MOCK_FACES_BY_PHOTO, MOCK_PEOPLE, MOCK_PHOTOS, getMockPaged } from '../data/mockData'
import type { FaceBox, Paginated, Person, Photo } from '../types'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL?.trim() || 'http://127.0.0.1:8000'
const ENABLE_MOCKS = import.meta.env.VITE_ENABLE_MOCKS === 'true'
const PAGE_SIZE = 24

function useMocks() {
    return ENABLE_MOCKS
}

type BackendPhoto = {
    id: number
    image: string
    thumbnail: string | null
    width: number | null
    height: number | null
    uploaded_at: string
}

type BackendFace = {
    id: number
    x: number
    y: number
    width: number
    height: number
    confidence: number
    person_id: number | null
    created_at?: string
    photo_id?: number
    photo?: {
        id: number
        image: string | null
        thumbnail: string | null
    }
    face_image?: string | null
}

type BackendPersonSummary = {
    person_id: number
    face_count: number
}

function toAbsoluteMediaUrl(url: string | null | undefined): string {
    if (!url) {
        return ''
    }

    if (url.startsWith('http://') || url.startsWith('https://')) {
        return url
    }

    const base = API_BASE_URL.replace(/\/$/, '')
    const normalizedPath = url.startsWith('/') ? url : `/${url}`
    return `${base}${normalizedPath}`
}

function mapBackendPhoto(photo: BackendPhoto): Photo {
    return {
        id: String(photo.id),
        url: toAbsoluteMediaUrl(photo.image),
        thumbnailUrl: toAbsoluteMediaUrl(photo.thumbnail ?? photo.image),
        title: `Photo ${photo.id}`,
        createdAt: photo.uploaded_at,
        width: photo.width ?? undefined,
        height: photo.height ?? undefined,
    }
}

function mapBackendFace(face: BackendFace): FaceBox {
    return {
        id: String(face.id),
        x: face.x,
        y: face.y,
        width: face.width,
        height: face.height,
        confidence: face.confidence,
        personId: face.person_id === null ? null : String(face.person_id),
    }
}

async function requestJson<T>(path: string): Promise<T> {
    const response = await fetch(`${API_BASE_URL}${path}`)
    if (!response.ok) {
        throw new Error(`Request failed: ${response.status}`)
    }
    return response.json() as Promise<T>
}

export async function getPhotos(page = 1, pageSize = PAGE_SIZE): Promise<Paginated<Photo>> {
    if (useMocks()) {
        return getMockPaged(MOCK_PHOTOS, page, pageSize)
    }

    try {
        const result = await requestJson<
            { count?: number; results?: BackendPhoto[]; next?: string | null } | BackendPhoto[]
        >(`/photos/?page=${page}`)

        if (Array.isArray(result)) {
            const start = (page - 1) * pageSize
            const items = result.slice(start, start + pageSize).map(mapBackendPhoto)
            return {
                items,
                nextPage: start + pageSize < result.length ? page + 1 : null,
            }
        }

        const pageItems = (result.results ?? []).map(mapBackendPhoto)
        const count = typeof result.count === 'number' ? result.count : undefined
        const inferredNext =
            typeof result.next === 'string'
                ? page + 1
                : typeof count === 'number'
                    ? page * pageItems.length < count
                        ? page + 1
                        : null
                    : pageItems.length >= pageSize
                        ? page + 1
                        : null

        return {
            items: pageItems,
            nextPage: inferredNext,
        }
    } catch {
        if (page > 1) {
            return {
                items: [],
                nextPage: null,
            }
        }

        if (useMocks()) {
            return getMockPaged(MOCK_PHOTOS, page, pageSize)
        }
        throw new Error('Failed to fetch photos from backend')
    }
}

export async function getPhotoById(photoId: string): Promise<Photo | null> {
    if (useMocks()) {
        return MOCK_PHOTOS.find((photo) => photo.id === photoId) ?? null
    }

    try {
        let page = 1
        while (page <= 100) {
            const result = await requestJson<{ results: BackendPhoto[]; next: string | null }>(
                `/photos/?page=${page}`,
            )

            const found = result.results.find((photo) => String(photo.id) === photoId)
            if (found) {
                return mapBackendPhoto(found)
            }

            if (!result.next) {
                break
            }
            page += 1
        }

        return null
    } catch {
        if (useMocks()) {
            return MOCK_PHOTOS.find((photo) => photo.id === photoId) ?? null
        }
        throw new Error('Failed to fetch photo from backend')
    }
}

export async function uploadPhotos(
    files: readonly File[],
    onProgress: (progress: number) => void,
): Promise<{ uploaded: number }> {
    if (useMocks()) {
        for (let i = 1; i <= 5; i += 1) {
            await new Promise((resolve) => setTimeout(resolve, 120))
            onProgress(i * 20)
        }
        return { uploaded: files.length }
    }

    let uploaded = 0

    for (let index = 0; index < files.length; index += 1) {
        const file = files[index]
        const form = new FormData()
        form.append('image', file)

        await new Promise<void>((resolve, reject) => {
            const xhr = new XMLHttpRequest()
            xhr.open('POST', `${API_BASE_URL}/photos/upload/`)

            xhr.upload.onprogress = (event) => {
                if (!event.lengthComputable) {
                    return
                }

                const fileProgress = event.loaded / event.total
                const totalProgress = ((index + fileProgress) / files.length) * 100
                onProgress(Math.round(totalProgress))
            }

            xhr.onload = () => {
                if (xhr.status >= 200 && xhr.status < 300) {
                    uploaded += 1
                    resolve()
                } else {
                    reject(new Error('Upload failed'))
                }
            }

            xhr.onerror = () => reject(new Error('Upload failed'))
            xhr.send(form)
        })
    }

    onProgress(100)
    return { uploaded }
}

export async function getFaces(photoId: string): Promise<FaceBox[]> {
    if (useMocks()) {
        return MOCK_FACES_BY_PHOTO[photoId] ?? []
    }

    try {
        const result = await requestJson<BackendFace[]>(`/faces/${photoId}/`)
        return result.map(mapBackendFace)
    } catch {
        if (useMocks()) {
            return MOCK_FACES_BY_PHOTO[photoId] ?? []
        }
        throw new Error('Failed to fetch faces from backend')
    }
}

export async function getPeople(page = 1, pageSize = 20): Promise<Paginated<Person>> {
    if (useMocks()) {
        return getMockPaged(MOCK_PEOPLE, page, pageSize)
    }

    try {
        const result = await requestJson<BackendPersonSummary[]>(`/faces/people/`)
        const sorted = [...result].sort((a, b) => b.face_count - a.face_count)
        const start = (page - 1) * pageSize
        const pageItems = sorted.slice(start, start + pageSize)

        const enrichedItems = await Promise.all(
            pageItems.map(async (person) => {
                try {
                    const faces = await requestJson<BackendFace[]>(`/faces/people/${person.person_id}/`)
                    const coverFromFace = toAbsoluteMediaUrl(faces[0]?.face_image)
                    const coverFromPhoto = toAbsoluteMediaUrl(
                        faces[0]?.photo?.thumbnail ?? faces[0]?.photo?.image ?? null,
                    )

                    const sampleImageUrls = faces
                        .slice(0, 4)
                        .map((face) =>
                            toAbsoluteMediaUrl(face.photo?.thumbnail ?? face.photo?.image ?? null),
                        )
                        .filter((url) => Boolean(url))

                    const averageConfidence =
                        faces.length > 0
                            ? faces.reduce((sum, face) => sum + (face.confidence ?? 0), 0) / faces.length
                            : 0

                    return {
                        id: String(person.person_id),
                        name: `Person ${person.person_id}`,
                        faceCount: person.face_count,
                        averageConfidence,
                        coverUrl: coverFromFace || coverFromPhoto,
                        sampleImageUrls,
                    }
                } catch {
                    return {
                        id: String(person.person_id),
                        name: `Person ${person.person_id}`,
                        faceCount: person.face_count,
                        averageConfidence: 0,
                        coverUrl: '',
                        sampleImageUrls: [],
                    }
                }
            }),
        )

        return {
            items: enrichedItems,
            nextPage: start + pageSize < sorted.length ? page + 1 : null,
        }
    } catch {
        if (useMocks()) {
            return getMockPaged(MOCK_PEOPLE, page, pageSize)
        }
        throw new Error('Failed to fetch people from backend')
    }
}

export async function getPerson(personId: string): Promise<{ person: Person; photos: Photo[] }> {
    if (useMocks()) {
        const person = MOCK_PEOPLE.find((item) => item.id === personId)
        const photos = MOCK_PHOTOS.filter((photo) =>
            (MOCK_FACES_BY_PHOTO[photo.id] ?? []).some((face) => face.personId === personId),
        )

        if (!person) {
            throw new Error('Person not found')
        }

        return { person, photos }
    }

    const faces = await requestJson<BackendFace[]>(`/faces/people/${personId}/`)

    const photoMap = new Map<string, Photo>()
    let confidenceTotal = 0
    let confidenceCount = 0

    faces.forEach((face) => {
        if (typeof face.confidence === 'number') {
            confidenceTotal += face.confidence
            confidenceCount += 1
        }

        const backendPhoto = face.photo
        if (!backendPhoto) {
            return
        }

        const mapped: Photo = {
            id: String(backendPhoto.id),
            url: toAbsoluteMediaUrl(backendPhoto.image),
            thumbnailUrl: toAbsoluteMediaUrl(backendPhoto.thumbnail ?? backendPhoto.image),
            title: `Photo ${backendPhoto.id}`,
            createdAt: face.created_at ?? '',
        }

        const existing = photoMap.get(mapped.id)
        if (!existing || (!existing.createdAt && mapped.createdAt)) {
            photoMap.set(mapped.id, mapped)
        }
    })

    const person: Person = {
        id: String(personId),
        name: `Person ${personId}`,
        faceCount: faces.length,
        averageConfidence: confidenceCount ? confidenceTotal / confidenceCount : 0,
        coverUrl: photoMap.values().next().value?.thumbnailUrl ?? '',
        sampleImageUrls: Array.from(photoMap.values())
            .slice(0, 4)
            .map((photo) => photo.thumbnailUrl),
    }

    return {
        person,
        photos: Array.from(photoMap.values()),
    }
}
