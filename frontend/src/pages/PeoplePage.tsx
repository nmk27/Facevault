import { useEffect, useRef } from 'react'
import { Users } from 'lucide-react'
import { PeopleGrid } from '../components/people/PeopleGrid'
import { EmptyState } from '../components/ui/EmptyState'
import { ErrorState } from '../components/ui/ErrorState'
import { GridSkeleton } from '../components/ui/GridSkeleton'
import { usePeople } from '../hooks/usePeople'

export function PeoplePage() {
    const peopleQuery = usePeople()
    const sentinelRef = useRef<HTMLDivElement | null>(null)
    const people = peopleQuery.data?.pages.flatMap((page) => page.items) ?? []
    const hasPeople = people.length > 0
    const showInitialError = peopleQuery.isError && !hasPeople

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
            { rootMargin: '400px' },
        )

        observer.observe(sentinel)
        return () => observer.disconnect()
    }, [peopleQuery.fetchNextPage, peopleQuery.hasNextPage, peopleQuery.isFetchingNextPage])

    return (
        <div className="space-y-5">
            {peopleQuery.isLoading && !hasPeople ? (
                <GridSkeleton count={16} circle />
            ) : showInitialError ? (
                <ErrorState
                    title="Could not load people"
                    description="Check the backend connection and try again."
                    onRetry={() => peopleQuery.refetch()}
                />
            ) : !hasPeople ? (
                <EmptyState
                    icon={Users}
                    title="No people yet"
                    description="Once faces are detected in your photos, they'll show up here."
                />
            ) : (
                <PeopleGrid people={people} />
            )}

            <div ref={sentinelRef} className="h-6" />
        </div>
    )
}
