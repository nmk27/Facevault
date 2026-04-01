import { useInfiniteQuery, useQuery } from '@tanstack/react-query'
import { getPeople, getPerson } from '../services/api'

export function usePeople() {
    return useInfiniteQuery({
        queryKey: ['people'],
        initialPageParam: 1,
        queryFn: ({ pageParam }) => getPeople(pageParam),
        getNextPageParam: (lastPage) => lastPage.nextPage,
    })
}

export function usePerson(personId: string | undefined) {
    return useQuery({
        queryKey: ['person', personId],
        queryFn: () => getPerson(personId ?? ''),
        enabled: Boolean(personId),
    })
}
