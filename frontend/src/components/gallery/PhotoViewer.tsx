import { useEffect, useState } from 'react'
import { ChevronLeft, ChevronRight, X } from 'lucide-react'
import type { FaceBox, Photo } from '../../types'
import { FaceOverlay } from './FaceOverlay'
import { SmartImage } from '../shared/SmartImage'
import { formatPhotoDate } from '../../utils'

type PhotoViewerProps = {
    photo: Photo
    faces: FaceBox[]
    onClose: () => void
    onPrev?: () => void
    onNext?: () => void
}

export function PhotoViewer({ photo, faces, onClose, onPrev, onNext }: PhotoViewerProps) {
    const [renderedSize, setRenderedSize] = useState({ width: 0, height: 0 })
    const [naturalSize, setNaturalSize] = useState({ width: 0, height: 0 })
    const faceCount = faces.length

    useEffect(() => {
        function handleKeyDown(event: KeyboardEvent) {
            if (event.key === 'Escape') {
                onClose()
            } else if (event.key === 'ArrowLeft' && onPrev) {
                onPrev()
            } else if (event.key === 'ArrowRight' && onNext) {
                onNext()
            }
        }

        window.addEventListener('keydown', handleKeyDown)
        return () => window.removeEventListener('keydown', handleKeyDown)
    }, [onClose, onPrev, onNext])

    return (
        <div className="fixed inset-0 z-50 flex flex-col bg-black">
            <header className="z-10 flex items-center justify-between gap-2 bg-gradient-to-b from-black/70 to-transparent px-4 py-3 sm:px-6">
                <button
                    type="button"
                    onClick={onClose}
                    className="flex h-9 w-9 items-center justify-center rounded-full text-white/90 transition hover:bg-white/10"
                    aria-label="Close"
                >
                    <X className="h-5 w-5" />
                </button>

                <div className="flex items-center gap-2 text-xs font-medium text-white/70">
                    <span>{formatPhotoDate(photo)}</span>
                    {photo.width && photo.height && (
                        <span className="hidden sm:inline">
                            · {photo.width}×{photo.height}
                        </span>
                    )}
                    <span>
                        · {faceCount} {faceCount === 1 ? 'face' : 'faces'}
                    </span>
                </div>
            </header>

            <div className="relative flex flex-1 items-center justify-center overflow-hidden px-2 pb-4">
                {onPrev && (
                    <button
                        type="button"
                        onClick={onPrev}
                        className="absolute left-2 top-1/2 z-10 flex h-10 w-10 -translate-y-1/2 items-center justify-center rounded-full text-white/80 transition hover:bg-white/10 sm:left-4"
                        aria-label="Previous photo"
                    >
                        <ChevronLeft className="h-6 w-6" />
                    </button>
                )}

                <div
                    className="relative inline-block max-h-full max-w-full"
                    style={{ width: renderedSize.width || undefined, height: renderedSize.height || undefined }}
                >
                    <SmartImage
                        src={photo.url}
                        fallbackSrc={photo.thumbnailUrl || photo.url}
                        alt="Photo"
                        className="block max-h-[calc(100svh-96px)] max-w-full"
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

                {onNext && (
                    <button
                        type="button"
                        onClick={onNext}
                        className="absolute right-2 top-1/2 z-10 flex h-10 w-10 -translate-y-1/2 items-center justify-center rounded-full text-white/80 transition hover:bg-white/10 sm:right-4"
                        aria-label="Next photo"
                    >
                        <ChevronRight className="h-6 w-6" />
                    </button>
                )}
            </div>
        </div>
    )
}
