import { useMemo, useState } from 'react'
import { useDropzone } from 'react-dropzone'
import { UploadCloud } from 'lucide-react'

type UploadDropzoneProps = {
    onUpload: (files: readonly File[], onProgress: (progress: number) => void) => Promise<void>
}

const MAX_FILE_SIZE = 10 * 1024 * 1024

export function UploadDropzone({ onUpload }: UploadDropzoneProps) {
    const [progress, setProgress] = useState(0)
    const [message, setMessage] = useState('')

    const { getRootProps, getInputProps, isDragActive, acceptedFiles, fileRejections } = useDropzone({
        accept: {
            'image/*': [],
            'image/heic': ['.heic'],
            'image/heif': ['.heif'],
        },
        maxSize: MAX_FILE_SIZE,
        multiple: true,
    })

    const rejectionMessage = useMemo(() => {
        if (fileRejections.length === 0) {
            return ''
        }
        return 'Invalid file detected. Only images under 10MB are allowed.'
    }, [fileRejections.length])

    async function handleUpload() {
        if (acceptedFiles.length === 0) {
            return
        }

        setMessage('Uploading...')
        setProgress(0)

        try {
            await onUpload(acceptedFiles, setProgress)
            setMessage(`Uploaded ${acceptedFiles.length} file(s).`)
        } catch {
            setMessage('Upload failed. Please retry.')
        }
    }

    return (
        <section className="space-y-3">
            <div
                {...getRootProps()}
                className={`flex cursor-pointer items-center gap-3 rounded-xl border p-4 text-sm transition ${
                    isDragActive
                        ? 'border-sky-400 bg-sky-400/5 text-neutral-900 dark:text-neutral-100'
                        : 'border-neutral-200 text-neutral-500 hover:border-neutral-300 dark:border-neutral-800 dark:text-neutral-400 dark:hover:border-neutral-700'
                }`}
            >
                <input {...getInputProps()} />
                <UploadCloud className="h-4 w-4 shrink-0" />
                <div>
                    <p className="font-medium text-neutral-900 dark:text-neutral-100">
                        {isDragActive ? 'Drop images here' : 'Drag and drop photos, or click to browse'}
                    </p>
                    <p className="mt-0.5 text-xs text-neutral-500">JPG, PNG, HEIC, HEIF · up to 10MB each</p>
                </div>
            </div>

            {acceptedFiles.length > 0 && (
                <div className="flex flex-wrap items-center gap-3">
                    <button
                        type="button"
                        onClick={handleUpload}
                        className="rounded-full bg-neutral-900 px-4 py-1.5 text-sm font-medium text-white transition hover:bg-neutral-700 dark:bg-white dark:text-neutral-900 dark:hover:bg-neutral-200"
                    >
                        Upload {acceptedFiles.length} file{acceptedFiles.length === 1 ? '' : 's'}
                    </button>

                    {progress > 0 && progress < 100 && (
                        <div className="h-1 w-32 overflow-hidden rounded bg-neutral-200 dark:bg-neutral-800">
                            <div className="h-full bg-neutral-900 dark:bg-white" style={{ width: `${progress}%` }} />
                        </div>
                    )}
                </div>
            )}

            {message && <p className="text-xs font-medium text-neutral-500">{message}</p>}
            {rejectionMessage && <p className="text-xs text-red-500">{rejectionMessage}</p>}
        </section>
    )
}
