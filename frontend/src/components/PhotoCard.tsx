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
            className="group h-full w-full overflow-hidden rounded-md border border-slate-200 bg-white text-left"
        >
            <SmartImage
                src={photo.thumbnailUrl || photo.url}
                fallbackSrc={photo.url}
                alt={photo.title}
                className="h-[82%] w-full object-cover transition duration-200 group-hover:scale-[1.02]"
            />
            <div className="space-y-0.5 px-2 py-1.5">
                <p className="truncate text-xs font-medium text-slate-800">{photo.title}</p>
                <p className="text-[11px] text-slate-500">{dateLabel}</p>
            </div>
        </button>
    )
}
