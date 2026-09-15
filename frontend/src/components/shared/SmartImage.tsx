import { useEffect, useMemo, useRef, useState } from 'react'

type SmartImageProps = {
    src: string
    alt: string
    className?: string
    fallbackSrc?: string
    style?: React.CSSProperties
    onLoad?: React.ReactEventHandler<HTMLImageElement>
}

function isHeicLike(value: string) {
    const lower = value.toLowerCase()
    return lower.includes('.heic') || lower.includes('.heif')
}

export function SmartImage({ src, alt, className, fallbackSrc, style, onLoad }: SmartImageProps) {
    const [currentSrc, setCurrentSrc] = useState(src)
    const objectUrlRef = useRef<string | null>(null)

    const canTryHeicConversion = useMemo(() => isHeicLike(currentSrc), [currentSrc])

    useEffect(() => {
        setCurrentSrc(src)
    }, [src])

    useEffect(() => {
        return () => {
            if (objectUrlRef.current) {
                URL.revokeObjectURL(objectUrlRef.current)
            }
        }
    }, [])

    async function handleError() {
        if (canTryHeicConversion) {
            try {
                const response = await fetch(currentSrc)
                if (!response.ok) {
                    throw new Error('Failed to fetch HEIC')
                }

                const blob = await response.blob()
                const heic2anyModule = await import('heic2any')
                const convert = heic2anyModule.default as unknown as (args: {
                    blob: Blob
                    toType: string
                    quality: number
                }) => Promise<Blob | Blob[]>

                const converted = await convert({
                    blob,
                    toType: 'image/jpeg',
                    quality: 0.92,
                })

                const convertedBlob = Array.isArray(converted) ? converted[0] : converted
                const objectUrl = URL.createObjectURL(convertedBlob)

                if (objectUrlRef.current) {
                    URL.revokeObjectURL(objectUrlRef.current)
                }

                objectUrlRef.current = objectUrl
                setCurrentSrc(objectUrl)
                return
            } catch {
                // Fallback to thumbnail path below.
            }
        }

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
