import { useInfiniteQuery, useQuery } from '@tanstack/react-query'
import { getPhotoById, getPhotos } from '../services/api'

export function usePhotos() {
    return useInfiniteQuery({
        queryKey: ['photos'],
        initialPageParam: 1,
        queryFn: ({ pageParam }) => getPhotos(pageParam),
        getNextPageParam: (lastPage) => lastPage.nextPage,
    })
}

export function usePhoto(photoId: string | undefined) {
    return useQuery({
        queryKey: ['photo', photoId],
        queryFn: () => getPhotoById(photoId ?? ''),
        enabled: Boolean(photoId),
    })
}
