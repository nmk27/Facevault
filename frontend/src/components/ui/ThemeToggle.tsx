import { Moon, Sun } from 'lucide-react'
import { useTheme } from '../../theme/ThemeProvider'

export function ThemeToggle() {
    const { theme, toggleTheme } = useTheme()

    return (
        <button
            type="button"
            onClick={toggleTheme}
            aria-label={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
            className="flex h-9 w-9 items-center justify-center rounded-full text-neutral-600 transition hover:bg-neutral-900/5 dark:text-neutral-300 dark:hover:bg-white/10"
        >
            {theme === 'dark' ? <Sun className="h-[18px] w-[18px]" /> : <Moon className="h-[18px] w-[18px]" />}
        </button>
    )
}
