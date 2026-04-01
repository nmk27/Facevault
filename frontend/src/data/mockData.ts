import type { FaceBox, Paginated, Person, Photo } from '../types'

export const MOCK_PHOTOS: Photo[] = Array.from({ length: 60 }).map((_, index) => {
    const id = String(index + 1)
    const picsumId = 100 + ((index * 7) % 80)
    return {
        id,
        url: `https://picsum.photos/id/${picsumId}/1400/900`,
        thumbnailUrl: `https://picsum.photos/id/${picsumId}/600/400`,
        title: `Photo ${id}`,
        createdAt: new Date(Date.now() - index * 86_400_000).toISOString(),
        width: 1400,
        height: 900,
    }
})

const PERSON_POOL = ['Alex', 'Jordan', 'Sam', 'Taylor', 'Casey', 'Riley']

export const MOCK_FACES_BY_PHOTO: Record<string, FaceBox[]> = Object.fromEntries(
    MOCK_PHOTOS.map((photo, index) => {
        const faces: FaceBox[] = Array.from({ length: (index % 3) + 1 }).map((_, faceIndex) => {
            const isUnknown = faceIndex === 0 && index % 4 === 0
            const person = PERSON_POOL[(index + faceIndex) % PERSON_POOL.length]
            return {
                id: `${photo.id}-${faceIndex}`,
                x: 0.1 + ((faceIndex * 0.23) % 0.5),
                y: 0.16 + ((faceIndex * 0.17) % 0.45),
                width: 0.18,
                height: 0.26,
                confidence: 0.75 + ((index + faceIndex) % 20) / 100,
                personId: isUnknown ? null : person.toLowerCase(),
            }
        })
        return [photo.id, faces]
    }),
)

export const MOCK_PEOPLE: Person[] = PERSON_POOL.map((name, index) => {
    const id = name.toLowerCase()
    const personPhotos = MOCK_PHOTOS.filter((photo) =>
        (MOCK_FACES_BY_PHOTO[photo.id] ?? []).some((face) => face.personId === id),
    )

    return {
        id,
        name,
        faceCount: personPhotos.length * 2,
        averageConfidence: 0.87 - index * 0.03,
        coverUrl: personPhotos[0]?.thumbnailUrl ?? 'https://picsum.photos/600/400',
        sampleImageUrls: personPhotos.slice(0, 4).map((photo) => photo.thumbnailUrl),
    }
})

export function getMockPaged<T>(items: T[], page: number, pageSize: number): Paginated<T> {
    const start = (page - 1) * pageSize
    const pageItems = items.slice(start, start + pageSize)
    const nextPage = start + pageSize < items.length ? page + 1 : null
    return { items: pageItems, nextPage }
}
