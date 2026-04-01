import type { CSSProperties } from 'react'
import type { Person } from '../types'
import { SmartImage } from './SmartImage'

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
            className="group h-full w-full overflow-hidden rounded-xl border border-slate-200 bg-white text-left shadow-sm transition hover:-translate-y-0.5 hover:border-slate-300 hover:shadow-md"
        >
            <div className="aspect-square w-full overflow-hidden bg-slate-100">
                {person.coverUrl ? (
                    <SmartImage
                        src={person.coverUrl}
                        alt={person.name}
                        className="h-full w-full object-cover transition duration-300 group-hover:scale-[1.03]"
                    />
                ) : (
                    <div className="flex h-full w-full items-center justify-center bg-gradient-to-br from-slate-200 to-slate-300">
                        <span className="text-xl font-semibold tracking-wide text-slate-600">{initials || '?'}</span>
                    </div>
                )}
            </div>

            <div className="space-y-1 px-3 py-2.5">
                <p className="truncate text-sm font-semibold text-slate-900">{person.name}</p>
                <p className="text-xs text-slate-500">{person.faceCount} {person.faceCount === 1 ? 'face' : 'faces'}</p>
            </div>
        </button>
    )
}
