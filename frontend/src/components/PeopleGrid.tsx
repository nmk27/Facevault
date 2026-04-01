import { useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import { Grid } from 'react-window'
import type { CellComponentProps } from 'react-window'
import type { Person } from '../types'
import { PersonCard } from './PersonCard'

type PeopleGridProps = {
    people: Person[]
}

type PeopleCellProps = {
    people: Person[]
    columns: number
    onPersonClick: (person: Person) => void
}

function PeopleCell({
    columnIndex,
    rowIndex,
    style,
    people,
    columns,
    onPersonClick,
}: CellComponentProps<PeopleCellProps>) {
    const index = rowIndex * columns + columnIndex
    const person = people[index]

    if (!person) {
        return null
    }

    return (
        <div style={style} className="p-1.5">
            <PersonCard person={person} onClick={onPersonClick} />
        </div>
    )
}

function useColumns() {
    const width = window.innerWidth
    if (width < 640) {
        return 2
    }
    if (width < 1024) {
        return 4
    }
    return 5
}

export function PeopleGrid({ people }: PeopleGridProps) {
    const navigate = useNavigate()
    const columns = useColumns()
    const cardHeight = 210
    const viewportWidth = Math.max(360, window.innerWidth - 48)
    const cardWidth = Math.floor(viewportWidth / columns)
    const rowCount = useMemo(() => Math.ceil(people.length / columns), [people.length, columns])

    return (
        <Grid
            className="!overflow-x-hidden"
            cellComponent={PeopleCell}
            cellProps={{
                people,
                columns,
                onPersonClick: (selected: Person) => navigate(`/people/${selected.id}`),
            }}
            columnCount={columns}
            columnWidth={cardWidth}
            defaultHeight={420}
            defaultWidth={viewportWidth}
            rowCount={rowCount}
            rowHeight={cardHeight}
            style={{
                width: viewportWidth,
                height: Math.min(window.innerHeight - 220, Math.max(280, rowCount * cardHeight)),
            }}
        />
    )
}
