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

    const isHeicLike = useMemo(() => {
        const value = photo.url.toLowerCase()
        return value.includes('.heic') || value.includes('.heif')
    }, [photo.url])

    const displaySrc = isHeicLike && photo.thumbnailUrl ? photo.thumbnailUrl : photo.url

    return (
        <section className="space-y-4 rounded-lg border border-slate-200 bg-white p-4">
            <header className="flex items-center justify-end">
                <p className="text-xs text-slate-500">{new Date(photo.createdAt).toLocaleString()}</p>
            </header>

            <div className="mx-auto flex w-full justify-center rounded-md bg-slate-100 p-2">
                <div
                    className="relative inline-block max-h-[75vh] max-w-full"
                    style={{ width: renderedSize.width || undefined, height: renderedSize.height || undefined }}
                >
                    <SmartImage
                        src={displaySrc}
                        fallbackSrc={photo.thumbnailUrl || photo.url}
                        alt="Photo"
                        className="block max-h-[75vh] max-w-full"
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

            <p className="text-xs text-slate-500">
                Face colors: green = identified person, red = unknown.
            </p>
        </section>
    )
}
