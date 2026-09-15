import { useNavigate } from 'react-router-dom'
import type { Photo } from '../../types'
import { groupPhotosByDay } from '../../utils'
import { PhotoCard } from './PhotoCard'

type PhotoGridProps = {
    photos: Photo[]
    groupByDay?: boolean
}

const GRID_CLASSES =
    'grid grid-cols-3 gap-1 sm:grid-cols-4 sm:gap-1.5 md:grid-cols-5 lg:grid-cols-6 xl:grid-cols-7'

export function PhotoGrid({ photos, groupByDay = true }: PhotoGridProps) {
    const navigate = useNavigate()
    const goToPhoto = (photo: Photo) => navigate(`/photos/${photo.id}`)

    if (!groupByDay) {
        return (
            <div className={GRID_CLASSES}>
                {photos.map((photo) => (
                    <PhotoCard key={photo.id} photo={photo} onClick={goToPhoto} />
                ))}
            </div>
        )
    }

    const sections = groupPhotosByDay(photos)

    return (
        <div className="space-y-6">
            {sections.map((section) => (
                <section key={section.key}>
                    <h3 className="mb-2 px-0.5 text-sm font-semibold text-neutral-900 dark:text-neutral-100">
                        {section.label}
                    </h3>
                    <div className={GRID_CLASSES}>
                        {section.photos.map((photo) => (
                            <PhotoCard key={photo.id} photo={photo} onClick={goToPhoto} />
                        ))}
                    </div>
                </section>
            ))}
        </div>
    )
}
