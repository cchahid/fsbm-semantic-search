'use client'

import Image from 'next/image'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { Menu, X } from 'lucide-react'
import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'

const links = [
  { href: '/', label: 'Home' },
  { href: '/faculty-profiles', label: 'Faculty Profiles' },
  { href: '/#analytics', label: 'Analytics' },
  { href: '/#about', label: 'About' },
]

export function Navbar() {
  const pathname = usePathname()
  const router = useRouter()
  const [menuOpen, setMenuOpen] = useState(false)
  const [query, setQuery] = useState('')

  function handleSearch(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const trimmedQuery = query.trim()
    if (trimmedQuery) router.push(`/?query=${encodeURIComponent(trimmedQuery)}`)
  }

  return (
    <header className="relative sticky top-0 z-50 flex w-full items-center justify-between border-b border-slate-200/80 bg-white/90 px-6 py-3 shadow-sm backdrop-blur-md">
      <div className="flex-shrink-0 flex items-center">
        <Link href="/" aria-label="FSBM Semantic Scholar home">
          <Image
            src="/fsbm_logo.png"
            alt="FSBM official logo"
            width={220}
            height={80}
            className="h-12 w-auto object-contain"
            priority
          />
        </Link>
      </div>

        {pathname === '/' && (
          <form onSubmit={handleSearch} className="relative mx-8 hidden min-w-0 max-w-2xl flex-1 md:block" role="search">
            <SearchIcon />
            <Input
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              className="h-10 rounded-lg border-slate-300 bg-white/70 pl-10 pr-20 text-sm shadow-sm focus-visible:border-blue-600 focus-visible:ring-blue-600/20"
              placeholder="Search papers, topics, or authors..."
              aria-label="Search research papers"
            />
            <Button type="submit" size="sm" className="absolute right-1 top-1 h-8 bg-blue-700 px-3 hover:bg-blue-900">
              Search
            </Button>
          </form>
        )}

        <nav className="hidden items-center gap-7 text-sm font-medium lg:flex" aria-label="Primary navigation">
          {links.map((link) => {
            const isActive = link.href === '/' ? pathname === '/' : pathname === link.href
            return (
              <Link
                key={link.href}
                href={link.href}
                className={`relative py-2 transition-colors after:absolute after:inset-x-0 after:-bottom-1 after:h-0.5 after:origin-left after:scale-x-0 after:bg-blue-600 after:transition-transform hover:text-blue-700 hover:after:scale-x-100 ${
                  isActive ? 'text-blue-700 after:scale-x-100' : 'text-slate-600'
                }`}
              >
                {link.label}
              </Link>
            )
          })}
        </nav>

        <Button
          variant="ghost"
          size="icon"
          className="md:hidden"
          aria-label={menuOpen ? 'Close menu' : 'Open menu'}
          aria-expanded={menuOpen}
          onClick={() => setMenuOpen((open) => !open)}
        >
          {menuOpen ? <X /> : <Menu />}
        </Button>
      {menuOpen && (
        <nav className="absolute left-0 right-0 top-full border-t border-slate-200/80 bg-white/90 px-5 py-3 shadow-lg backdrop-blur-xl md:hidden" aria-label="Mobile navigation">
          <div className="mx-auto flex max-w-7xl flex-col gap-1">
            {links.map((link) => (
              <Link
                key={link.href}
                href={link.href}
                onClick={() => setMenuOpen(false)}
                className="rounded-lg px-3 py-3 text-sm font-medium text-slate-700 transition-colors hover:bg-blue-50 hover:text-blue-700"
              >
                {link.label}
              </Link>
            ))}
          </div>
        </nav>
      )}
    </header>
  )
}

function SearchIcon() {
  return <span className="pointer-events-none absolute left-3 top-1/2 z-10 -translate-y-1/2 text-slate-400">⌕</span>
}
