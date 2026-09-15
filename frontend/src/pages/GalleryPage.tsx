import { useEffect, useRef } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { ImageIcon } from 'lucide-react'
import { PhotoGrid } from '../components/gallery/PhotoGrid'
import { UploadDropzone } from '../components/upload/UploadDropzone'
import { EmptyState } from '../components/ui/EmptyState'
import { ErrorState } from '../components/ui/ErrorState'
import { GridSkeleton } from '../components/ui/GridSkeleton'
import { usePhotos } from '../hooks/usePhotos'
import { uploadPhotos } from '../services/api'

export function GalleryPage() {
    const queryClient = useQueryClient()
    const photosQuery = usePhotos()
    const sentinelRef = useRef<HTMLDivElement | null>(null)

    const photos = photosQuery.data?.pages.flatMap((page) => page.items) ?? []
    const hasPhotos = photos.length > 0
    const showInitialError = photosQuery.isError && !hasPhotos
    const showPageError = photosQuery.isError && hasPhotos

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
            { rootMargin: '400px' },
        )

        observer.observe(sentinel)
        return () => observer.disconnect()
    }, [photosQuery.fetchNextPage, photosQuery.hasNextPage, photosQuery.isFetchingNextPage])

    async function handleUpload(files: readonly File[], onProgress: (progress: number) => void) {
        await uploadPhotos(files, onProgress)
        await queryClient.invalidateQueries({ queryKey: ['photos'] })
    }

    return (
        <div className="space-y-5">
            <UploadDropzone onUpload={handleUpload} />

            {photosQuery.isLoading && !hasPhotos ? (
                <GridSkeleton />
            ) : showInitialError ? (
                <ErrorState
                    title="Could not load photos"
                    description="Check the backend connection and try again."
                    onRetry={() => photosQuery.refetch()}
                />
            ) : !hasPhotos ? (
                <EmptyState
                    icon={ImageIcon}
                    title="No photos yet"
                    description="Drop a few images above and they'll show up here."
                />
            ) : (
                <PhotoGrid photos={photos} />
            )}

            {showPageError && (
                <div className="rounded-xl bg-amber-500/10 px-4 py-3 text-sm text-amber-700 dark:text-amber-400">
                    <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
                        <p>More photos could not be loaded right now.</p>
                        <button
                            type="button"
                            onClick={() => photosQuery.fetchNextPage()}
                            className="rounded-full border border-amber-500/30 px-3 py-1 text-xs font-medium"
                        >
                            Try again
                        </button>
                    </div>
                </div>
            )}

            <div ref={sentinelRef} className="h-6" />
        </div>
    )
}
