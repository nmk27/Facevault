import type { FaceBox } from '../../types'

type FaceOverlayProps = {
    faces: FaceBox[]
    imageWidth?: number
    imageHeight?: number
    renderedWidth?: number
    renderedHeight?: number
}

export function FaceOverlay({
    faces,
    imageWidth,
    imageHeight,
    renderedWidth,
    renderedHeight,
}: FaceOverlayProps) {
    return (
        <div
            className="pointer-events-none absolute left-0 top-0 z-10"
            style={{ width: renderedWidth || '100%', height: renderedHeight || '100%' }}
        >
            {faces.map((face) => {
                const color = face.personId ? 'border-sky-400/90' : 'border-white/60'

                const sourceWidth = imageWidth ?? renderedWidth ?? 1
                const sourceHeight = imageHeight ?? renderedHeight ?? 1
                const targetWidth = renderedWidth ?? sourceWidth
                const targetHeight = renderedHeight ?? sourceHeight

                const rawLeft = face.x <= 1 ? face.x * targetWidth : (face.x / sourceWidth) * targetWidth
                const rawTop = face.y <= 1 ? face.y * targetHeight : (face.y / sourceHeight) * targetHeight
                const rawWidth =
                    face.width <= 1 ? face.width * targetWidth : (face.width / sourceWidth) * targetWidth
                const rawHeight =
                    face.height <= 1 ? face.height * targetHeight : (face.height / sourceHeight) * targetHeight

                const left = Math.max(0, Math.min(rawLeft, targetWidth))
                const top = Math.max(0, Math.min(rawTop, targetHeight))
                const width = Math.max(1, Math.min(rawWidth, targetWidth - left))
                const height = Math.max(1, Math.min(rawHeight, targetHeight - top))

                return (
                    <div
                        key={face.id}
                        className={`absolute rounded-md border ${color} bg-transparent`}
                        style={{ left, top, width, height }}
                    />
                )
            })}
        </div>
    )
}
