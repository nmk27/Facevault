import type { CSSProperties } from 'react'
import type { Photo } from '../../types'
import { SmartImage } from '../shared/SmartImage'

type PhotoCardProps = {
    photo: Photo
    onClick: (photo: Photo) => void
    style?: CSSProperties
}

export function PhotoCard({ photo, onClick, style }: PhotoCardProps) {
    return (
        <button
            type="button"
            style={style}
            onClick={() => onClick(photo)}
            className="group relative block h-full w-full overflow-hidden bg-neutral-100 focus-visible:z-10 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-sky-400 dark:bg-neutral-900"
        >
            <SmartImage
                src={photo.thumbnailUrl || photo.url}
                fallbackSrc={photo.url}
                alt={photo.title}
                className="h-full w-full object-cover transition duration-300 ease-out group-hover:scale-[1.03]"
            />
        </button>
    )
}
