import { Link, useParams } from 'react-router-dom'
import { PhotoViewer } from '../components/PhotoViewer'
import { useFaces } from '../hooks/useFaces'
import { usePhoto } from '../hooks/usePhotos'

export function PhotoPage() {
    const { photoId } = useParams()
    const photoQuery = usePhoto(photoId)
    const facesQuery = useFaces(photoId)
    const faceCount = facesQuery.data?.length ?? 0

    if (photoQuery.isLoading) {
        return (
            <div className="space-y-4">
                <Link to="/" className="text-sm font-medium text-slate-600 underline decoration-slate-300 underline-offset-4">
                    Back to gallery
                </Link>

                <div className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_300px] xl:items-start">
                    <div className="overflow-hidden rounded-3xl border border-slate-200 bg-white/80 p-4 shadow-sm backdrop-blur-sm">
                        <div className="aspect-[4/3] animate-pulse rounded-2xl bg-slate-200/80" />
                        <div className="mt-4 h-3 w-40 animate-pulse rounded-full bg-slate-200/80" />
                    </div>
                    <aside className="space-y-3 rounded-3xl border border-slate-200 bg-white/80 p-4 shadow-sm backdrop-blur-sm">
                        <div className="h-3 w-24 animate-pulse rounded-full bg-slate-200/80" />
                        <div className="h-16 animate-pulse rounded-2xl bg-slate-200/80" />
                        <div className="h-16 animate-pulse rounded-2xl bg-slate-200/80" />
                    </aside>
                </div>
            </div>
        )
    }

    if (!photoQuery.data) {
        return (
            <div className="space-y-4">
                <Link to="/" className="text-sm font-medium text-slate-600 underline decoration-slate-300 underline-offset-4">
                    Back to gallery
                </Link>
                <div className="rounded-3xl border border-dashed border-slate-300 bg-slate-50/80 px-6 py-10 text-center">
                    <p className="text-sm font-medium text-slate-900">Photo not found</p>
                    <p className="mt-2 text-sm text-slate-500">The requested image may have been removed or is unavailable.</p>
                </div>
            </div>
        )
    }

    return (
        <div className="space-y-4">
            <Link to="/" className="text-sm font-medium text-slate-600 underline decoration-slate-300 underline-offset-4">
                Back to gallery
            </Link>
            <div className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_300px] xl:items-start">
                <PhotoViewer photo={photoQuery.data} faces={facesQuery.data ?? []} />

                <aside className="space-y-3 rounded-3xl border border-slate-200 bg-white/80 p-4 shadow-sm backdrop-blur-sm">
                    <div>
                        <p className="text-xs font-semibold uppercase tracking-[0.22em] text-slate-500">Details</p>
                        <h2 className="mt-1 text-base font-semibold tracking-tight text-slate-950">Photo metadata</h2>
                    </div>

                    <div className="space-y-3">
                        <div className="rounded-2xl bg-slate-50 p-3">
                            <p className="text-xs font-medium text-slate-500">Created</p>
                            <p className="mt-1 text-sm font-semibold text-slate-900">
                                {new Date(photoQuery.data.createdAt).toLocaleString()}
                            </p>
                        </div>

                        <div className="rounded-2xl bg-slate-50 p-3">
                            <p className="text-xs font-medium text-slate-500">Faces detected</p>
                            <p className="mt-1 text-sm font-semibold text-slate-900">{faceCount}</p>
                        </div>

                        <div className="rounded-2xl bg-slate-50 p-3">
                            <p className="text-xs font-medium text-slate-500">Dimensions</p>
                            <p className="mt-1 text-sm font-semibold text-slate-900">
                                {photoQuery.data.width && photoQuery.data.height
                                    ? `${photoQuery.data.width} × ${photoQuery.data.height}`
                                    : 'Unknown'}
                            </p>
                        </div>
                    </div>

                    <p className="text-xs leading-5 text-slate-500">
                        Face boxes are color-coded in the viewer: green means identified, red means unknown.
                    </p>
                </aside>
            </div>
        </div>
    )
}
