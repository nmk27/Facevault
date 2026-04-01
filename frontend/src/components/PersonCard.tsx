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
            className="group relative h-full w-full overflow-hidden rounded-2xl border border-slate-200/90 bg-white text-left shadow-sm transition duration-300 hover:-translate-y-1 hover:border-slate-300 hover:shadow-lg focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-amber-400/70"
        >
            <div className="relative aspect-square w-full overflow-hidden bg-slate-100">
                {person.coverUrl ? (
                    <SmartImage
                        src={person.coverUrl}
                        alt={person.name}
                        className="h-full w-full object-cover transition duration-500 group-hover:scale-[1.06]"
                    />
                ) : (
                    <div className="flex h-full w-full items-center justify-center bg-gradient-to-br from-amber-100 via-slate-200 to-slate-300">
                        <span className="text-xl font-semibold tracking-wide text-slate-700">{initials || '?'}</span>
                    </div>
                )}

                <div className="pointer-events-none absolute inset-x-0 bottom-0 h-16 bg-gradient-to-t from-black/35 to-transparent" />
                <div className="absolute left-2 top-2 rounded-full bg-white/90 px-2 py-0.5 text-[11px] font-semibold text-slate-700 backdrop-blur-sm">
                    {person.faceCount} {person.faceCount === 1 ? 'face' : 'faces'}
                </div>
            </div>

            <div className="space-y-1 px-3 py-3">
                <p className="truncate text-sm font-semibold tracking-tight text-slate-900">{person.name}</p>
                <p className="text-xs font-medium text-slate-500">Tap to view timeline</p>
            </div>
        </button>
    )
}
