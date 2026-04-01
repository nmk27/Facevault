import { Route, Routes } from 'react-router-dom'
import { Navbar } from './components/Navbar'
import { GalleryPage } from './pages/GalleryPage'
import { PeoplePage } from './pages/PeoplePage'
import { PersonPage } from './pages/PersonPage'
import { PhotoPage } from './pages/PhotoPage'

export default function App() {
    return (
        <div className="relative min-h-screen overflow-hidden bg-slate-50">
            <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_top_left,_rgba(251,191,36,0.16),_transparent_38%),radial-gradient(circle_at_top_right,_rgba(148,163,184,0.18),_transparent_34%),linear-gradient(to_bottom,_rgba(248,250,252,0.96),_rgba(248,250,252,1))]" />
            <div className="pointer-events-none absolute inset-x-0 top-24 -z-0 mx-auto h-[28rem] w-[28rem] rounded-full bg-amber-200/20 blur-3xl" />
            <Navbar />
            <main className="relative z-10 mx-auto w-full max-w-7xl p-4 sm:p-6">
                <Routes>
                    <Route path="/" element={<GalleryPage />} />
                    <Route path="/photos/:photoId" element={<PhotoPage />} />
                    <Route path="/people" element={<PeoplePage />} />
                    <Route path="/people/:personId" element={<PersonPage />} />
                </Routes>
            </main>
        </div>
    )
}
