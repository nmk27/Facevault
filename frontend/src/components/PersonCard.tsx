import type { CSSProperties } from 'react'
import type { Person } from '../types'
import { SmartImage } from './SmartImage'

type PersonCardProps = {
    person: Person
    onClick: (person: Person) => void
    style?: CSSProperties
}

export function PersonCard({ person, onClick, style }: PersonCardProps) {
    return (
        <button
            type="button"
            style={style}
            onClick={() => onClick(person)}
            className="h-full w-full overflow-hidden rounded-md border border-slate-200 bg-white text-left"
        >
            {person.coverUrl ? (
                <SmartImage
                    src={person.coverUrl}
                    alt={person.name}
                    className="h-[75%] w-full object-cover"
                />
            ) : (
                <div className="h-[75%] w-full bg-slate-100" />
            )}
            <div className="space-y-0.5 px-2 py-2">
                <p className="truncate text-sm font-medium text-slate-900">{person.name}</p>
                <p className="text-xs text-slate-500">{person.faceCount} faces</p>
            </div>
        </button>
    )
}
