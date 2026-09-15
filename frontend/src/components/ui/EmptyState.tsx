import type { ComponentType } from 'react'

type EmptyStateProps = {
    icon: ComponentType<{ className?: string }>
    title: string
    description: string
}

export function EmptyState({ icon: Icon, title, description }: EmptyStateProps) {
    return (
        <div className="flex min-h-[280px] flex-col items-center justify-center px-6 py-16 text-center">
            <Icon className="h-7 w-7 text-neutral-400 dark:text-neutral-600" />
            <h3 className="mt-4 text-[15px] font-medium text-neutral-900 dark:text-neutral-100">{title}</h3>
            <p className="mt-1.5 max-w-xs text-sm text-neutral-500 dark:text-neutral-500">{description}</p>
        </div>
    )
}
