type ErrorStateProps = {
    title: string
    description: string
    onRetry: () => void
}

export function ErrorState({ title, description, onRetry }: ErrorStateProps) {
    return (
        <div className="flex min-h-[280px] flex-col items-center justify-center px-6 py-16 text-center">
            <h3 className="text-[15px] font-medium text-neutral-900 dark:text-neutral-100">{title}</h3>
            <p className="mt-1.5 max-w-sm text-sm text-neutral-500 dark:text-neutral-500">{description}</p>
            <button
                type="button"
                onClick={onRetry}
                className="mt-4 rounded-full bg-neutral-900 px-4 py-1.5 text-sm font-medium text-white transition hover:bg-neutral-700 dark:bg-white dark:text-neutral-900 dark:hover:bg-neutral-200"
            >
                Retry
            </button>
        </div>
    )
}
