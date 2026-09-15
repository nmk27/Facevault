import { useState, type KeyboardEvent } from 'react'
import { Pencil } from 'lucide-react'

type PersonNameEditorProps = {
    name: string
    onSave: (name: string) => void
    saving?: boolean
}

export function PersonNameEditor({ name, onSave, saving }: PersonNameEditorProps) {
    const [isEditing, setIsEditing] = useState(false)
    const [draft, setDraft] = useState(name)

    function commit() {
        const trimmed = draft.trim()
        setIsEditing(false)
        if (trimmed && trimmed !== name) {
            onSave(trimmed)
        } else {
            setDraft(name)
        }
    }

    function handleKeyDown(event: KeyboardEvent<HTMLInputElement>) {
        if (event.key === 'Enter') {
            event.currentTarget.blur()
        } else if (event.key === 'Escape') {
            setDraft(name)
            setIsEditing(false)
        }
    }

    if (isEditing) {
        return (
            <input
                autoFocus
                value={draft}
                disabled={saving}
                onChange={(event) => setDraft(event.target.value)}
                onBlur={commit}
                onKeyDown={handleKeyDown}
                maxLength={100}
                className="rounded-lg border border-neutral-300 bg-white px-2 py-1 text-xl font-semibold text-neutral-900 outline-none focus:border-sky-400 dark:border-neutral-700 dark:bg-neutral-900 dark:text-neutral-100"
            />
        )
    }

    return (
        <button
            type="button"
            onClick={() => {
                setDraft(name)
                setIsEditing(true)
            }}
            className="group flex items-center gap-1.5 text-xl font-semibold text-neutral-900 dark:text-neutral-100"
        >
            {name}
            <Pencil className="h-3.5 w-3.5 text-neutral-400 opacity-0 transition group-hover:opacity-100" />
        </button>
    )
}
