import { useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import { Grid } from 'react-window'
import type { CellComponentProps } from 'react-window'
import type { Photo } from '../types'
import { PhotoCard } from './PhotoCard'

type PhotoGridProps = {
    photos: Photo[]
}

type PhotoCellProps = {
    photos: Photo[]
    columns: number
    onPhotoClick: (photo: Photo) => void
}

function PhotoCell({
    columnIndex,
    rowIndex,
    style,
    photos,
    columns,
    onPhotoClick,
}: CellComponentProps<PhotoCellProps>) {
    const index = rowIndex * columns + columnIndex
    const photo = photos[index]

    if (!photo) {
        return null
    }

    return (
        <div style={style} className="p-1.5">
            <PhotoCard photo={photo} onClick={onPhotoClick} />
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
    return 6
}

export function PhotoGrid({ photos }: PhotoGridProps) {
    const navigate = useNavigate()
    const columns = useColumns()
    const cardHeight = 220
    const viewportWidth = Math.max(360, window.innerWidth - 48)
    const cardWidth = Math.floor(viewportWidth / columns)

    const rowCount = useMemo(() => Math.ceil(photos.length / columns), [photos.length, columns])

    return (
        <Grid
            className="!overflow-x-hidden"
            cellComponent={PhotoCell}
            cellProps={{
                photos,
                columns,
                onPhotoClick: (selected: Photo) => navigate(`/photos/${selected.id}`),
            }}
            columnCount={columns}
            columnWidth={cardWidth}
            defaultHeight={480}
            defaultWidth={viewportWidth}
            rowCount={rowCount}
            rowHeight={cardHeight}
            style={{
                width: viewportWidth,
                height: Math.min(window.innerHeight - 260, Math.max(280, rowCount * cardHeight)),
            }}
        />
    )
}
