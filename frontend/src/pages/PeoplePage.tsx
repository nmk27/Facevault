import { useEffect, useRef } from 'react'
import { PeopleGrid } from '../components/PeopleGrid'
import { usePeople } from '../hooks/usePeople'

export function PeoplePage() {
    const peopleQuery = usePeople()
    const sentinelRef = useRef<HTMLDivElement | null>(null)
    const people = (peopleQuery.data?.pages.flatMap((page) => page.items) ?? []).filter(
        (person) => person.id !== '-1',
    )

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
        <section className="rounded-lg border border-slate-200 bg-white p-4">
            <div className="mb-3 flex items-center justify-between">
                <h2 className="text-sm font-semibold text-slate-900">People</h2>
                <p className="text-xs text-slate-500">{people.length} identities</p>
            </div>

            {peopleQuery.isError && (
                <p className="mb-3 text-sm text-red-600">
                    Failed to fetch people from backend endpoint /faces/people/.
                </p>
            )}

            {people.length === 0 && !peopleQuery.isLoading ? (
                <p className="text-sm text-slate-500">No clustered identities available.</p>
            ) : (
                <PeopleGrid people={people} />
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

            <div ref={sentinelRef} className="h-6" />
        </section>
    )
}
