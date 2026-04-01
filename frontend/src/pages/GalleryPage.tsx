import { useEffect, useRef } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { ImageIcon } from 'lucide-react'
import { PhotoGrid } from '../components/PhotoGrid'
import { UploadDropzone } from '../components/UploadDropzone'
import { usePhotos } from '../hooks/usePhotos'
import { uploadPhotos } from '../services/api'

function GallerySkeleton() {
    return (
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 sm:gap-4 lg:grid-cols-4 xl:grid-cols-5 2xl:grid-cols-6">
            {Array.from({ length: 8 }).map((_, index) => (
                <div
                    key={index}
                    className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm"
                >
                    <div className="aspect-square animate-pulse bg-slate-200/80" />
                    <div className="space-y-2 px-3 py-3">
                        <div className="h-3 w-20 animate-pulse rounded-full bg-slate-200/80" />
                    </div>
                </div>
            ))}
        </div>
    )
}

function GalleryEmptyState() {
    return (
        <div className="flex min-h-[280px] flex-col items-center justify-center rounded-3xl border border-dashed border-slate-300 bg-slate-50/80 px-6 py-10 text-center">
            <span className="flex h-12 w-12 items-center justify-center rounded-2xl bg-white text-slate-500 shadow-sm ring-1 ring-slate-200">
                <ImageIcon className="h-6 w-6" />
            </span>
            <h3 className="mt-4 text-base font-semibold text-slate-900">No photos yet</h3>
            <p className="mt-2 max-w-md text-sm text-slate-500">
                Add a few images using the upload panel above, then they will appear here in a clean grid.
            </p>
        </div>
    )
}

function GalleryErrorState({ onRetry }: { onRetry: () => void }) {
    return (
        <div className="flex min-h-[280px] flex-col items-center justify-center rounded-3xl border border-red-200 bg-red-50/80 px-6 py-10 text-center">
            <h3 className="text-base font-semibold text-red-900">Could not load photos</h3>
            <p className="mt-2 max-w-md text-sm text-red-700/90">
                Check the backend connection or try again. If you just reached the end of the library, no action is
                needed.
            </p>
            <button
                type="button"
                onClick={onRetry}
                className="mt-4 rounded-lg border border-red-200 bg-white px-3 py-1.5 text-sm font-medium text-red-700 transition hover:border-red-300"
            >
                Retry
            </button>
        </div>
    )
}

function GalleryEndState() {
    return (
        <div className="rounded-2xl border border-slate-200 bg-white/80 px-4 py-3 text-center text-sm text-slate-600 shadow-sm">
            You&apos;ve reached the end of the gallery.
        </div>
    )
}

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
        <div className="space-y-4 sm:space-y-5">
            <section className="flex items-end justify-between gap-4 rounded-2xl border border-slate-200 bg-white/70 px-4 py-3 shadow-sm backdrop-blur-sm sm:px-5">
                <div>
                    <p className="text-xs font-semibold uppercase tracking-[0.22em] text-slate-500">Gallery</p>
                    <h1 className="mt-1 text-lg font-semibold tracking-tight text-slate-950">Your photo library</h1>
                </div>
                <p className="rounded-full bg-slate-100 px-2.5 py-1 text-xs font-medium text-slate-600">
                    {photos.length} photos
                </p>
            </section>

            <UploadDropzone onUpload={handleUpload} />

            <section className="rounded-2xl border border-slate-200 bg-gradient-to-b from-white to-slate-50/70 p-4 sm:p-5">
                <div className="mb-4 flex items-center justify-between">
                    <div>
                        <h2 className="text-base font-semibold tracking-tight text-slate-900">Gallery</h2>
                        <p className="text-xs text-slate-500">Your uploaded photos</p>
                    </div>
                    <p className="rounded-full bg-slate-100 px-2.5 py-1 text-xs font-medium text-slate-600">
                        {photos.length} photos
                    </p>
                </div>

                {photosQuery.isLoading && !hasPhotos ? (
                    <GallerySkeleton />
                ) : showInitialError ? (
                    <GalleryErrorState onRetry={() => photosQuery.refetch()} />
                ) : !hasPhotos ? (
                    <GalleryEmptyState />
                ) : (
                    <PhotoGrid photos={photos} />
                )}

                {showPageError && (
                    <div className="mt-4 rounded-2xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900">
                        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                            <p>More photos could not be loaded right now.</p>
                            <button
                                type="button"
                                onClick={() => photosQuery.fetchNextPage()}
                                className="rounded-lg border border-amber-200 bg-white px-3 py-1.5 text-sm font-medium text-amber-900 transition hover:border-amber-300"
                            >
                                Try again
                            </button>
                        </div>
                    </div>
                )}

                {photosQuery.hasNextPage && (
                    <div className="mt-3 flex justify-center">
                        <button
                            type="button"
                            onClick={() => photosQuery.fetchNextPage()}
                            disabled={photosQuery.isFetchingNextPage}
                            className="rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-sm font-medium text-slate-700 transition hover:border-slate-400 disabled:opacity-60"
                        >
                            {photosQuery.isFetchingNextPage ? 'Loading more...' : 'Load more'}
                        </button>
                    </div>
                )}

                {!photosQuery.hasNextPage && hasPhotos && <GalleryEndState />}

                <div ref={sentinelRef} className="h-6" />
            </section>
        </div>
    )
}
