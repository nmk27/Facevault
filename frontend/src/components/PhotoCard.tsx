import type { CSSProperties } from 'react'
import type { Photo } from '../types'
import { SmartImage } from './SmartImage'

type PhotoCardProps = {
    photo: Photo
    onClick: (photo: Photo) => void
    style?: CSSProperties
}

export function PhotoCard({ photo, onClick, style }: PhotoCardProps) {
    const dateLabel = photo.createdAt ? new Date(photo.createdAt).toLocaleDateString() : 'Unknown date'

    return (
        <button
            type="button"
            style={style}
            onClick={() => onClick(photo)}
            className="group relative h-full w-full overflow-hidden rounded-2xl border border-slate-200/90 bg-white text-left shadow-sm transition duration-300 hover:-translate-y-1 hover:border-slate-300 hover:shadow-lg focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-amber-400/70"
        >
            <div className="relative aspect-square w-full overflow-hidden bg-slate-100">
                <SmartImage
                    src={photo.thumbnailUrl || photo.url}
                    fallbackSrc={photo.url}
                    alt={photo.title}
                    className="h-full w-full object-cover transition duration-500 group-hover:scale-[1.06]"
                />
                <div className="pointer-events-none absolute inset-x-0 bottom-0 h-16 bg-gradient-to-t from-black/35 to-transparent" />
            </div>

            <div className="space-y-1 px-3 py-3">
                <p className="text-xs font-medium text-slate-500">{dateLabel}</p>
            </div>
        </button>
    )
}
