import { useEffect, useState } from 'react'

type SmartImageProps = {
    src: string
    alt: string
    className?: string
    fallbackSrc?: string
    style?: React.CSSProperties
    onLoad?: React.ReactEventHandler<HTMLImageElement>
}

export function SmartImage({ src, alt, className, fallbackSrc, style, onLoad }: SmartImageProps) {
    const [currentSrc, setCurrentSrc] = useState(src)

    useEffect(() => {
        setCurrentSrc(src)
    }, [src])

    function handleError() {
        if (fallbackSrc && currentSrc !== fallbackSrc) {
            setCurrentSrc(fallbackSrc)
        }
    }

    return (
        <img
            src={currentSrc}
            alt={alt}
            style={style}
            className={className}
            onError={handleError}
            onLoad={onLoad}
        />
    )
}
