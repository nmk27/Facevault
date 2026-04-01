import { Link, NavLink } from 'react-router-dom'

const navItems = [
    { to: '/', label: 'Gallery' },
    { to: '/people', label: 'People' },
]

export function Navbar() {
    return (
        <header className="sticky top-0 z-20 border-b border-slate-200 bg-white/90 backdrop-blur">
            <div className="mx-auto flex h-14 w-full max-w-7xl items-center justify-between px-4">
                <Link to="/" className="text-sm font-semibold tracking-tight text-slate-900">
                    FaceVault
                </Link>

                <nav className="flex items-center gap-2">
                    {navItems.map((item) => (
                        <NavLink
                            key={item.to}
                            to={item.to}
                            className={({ isActive }) =>
                                `rounded-md px-3 py-1.5 text-sm ${isActive
                                    ? 'bg-slate-900 text-white'
                                    : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900'
                                }`
                            }
                        >
                            {item.label}
                        </NavLink>
                    ))}
                </nav>
            </div>
        </header>
    )
}
