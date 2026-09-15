import { useNavigate } from 'react-router-dom'
import type { Person } from '../../types'
import { PersonCard } from './PersonCard'

type PeopleGridProps = {
    people: Person[]
}

export function PeopleGrid({ people }: PeopleGridProps) {
    const navigate = useNavigate()

    return (
        <div className="grid grid-cols-3 gap-2 sm:grid-cols-4 md:grid-cols-6 lg:grid-cols-8">
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
