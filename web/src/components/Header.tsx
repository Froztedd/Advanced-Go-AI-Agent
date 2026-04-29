import { Link } from 'react-router-dom'

export default function Header() {
  return (
    <header className="border-b border-ink-700/60 backdrop-blur supports-[backdrop-filter]:bg-ink-900/40">
      <div className="max-w-6xl mx-auto px-6 h-16 flex items-center justify-between">
        <Link to="/" className="flex items-center gap-3 group">
          <span className="relative w-7 h-7">
            <span className="absolute inset-0 rounded-full bg-gradient-to-br from-wood-300 to-wood-600 shadow-[inset_-2px_-2px_4px_rgba(0,0,0,0.4),inset_2px_2px_3px_rgba(255,255,255,0.2)]" />
            <span className="absolute inset-1 rounded-full bg-gradient-to-br from-ink-700 to-ink-900 shadow-stone" />
          </span>
          <span className="font-display text-xl tracking-tight text-wood-100">
            go<span className="text-wood-300">·</span>arena
          </span>
        </Link>
        <nav className="flex items-center gap-6 text-sm text-ink-300">
          <Link to="/setup" className="hover:text-wood-200 transition-colors">
            Play
          </Link>
          <a
            href="https://github.com"
            target="_blank"
            rel="noreferrer"
            className="hover:text-wood-200 transition-colors"
          >
            GitHub
          </a>
        </nav>
      </div>
    </header>
  )
}
