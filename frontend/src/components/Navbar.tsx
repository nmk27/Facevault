import { Link, NavLink } from 'react-router-dom'

const navItems = [
    { to: '/', label: 'Gallery' },
    { to: '/people', label: 'People' },
]

export function Navbar() {
    return (
        <header className="sticky top-0 z-20 border-b border-white/60 bg-white/70 backdrop-blur-xl">
            <div className="mx-auto flex h-16 w-full max-w-7xl items-center justify-between px-4 sm:px-6">
                <Link to="/" className="flex items-center gap-3 text-sm font-semibold tracking-tight text-slate-900">
                    <span className="flex h-8 w-8 items-center justify-center rounded-xl bg-slate-900 text-xs font-bold text-white shadow-sm">
                        FV
                    </span>
                    <span className="flex flex-col leading-tight">
                        <span>FaceVault</span>
                        <span className="text-[11px] font-medium text-slate-500">Private gallery</span>
                    </span>
                </Link>

                <nav className="flex items-center gap-2">
                    {navItems.map((item) => (
                        <NavLink
                            key={item.to}
                            to={item.to}
                            className={({ isActive }) =>
                                `rounded-full px-3.5 py-1.5 text-sm font-medium transition ${isActive
                                    ? 'bg-slate-900 text-white shadow-sm'
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
