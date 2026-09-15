import { Route, Routes } from 'react-router-dom'
import { Navbar } from './components/layout/Navbar'
import { GalleryPage } from './pages/GalleryPage'
import { PeoplePage } from './pages/PeoplePage'
import { PersonPage } from './pages/PersonPage'
import { PhotoPage } from './pages/PhotoPage'

export default function App() {
    return (
        <div className="min-h-screen bg-white dark:bg-black">
            <Routes>
                <Route path="/photos/:photoId" element={<PhotoPage />} />
                <Route
                    path="*"
                    element={
                        <>
                            <Navbar />
                            <main className="mx-auto w-full max-w-7xl p-3 sm:p-5">
                                <Routes>
                                    <Route path="/" element={<GalleryPage />} />
                                    <Route path="/people" element={<PeoplePage />} />
                                    <Route path="/people/:personId" element={<PersonPage />} />
                                </Routes>
                            </main>
                        </>
                    }
                />
            </Routes>
        </div>
    )
}
