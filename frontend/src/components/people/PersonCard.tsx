import type { CSSProperties } from 'react'
import type { Person } from '../../types'
import { SmartImage } from '../shared/SmartImage'

type PersonCardProps = {
    person: Person
    onClick: (person: Person) => void
    style?: CSSProperties
}

export function PersonCard({ person, onClick, style }: PersonCardProps) {
    const initials = person.name
        .split(' ')
        .map((part) => part[0])
        .join('')
        .slice(0, 2)
        .toUpperCase()

    return (
        <button
            type="button"
            style={style}
            onClick={() => onClick(person)}
            className="group flex flex-col items-center gap-2 rounded-2xl p-2 text-center transition hover:bg-neutral-900/5 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-sky-400 dark:hover:bg-white/5"
        >
            <div className="relative aspect-square w-full overflow-hidden rounded-full bg-neutral-200 dark:bg-neutral-800">
                {person.coverUrl ? (
                    <SmartImage
                        src={person.coverUrl}
                        alt={person.name}
                        className="h-full w-full object-cover transition duration-300 group-hover:scale-[1.05]"
                    />
                ) : (
                    <div className="flex h-full w-full items-center justify-center bg-neutral-300 dark:bg-neutral-700">
                        <span className="text-lg font-semibold text-neutral-600 dark:text-neutral-300">
                            {initials || '?'}
                        </span>
                    </div>
                )}
            </div>

            <div className="w-full">
                <p className="truncate text-sm font-medium text-neutral-900 dark:text-neutral-100">{person.name}</p>
                <p className="text-xs text-neutral-500">{person.faceCount} {person.faceCount === 1 ? 'photo' : 'photos'}</p>
            </div>
        </button>
    )
}
