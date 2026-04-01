import { useNavigate } from 'react-router-dom'
import type { Photo } from '../types'
import { PhotoCard } from './PhotoCard'

type PhotoGridProps = {
    photos: Photo[]
}

export function PhotoGrid({ photos }: PhotoGridProps) {
    const navigate = useNavigate()

    return (
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 sm:gap-4 lg:grid-cols-4 xl:grid-cols-5 2xl:grid-cols-6">
            {photos.map((photo) => (
                <PhotoCard key={photo.id} photo={photo} onClick={(selected) => navigate(`/photos/${selected.id}`)} />
            ))}
        </div>
    )
}
