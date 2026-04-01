import { Link, useParams } from 'react-router-dom'
import { PhotoGrid } from '../components/PhotoGrid'
import { usePerson } from '../hooks/usePeople'

export function PersonPage() {
    const { personId } = useParams()
    const personQuery = usePerson(personId)

    if (personQuery.isError) {
        return (
            <div className="space-y-3">
                <p className="text-sm text-red-600">
                    Failed to fetch person details from backend endpoint /faces/people/{personId}/.
                </p>
                <Link to="/people" className="text-sm text-slate-900 underline">
                    Back to people
                </Link>
            </div>
        )
    }

    if (personQuery.isLoading) {
        return <p className="text-sm text-slate-500">Loading person...</p>
    }

    if (!personQuery.data) {
        return (
            <div className="space-y-3">
                <p className="text-sm text-slate-500">Person not found.</p>
                <Link to="/people" className="text-sm text-slate-900 underline">
                    Back to people
                </Link>
            </div>
        )
    }

    const { person, photos } = personQuery.data

    return (
        <section className="space-y-4">
            <Link to="/people" className="text-sm text-slate-600 underline">
                Back to people
            </Link>

            <div className="rounded-lg border border-slate-200 bg-white p-4">
                <h1 className="text-base font-semibold text-slate-900">{person.name}</h1>
                <p className="mt-1 text-xs text-slate-500">
                    Appearances: {person.faceCount} · Avg confidence: {(person.averageConfidence * 100).toFixed(1)}%
                </p>
            </div>

            <div className="rounded-lg border border-slate-200 bg-white p-4">
                <PhotoGrid photos={photos} />
            </div>
        </section>
    )
}
