import { useEffect, useRef } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { PhotoGrid } from '../components/PhotoGrid'
import { UploadDropzone } from '../components/UploadDropzone'
import { usePhotos } from '../hooks/usePhotos'
import { uploadPhotos } from '../services/api'

export function GalleryPage() {
    const queryClient = useQueryClient()
    const photosQuery = usePhotos()
    const sentinelRef = useRef<HTMLDivElement | null>(null)

    const photos = photosQuery.data?.pages.flatMap((page) => page.items) ?? []

    useEffect(() => {
        const sentinel = sentinelRef.current
        if (!sentinel) {
            return
        }

        const observer = new IntersectionObserver(
            (entries) => {
                const target = entries[0]
                if (target.isIntersecting && photosQuery.hasNextPage && !photosQuery.isFetchingNextPage) {
                    photosQuery.fetchNextPage()
                }
            },
            { rootMargin: '200px' },
        )

        observer.observe(sentinel)
        return () => observer.disconnect()
    }, [photosQuery.fetchNextPage, photosQuery.hasNextPage, photosQuery.isFetchingNextPage])

    async function handleUpload(files: readonly File[], onProgress: (progress: number) => void) {
        await uploadPhotos(files, onProgress)
        await queryClient.invalidateQueries({ queryKey: ['photos'] })
    }

    return (
        <div className="space-y-4">
            <UploadDropzone onUpload={handleUpload} />

            <section className="rounded-lg border border-slate-200 bg-white p-4">
                <div className="mb-3 flex items-center justify-between">
                    <h2 className="text-sm font-semibold text-slate-900">Gallery</h2>
                    <p className="text-xs text-slate-500">{photos.length} photos</p>
                </div>

                {photosQuery.isError && (
                    <p className="mb-3 text-sm text-red-600">
                        Failed to fetch photos from backend. Check backend server and CORS on
                        {' '}
                        {import.meta.env.VITE_API_BASE_URL?.trim() || 'http://127.0.0.1:8000'}.
                    </p>
                )}

                {photos.length === 0 && !photosQuery.isLoading ? (
                    <p className="text-sm text-slate-500">No photos available.</p>
                ) : (
                    <PhotoGrid photos={photos} />
                )}

                {photosQuery.hasNextPage && (
                    <div className="mt-3 flex justify-center">
                        <button
                            type="button"
                            onClick={() => photosQuery.fetchNextPage()}
                            disabled={photosQuery.isFetchingNextPage}
                            className="rounded-md border border-slate-300 px-3 py-1.5 text-sm text-slate-700 disabled:opacity-60"
                        >
                            {photosQuery.isFetchingNextPage ? 'Loading more...' : 'Load more'}
                        </button>
                    </div>
                )}

                <div ref={sentinelRef} className="h-6" />
            </section>
        </div>
    )
}
