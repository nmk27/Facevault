export type Photo = {
    id: string
    url: string
    thumbnailUrl: string
    title: string
    /** Upload time (true UTC). */
    createdAt: string
    /** Camera capture time from EXIF: wall-clock time labelled UTC, so read it with UTC getters. */
    takenAt?: string
    width?: number
    height?: number
}

export type FaceBox = {
    id: string
    x: number
    y: number
    width: number
    height: number
    confidence: number
    personId: string | null
}

export type Person = {
    id: string
    name: string
    faceCount: number
    averageConfidence: number
    coverUrl: string
    sampleImageUrls: string[]
}

export type Paginated<T> = {
    items: T[]
    nextPage: number | null
}
