import { useInfiniteQuery, useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { getPeople, getPerson, renamePerson } from '../services/api'

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

export function useRenamePerson(personId: string | undefined) {
    const queryClient = useQueryClient()

    return useMutation({
        mutationFn: (name: string) => renamePerson(personId ?? '', name),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['people'] })
            queryClient.invalidateQueries({ queryKey: ['person', personId] })
        },
    })
}
