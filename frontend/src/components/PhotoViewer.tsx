import { useMemo, useState } from 'react'
import type { FaceBox, Photo } from '../types'
import { FaceOverlay } from './FaceOverlay'
import { SmartImage } from './SmartImage'

type PhotoViewerProps = {
    photo: Photo
    faces: FaceBox[]
}

export function PhotoViewer({ photo, faces }: PhotoViewerProps) {
    const [renderedSize, setRenderedSize] = useState({ width: 0, height: 0 })
    const [naturalSize, setNaturalSize] = useState({ width: 0, height: 0 })
    const createdAtLabel = new Date(photo.createdAt).toLocaleString()
    const faceCount = faces.length

    const isHeicLike = useMemo(() => {
        const value = photo.url.toLowerCase()
        return value.includes('.heic') || value.includes('.heif')
    }, [photo.url])

    const displaySrc = isHeicLike && photo.thumbnailUrl ? photo.thumbnailUrl : photo.url

    return (
        <section className="space-y-4 overflow-hidden rounded-3xl border border-slate-200 bg-white/85 p-4 shadow-sm backdrop-blur-sm">
            <header className="flex flex-wrap items-center justify-between gap-2">
                <div className="flex flex-wrap gap-2">
                    <span className="rounded-full bg-slate-100 px-2.5 py-1 text-xs font-medium text-slate-600">
                        {createdAtLabel}
                    </span>
                    <span className="rounded-full bg-slate-100 px-2.5 py-1 text-xs font-medium text-slate-600">
                        {photo.width && photo.height ? `${photo.width} × ${photo.height}` : 'Unknown size'}
                    </span>
                </div>
                <span className="rounded-full bg-slate-900 px-2.5 py-1 text-xs font-medium text-white shadow-sm">
                    {faceCount} {faceCount === 1 ? 'face' : 'faces'}
                </span>
            </header>

            <div className="mx-auto flex w-full justify-center rounded-2xl bg-slate-100/80 p-2 sm:p-3">
                <div
                    className="relative inline-block max-h-[78vh] max-w-full"
                    style={{ width: renderedSize.width || undefined, height: renderedSize.height || undefined }}
                >
                    <SmartImage
                        src={displaySrc}
                        fallbackSrc={photo.thumbnailUrl || photo.url}
                        alt="Photo"
                        className="block max-h-[78vh] max-w-full"
                        style={{ imageOrientation: 'none' }}
                        onLoad={(event) => {
                            const image = event.currentTarget
                            setRenderedSize({ width: image.clientWidth, height: image.clientHeight })
                            setNaturalSize({ width: image.naturalWidth, height: image.naturalHeight })
                        }}
                    />
                    <FaceOverlay
                        faces={faces}
                        imageWidth={photo.width || naturalSize.width}
                        imageHeight={photo.height || naturalSize.height}
                        renderedWidth={renderedSize.width}
                        renderedHeight={renderedSize.height}
                    />
                </div>
            </div>

            <div className="flex flex-wrap gap-2 text-xs text-slate-500">
                <span className="rounded-full bg-emerald-50 px-2.5 py-1 font-medium text-emerald-700">
                    Green = identified person
                </span>
                <span className="rounded-full bg-red-50 px-2.5 py-1 font-medium text-red-700">
                    Red = unknown
                </span>
            </div>
        </section>
    )
}
