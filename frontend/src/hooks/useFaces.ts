import { useQuery } from '@tanstack/react-query'
import { getFaces } from '../services/api'

export function useFaces(photoId: string | undefined) {
    return useQuery({
        queryKey: ['faces', photoId],
        queryFn: () => getFaces(photoId ?? ''),
        enabled: Boolean(photoId),
    })
}
