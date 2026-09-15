import { useNavigate, useParams } from 'react-router-dom'
import { useQueryClient, type InfiniteData } from '@tanstack/react-query'
import { PhotoViewer } from '../components/gallery/PhotoViewer'
import { useFaces } from '../hooks/useFaces'
import { usePhoto } from '../hooks/usePhotos'
import type { Paginated, Photo } from '../types'

export function PhotoPage() {
    const { photoId } = useParams()
    const navigate = useNavigate()
    const queryClient = useQueryClient()
    const photoQuery = usePhoto(photoId)
    const facesQuery = useFaces(photoId)

    const cached = queryClient.getQueryData<InfiniteData<Paginated<Photo>>>(['photos'])
    const loadedPhotos = cached?.pages.flatMap((page) => page.items) ?? []
    const currentIndex = loadedPhotos.findIndex((photo) => photo.id === photoId)
    const prevPhoto = currentIndex > 0 ? loadedPhotos[currentIndex - 1] : undefined
    const nextPhoto =
        currentIndex >= 0 && currentIndex < loadedPhotos.length - 1 ? loadedPhotos[currentIndex + 1] : undefined

    function close() {
        navigate('/')
    }

    if (photoQuery.isLoading) {
        return (
            <div className="fixed inset-0 z-50 flex items-center justify-center bg-black">
                <div className="h-8 w-8 animate-spin rounded-full border-2 border-white/20 border-t-white" />
            </div>
        )
    }

    if (!photoQuery.data) {
        return (
            <div className="fixed inset-0 z-50 flex flex-col items-center justify-center gap-3 bg-black text-center text-white">
                <p className="text-sm font-medium">Photo not found</p>
                <p className="max-w-xs text-sm text-white/60">The requested image may have been removed or is unavailable.</p>
                <button type="button" onClick={close} className="mt-2 rounded-full bg-white px-4 py-1.5 text-sm font-medium text-black">
                    Back to gallery
                </button>
            </div>
        )
    }

    return (
        <PhotoViewer
            photo={photoQuery.data}
            faces={facesQuery.data ?? []}
            onClose={close}
            onPrev={prevPhoto ? () => navigate(`/photos/${prevPhoto.id}`) : undefined}
            onNext={nextPhoto ? () => navigate(`/photos/${nextPhoto.id}`) : undefined}
        />
    )
}
