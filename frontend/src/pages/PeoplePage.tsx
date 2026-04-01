import { useEffect, useRef } from 'react'
import { Users } from 'lucide-react'
import { PeopleGrid } from '../components/PeopleGrid'
import { usePeople } from '../hooks/usePeople'

function PeopleSkeleton() {
    return (
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 sm:gap-4 lg:grid-cols-4 xl:grid-cols-5">
            {Array.from({ length: 8 }).map((_, index) => (
                <div key={index} className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
                    <div className="aspect-square animate-pulse bg-slate-200/80" />
                    <div className="space-y-2 px-3 py-3">
                        <div className="h-3 w-24 animate-pulse rounded-full bg-slate-200/80" />
                        <div className="h-3 w-16 animate-pulse rounded-full bg-slate-100" />
                    </div>
                </div>
            ))}
        </div>
    )
}

function PeopleEmptyState() {
    return (
        <div className="flex min-h-[280px] flex-col items-center justify-center rounded-3xl border border-dashed border-slate-300 bg-slate-50/80 px-6 py-10 text-center">
            <span className="flex h-12 w-12 items-center justify-center rounded-2xl bg-white text-slate-500 shadow-sm ring-1 ring-slate-200">
                <Users className="h-6 w-6" />
            </span>
            <h3 className="mt-4 text-base font-semibold text-slate-900">No identities detected</h3>
            <p className="mt-2 max-w-md text-sm text-slate-500">
                Once the backend finds faces in uploaded photos, grouped people cards will appear here.
            </p>
        </div>
    )
}

function PeopleErrorState({ onRetry }: { onRetry: () => void }) {
    return (
        <div className="flex min-h-[280px] flex-col items-center justify-center rounded-3xl border border-red-200 bg-red-50/80 px-6 py-10 text-center">
            <h3 className="text-base font-semibold text-red-900">Could not load people</h3>
            <p className="mt-2 max-w-md text-sm text-red-700/90">
                Check the backend connection or try again. If all people have already been loaded, the page will show
                the full set below.
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

function PeopleEndState() {
    return (
        <div className="rounded-2xl border border-slate-200 bg-white/80 px-4 py-3 text-center text-sm text-slate-600 shadow-sm">
            You&apos;ve reached the end of the people list.
        </div>
    )
}

export function PeoplePage() {
    const peopleQuery = usePeople()
    const sentinelRef = useRef<HTMLDivElement | null>(null)
    const people = (peopleQuery.data?.pages.flatMap((page) => page.items) ?? []).filter(
        (person) => person.id !== '-1',
    )
    const hasPeople = people.length > 0
    const showInitialError = peopleQuery.isError && !hasPeople
    const showPageError = peopleQuery.isError && hasPeople

    useEffect(() => {
        const sentinel = sentinelRef.current
        if (!sentinel) {
            return
        }

        const observer = new IntersectionObserver(
            (entries) => {
                const target = entries[0]
                if (target.isIntersecting && peopleQuery.hasNextPage && !peopleQuery.isFetchingNextPage) {
                    peopleQuery.fetchNextPage()
                }
            },
            { rootMargin: '200px' },
        )

        observer.observe(sentinel)
        return () => observer.disconnect()
    }, [peopleQuery.fetchNextPage, peopleQuery.hasNextPage, peopleQuery.isFetchingNextPage])

    return (
        <section className="space-y-4 rounded-2xl border border-slate-200 bg-gradient-to-b from-white to-slate-50/70 p-4 sm:p-5">
            <div className="flex items-end justify-between gap-4 rounded-xl border border-slate-200 bg-white/70 px-4 py-3 shadow-sm backdrop-blur-sm">
                <div>
                    <p className="text-xs font-semibold uppercase tracking-[0.22em] text-slate-500">People</p>
                    <h1 className="mt-1 text-lg font-semibold tracking-tight text-slate-950">Detected identities</h1>
                </div>
                <p className="rounded-full bg-slate-100 px-2.5 py-1 text-xs font-medium text-slate-600">
                    {people.length} identities
                </p>
            </div>

            {peopleQuery.isLoading && !hasPeople ? (
                <PeopleSkeleton />
            ) : showInitialError ? (
                <PeopleErrorState onRetry={() => peopleQuery.refetch()} />
            ) : !hasPeople ? (
                <PeopleEmptyState />
            ) : (
                <PeopleGrid people={people} />
            )}

            {showPageError && (
                <div className="mt-4 rounded-2xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900">
                    <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                        <p>More people could not be loaded right now.</p>
                        <button
                            type="button"
                            onClick={() => peopleQuery.fetchNextPage()}
                            className="rounded-lg border border-amber-200 bg-white px-3 py-1.5 text-sm font-medium text-amber-900 transition hover:border-amber-300"
                        >
                            Try again
                        </button>
                    </div>
                </div>
            )}

            {peopleQuery.hasNextPage && (
                <div className="mt-3 flex justify-center">
                    <button
                        type="button"
                        onClick={() => peopleQuery.fetchNextPage()}
                        disabled={peopleQuery.isFetchingNextPage}
                        className="rounded-md border border-slate-300 px-3 py-1.5 text-sm text-slate-700 disabled:opacity-60"
                    >
                        {peopleQuery.isFetchingNextPage ? 'Loading more...' : 'Load more'}
                    </button>
                </div>
            )}

            {!peopleQuery.hasNextPage && hasPeople && <PeopleEndState />}

            <div ref={sentinelRef} className="h-6" />
        </section>
    )
}
