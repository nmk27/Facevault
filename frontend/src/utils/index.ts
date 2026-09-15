import type { Photo } from '../types'

export type PhotoSection = {
    key: string
    label: string
    photos: Photo[]
}

function sectionLabel(date: Date): string {
    const now = new Date()
    const isSameDay =
        date.getFullYear() === now.getFullYear() && date.getMonth() === now.getMonth() && date.getDate() === now.getDate()

    const yesterday = new Date(now)
    yesterday.setDate(now.getDate() - 1)
    const isYesterday =
        date.getFullYear() === yesterday.getFullYear() &&
        date.getMonth() === yesterday.getMonth() &&
        date.getDate() === yesterday.getDate()

    if (isSameDay) return 'Today'
    if (isYesterday) return 'Yesterday'

    const sameYear = date.getFullYear() === now.getFullYear()
    return date.toLocaleDateString(undefined, {
        month: 'long',
        day: 'numeric',
        year: sameYear ? undefined : 'numeric',
    })
}

export function groupPhotosByDay(photos: Photo[]): PhotoSection[] {
    const sections: PhotoSection[] = []
    const indexByKey = new Map<string, number>()

    for (const photo of photos) {
        const date = photo.createdAt ? new Date(photo.createdAt) : null
        const key = date && !Number.isNaN(date.getTime()) ? date.toDateString() : 'unknown'

        let index = indexByKey.get(key)
        if (index === undefined) {
            index = sections.length
            indexByKey.set(key, index)
            sections.push({
                key,
                label: date && !Number.isNaN(date.getTime()) ? sectionLabel(date) : 'Unknown date',
                photos: [],
            })
        }

        sections[index].photos.push(photo)
    }

    return sections
}
