import { MOCK_FACES_BY_PHOTO, MOCK_PEOPLE, MOCK_PHOTOS, getMockPaged } from '../data/mockData'
import type { FaceBox, Paginated, Person, Photo } from '../types'
import { photoTime } from '../utils'

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
    taken_at: string | null
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
        taken_at?: string | null
        uploaded_at?: string
    }
    face_image?: string | null
}

type BackendPersonSummary = {
    id: number
    name: string
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
        takenAt: photo.taken_at ?? undefined,
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

    const response = await fetch(`${API_BASE_URL}/photos/${encodeURIComponent(photoId)}/`)
    if (response.status === 404) {
        return null
    }
    if (!response.ok) {
        throw new Error('Failed to fetch photo from backend')
    }
    return mapBackendPhoto((await response.json()) as BackendPhoto)
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
                    const detail = await requestJson<{ faces: BackendFace[] }>(`/faces/people/${person.id}/`)
                    const faces = detail.faces
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
                        id: String(person.id),
                        name: person.name,
                        faceCount: person.face_count,
                        averageConfidence,
                        coverUrl: coverFromFace || coverFromPhoto,
                        sampleImageUrls,
                    }
                } catch {
                    return {
                        id: String(person.id),
                        name: person.name,
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

    const detail = await requestJson<{ person: BackendPersonSummary; faces: BackendFace[] }>(
        `/faces/people/${personId}/`,
    )

    const photoMap = new Map<string, Photo>()
    let confidenceTotal = 0
    let confidenceCount = 0

    detail.faces.forEach((face) => {
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
            createdAt: backendPhoto.uploaded_at ?? face.created_at ?? '',
            takenAt: backendPhoto.taken_at ?? undefined,
        }

        const existing = photoMap.get(mapped.id)
        if (!existing || (!existing.createdAt && mapped.createdAt)) {
            photoMap.set(mapped.id, mapped)
        }
    })

    const photosInApiOrder = Array.from(photoMap.values())

    const person: Person = {
        id: String(detail.person.id),
        name: detail.person.name,
        faceCount: detail.person.face_count,
        averageConfidence: confidenceCount ? confidenceTotal / confidenceCount : 0,
        coverUrl: photosInApiOrder[0]?.thumbnailUrl ?? '',
        sampleImageUrls: photosInApiOrder.slice(0, 4).map((photo) => photo.thumbnailUrl),
    }

    // The API lists faces in id order; show the person's photos newest first like the gallery.
    const photos = [...photosInApiOrder].sort((a, b) => photoTime(b) - photoTime(a))

    return { person, photos }
}

export async function renamePerson(personId: string, name: string): Promise<Person> {
    if (useMocks()) {
        return { id: personId, name, faceCount: 0, averageConfidence: 0, coverUrl: '', sampleImageUrls: [] }
    }

    const response = await fetch(`${API_BASE_URL}/faces/people/${personId}/`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name }),
    })

    if (!response.ok) {
        throw new Error(`Failed to rename person: ${response.status}`)
    }

    const summary = (await response.json()) as BackendPersonSummary
    return {
        id: String(summary.id),
        name: summary.name,
        faceCount: summary.face_count,
        averageConfidence: 0,
        coverUrl: '',
        sampleImageUrls: [],
    }
}
