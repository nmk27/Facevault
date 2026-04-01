import { Link, useParams } from 'react-router-dom'
import { PhotoViewer } from '../components/PhotoViewer'
import { useFaces } from '../hooks/useFaces'
import { usePhoto } from '../hooks/usePhotos'

export function PhotoPage() {
    const { photoId } = useParams()
    const photoQuery = usePhoto(photoId)
    const facesQuery = useFaces(photoId)

    if (photoQuery.isLoading) {
        return <p className="text-sm text-slate-500">Loading photo...</p>
    }

    if (!photoQuery.data) {
        return (
            <div className="space-y-3">
                <p className="text-sm text-slate-500">Photo not found.</p>
                <Link to="/" className="text-sm text-slate-900 underline">
                    Back to gallery
                </Link>
            </div>
        )
    }

    return (
        <div className="space-y-3">
            <Link to="/" className="text-sm text-slate-600 underline">
                Back to gallery
            </Link>
            <PhotoViewer photo={photoQuery.data} faces={facesQuery.data ?? []} />
        </div>
    )
}
