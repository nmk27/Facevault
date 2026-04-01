import { useMemo, useState } from 'react'
import { useDropzone } from 'react-dropzone'

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
        <section className="space-y-3 rounded-lg border border-slate-200 bg-white p-4">
            <div
                {...getRootProps()}
                className={`cursor-pointer rounded-md border border-dashed p-6 text-center text-sm ${isDragActive ? 'border-slate-900 bg-slate-50' : 'border-slate-300 text-slate-600'
                    }`}
            >
                <input {...getInputProps()} />
                {isDragActive ? 'Drop images here' : 'Drag and drop photos, or click to browse'}
            </div>

            <div className="flex flex-wrap items-center gap-3">
                <button
                    type="button"
                    onClick={handleUpload}
                    disabled={acceptedFiles.length === 0}
                    className="rounded-md bg-slate-900 px-3 py-2 text-sm text-white disabled:cursor-not-allowed disabled:bg-slate-300"
                >
                    Upload
                </button>

                <span className="text-xs text-slate-500">{acceptedFiles.length} file(s) selected</span>
            </div>

            {progress > 0 && progress < 100 && (
                <div className="h-1.5 w-full overflow-hidden rounded bg-slate-200">
                    <div className="h-full bg-slate-900" style={{ width: `${progress}%` }} />
                </div>
            )}

            {message && <p className="text-xs text-slate-600">{message}</p>}
            {rejectionMessage && <p className="text-xs text-red-600">{rejectionMessage}</p>}
        </section>
    )
}
