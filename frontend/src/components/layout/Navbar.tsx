import { Link, NavLink } from 'react-router-dom'
import { ThemeToggle } from '../ui/ThemeToggle'

const navItems = [
    { to: '/', label: 'Gallery' },
    { to: '/people', label: 'People' },
]

export function Navbar() {
    return (
        <header className="sticky top-0 z-20 border-b border-neutral-200/70 bg-white/70 backdrop-blur-xl dark:border-neutral-800/70 dark:bg-black/50">
            <div className="mx-auto flex h-14 w-full max-w-7xl items-center justify-between px-4 sm:px-6">
                <Link to="/" className="flex items-center gap-2 text-sm font-semibold tracking-tight text-neutral-900 dark:text-neutral-100">
                    <span className="flex h-7 w-7 items-center justify-center rounded-full bg-neutral-900 text-[11px] font-bold text-white dark:bg-white dark:text-neutral-900">
                        FV
                    </span>
                    <span>FaceVault</span>
                </Link>

                <div className="flex items-center gap-1">
                    <nav className="flex items-center gap-1">
                        {navItems.map((item) => (
                            <NavLink
                                key={item.to}
                                to={item.to}
                                end={item.to === '/'}
                                className={({ isActive }) =>
                                    `rounded-full px-3.5 py-1.5 text-sm font-medium transition ${isActive
                                        ? 'bg-neutral-900 text-white dark:bg-white dark:text-neutral-900'
                                        : 'text-neutral-600 hover:bg-neutral-900/5 dark:text-neutral-400 dark:hover:bg-white/10'
                                    }`
                                }
                            >
                                {item.label}
                            </NavLink>
                        ))}
                    </nav>
                    <ThemeToggle />
                </div>
            </div>
        </header>
    )
}
