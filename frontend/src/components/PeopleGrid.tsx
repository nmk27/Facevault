import { useNavigate } from 'react-router-dom'
import type { Person } from '../types'
import { PersonCard } from './PersonCard'

type PeopleGridProps = {
    people: Person[]
}

export function PeopleGrid({ people }: PeopleGridProps) {
    const navigate = useNavigate()

    return (
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5">
            {people.map((person) => (
                <PersonCard
                    key={person.id}
                    person={person}
                    onClick={(selected) => navigate(`/people/${selected.id}`)}
                />
            ))}
        </div>
    )
}
