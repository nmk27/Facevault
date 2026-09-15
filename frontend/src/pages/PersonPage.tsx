import { ArrowLeft } from 'lucide-react'
import { Link, useParams } from 'react-router-dom'
import { PhotoGrid } from '../components/gallery/PhotoGrid'
import { PersonNameEditor } from '../components/people/PersonNameEditor'
import { SmartImage } from '../components/shared/SmartImage'
import { usePerson, useRenamePerson } from '../hooks/usePeople'

export function PersonPage() {
    const { personId } = useParams()
    const personQuery = usePerson(personId)
    const renameMutation = useRenamePerson(personId)

    if (personQuery.isError) {
        return (
            <div className="space-y-3">
                <p className="text-sm text-red-500">Failed to load this person.</p>
                <Link to="/people" className="text-sm text-neutral-500 underline">
                    Back to people
                </Link>
            </div>
        )
    }

    if (personQuery.isLoading) {
        return <p className="text-sm text-neutral-500">Loading...</p>
    }

    if (!personQuery.data) {
        return (
            <div className="space-y-3">
                <p className="text-sm text-neutral-500">Person not found.</p>
                <Link to="/people" className="text-sm text-neutral-500 underline">
                    Back to people
                </Link>
            </div>
        )
    }

    const { person, photos } = personQuery.data

    return (
        <section className="space-y-6">
            <Link
                to="/people"
                className="inline-flex items-center gap-1.5 text-sm font-medium text-neutral-500 hover:text-neutral-900 dark:hover:text-neutral-100"
            >
                <ArrowLeft className="h-4 w-4" />
                People
            </Link>

            <div className="flex items-center gap-4">
                <div className="h-20 w-20 shrink-0 overflow-hidden rounded-full bg-neutral-200 dark:bg-neutral-800">
                    {person.coverUrl && <SmartImage src={person.coverUrl} alt={person.name} className="h-full w-full object-cover" />}
                </div>
                <div>
                    <PersonNameEditor
                        name={person.name}
                        saving={renameMutation.isPending}
                        onSave={(name) => renameMutation.mutate(name)}
                    />
                    <p className="mt-1 text-sm text-neutral-500">
                        {person.faceCount} {person.faceCount === 1 ? 'photo' : 'photos'}
                    </p>
                </div>
            </div>

            <PhotoGrid photos={photos} />
        </section>
    )
}
