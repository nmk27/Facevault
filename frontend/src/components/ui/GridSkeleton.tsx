type GridSkeletonProps = {
    count?: number
    circle?: boolean
}

export function GridSkeleton({ count = 24, circle = false }: GridSkeletonProps) {
    return (
        <div className="grid grid-cols-3 gap-1 sm:grid-cols-4 sm:gap-1.5 md:grid-cols-5 lg:grid-cols-6 xl:grid-cols-7">
            {Array.from({ length: count }).map((_, index) => (
                <div
                    key={index}
                    className={`aspect-square animate-pulse bg-neutral-200/70 dark:bg-neutral-800/70 ${circle ? 'rounded-full' : ''}`}
                />
            ))}
        </div>
    )
}
