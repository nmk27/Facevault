import type { Photo } from '../types'

export type PhotoSection = {
    key: string
    label: string
    photos: Photo[]
}

type CalendarDay = { year: number; month: number; day: number }

function localDay(date: Date): CalendarDay {
    return { year: date.getFullYear(), month: date.getMonth(), day: date.getDate() }
}

function isSameDay(a: CalendarDay, b: CalendarDay): boolean {
    return a.year === b.year && a.month === b.month && a.day === b.day
}

function parseDate(value: string | undefined): Date | null {
    if (!value) return null
    const date = new Date(value)
    return Number.isNaN(date.getTime()) ? null : date
}

// takenAt is camera wall-clock time labelled UTC, so its calendar day is read with UTC
// getters; local getters would shift a late-evening shot to the next day for some viewers.
// Upload times are real instants and use the viewer's local day.
function dayOf(photo: Photo): CalendarDay | null {
    const taken = parseDate(photo.takenAt)
    if (taken) {
        return { year: taken.getUTCFullYear(), month: taken.getUTCMonth(), day: taken.getUTCDate() }
    }
    const uploaded = parseDate(photo.createdAt)
    return uploaded ? localDay(uploaded) : null
}

/** Sort key: capture time when known, otherwise upload time. */
export function photoTime(photo: Photo): number {
    return (parseDate(photo.takenAt) ?? parseDate(photo.createdAt))?.getTime() ?? 0
}

/** Date and time shown for a photo, preferring when it was taken over when it was uploaded. */
export function formatPhotoDate(photo: Photo): string {
    const taken = parseDate(photo.takenAt)
    if (taken) return taken.toLocaleString(undefined, { timeZone: 'UTC' })
    const uploaded = parseDate(photo.createdAt)
    return uploaded ? uploaded.toLocaleString() : ''
}

function sectionLabel(day: CalendarDay): string {
    const now = new Date()
    const yesterday = new Date(now)
    yesterday.setDate(now.getDate() - 1)

    if (isSameDay(day, localDay(now))) return 'Today'
    if (isSameDay(day, localDay(yesterday))) return 'Yesterday'

    return new Date(day.year, day.month, day.day).toLocaleDateString(undefined, {
        month: 'long',
        day: 'numeric',
        year: day.year === now.getFullYear() ? undefined : 'numeric',
    })
}

export function groupPhotosByDay(photos: Photo[]): PhotoSection[] {
    const sections: PhotoSection[] = []
    const indexByKey = new Map<string, number>()

    for (const photo of photos) {
        const day = dayOf(photo)
        const key = day ? `${day.year}-${day.month}-${day.day}` : 'unknown'

        let index = indexByKey.get(key)
        if (index === undefined) {
            index = sections.length
            indexByKey.set(key, index)
            sections.push({
                key,
                label: day ? sectionLabel(day) : 'Unknown date',
                photos: [],
            })
        }

        sections[index].photos.push(photo)
    }

    return sections
}
