'use client'

import Image from 'next/image'
import { useEffect, useMemo, useState } from 'react'
import type { FormEvent } from 'react'
import {
  BookOpen,
  ChevronDown,
  Download,
  Filter,
  Menu,
  Search,
  SlidersHorizontal,
  TrendingUp,
  UserRound,
} from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Checkbox } from '@/components/ui/checkbox'
import { Input } from '@/components/ui/input'
import { Progress } from '@/components/ui/progress'
import { Separator } from '@/components/ui/separator'
import { Slider } from '@/components/ui/slider'

type SearchResult = {
  id: string
  title: string
  author: string
  year: string
  citations: number
  abstract: string
  match_score: number
}

type BackendSearchResult = {
  id?: string
  article_id?: string
  title?: string
  authors?: string[] | string
  author_display?: string
  year?: string | number
  citations?: number | string
  match_score?: number
  distance?: number
  metadata?: Record<string, unknown>
  abstract?: string
}

type FacultyProfile = {
  id: string
  name: string
  department: string
  affiliation: string
  citations_total: number
  h_index: number
  i10_index: number
  publications_count: number
  top_publication?: string
  top_publication_citations?: number
}

type ActiveView = 'home' | 'faculty'

function formatNumber(value: number) {
  return new Intl.NumberFormat('en-US').format(value)
}

function PaperCard({ result, index }: { result: SearchResult; index: number }) {
  const [expanded, setExpanded] = useState(false)

  return (
    <Card
      className="motion-fade-up border border-[#d4deeb] bg-white shadow-[0_8px_24px_rgba(11,35,65,0.08)] transition-all duration-300 hover:-translate-y-0.5 hover:scale-[1.01] hover:border-[#2f76ab]/45 hover:shadow-[0_20px_40px_rgba(12,57,97,0.14)]"
      style={{ animationDelay: `${80 + index * 70}ms` }}
    >
      <CardContent className="p-5 sm:p-6">
        <div className="flex items-start justify-between gap-4">
          <div className="min-w-0">
            <h3 className="font-serif text-lg font-semibold leading-snug text-[#0b2341] sm:text-xl">{result.title}</h3>
            <p className="mt-2 flex items-center gap-2 text-sm text-slate-600">
              <UserRound className="size-4 text-[#1a659b]" />
              {result.author}
            </p>
          </div>
          <Badge className="shrink-0 border-[#8ec0e4] bg-[#eff7fd] text-[#0f5f9a]">{result.match_score}% match</Badge>
        </div>
        <div className="mt-4 flex flex-wrap gap-2">
          <Badge variant="outline" className="border-[#d3e1ef] font-normal text-[#1b3653]">{result.year}</Badge>
          <Badge variant="outline" className="border-[#d3e1ef] font-normal text-[#1b3653]">{result.citations} citations</Badge>
        </div>
        <p className={`mt-4 text-sm leading-6 text-slate-600 ${expanded ? '' : 'line-clamp-3'}`}>{result.abstract}</p>
        <button
          onClick={() => setExpanded((prev) => !prev)}
          className="mt-1 inline-flex items-center gap-1 text-sm font-medium text-[#0f5f9a] hover:text-[#0b2341]"
        >
          {expanded ? 'Show less' : 'Read more'}
          <ChevronDown className={`size-4 transition-transform ${expanded ? 'rotate-180' : ''}`} />
        </button>
        <Separator className="my-5 bg-[#dbe6f1]" />
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <Button variant="outline" size="sm" className="w-fit border-[#0b2341]/20 text-[#0b2341] hover:bg-[#eff4f9]">
            <Download data-icon="inline-start" /> View PDF
          </Button>
          <div className="flex min-w-52 flex-1 items-center gap-3 sm:max-w-64">
            <span className="whitespace-nowrap text-xs font-medium text-slate-500">Semantic match</span>
            <Progress value={result.match_score} className="h-2 bg-[#e6edf5] [&>div]:bg-[#1a659b]" />
            <span className="text-sm font-semibold text-[#0b2341]">{result.match_score}%</span>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

function Filters() {
  return (
    <Card className="border border-[#d4deeb] bg-white shadow-[0_6px_18px_rgba(11,35,65,0.08)]">
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center gap-2 text-base text-[#0b2341]">
          <SlidersHorizontal className="size-4 text-[#1a659b]" />
          Refine results
        </CardTitle>
      </CardHeader>
      <CardContent className="flex flex-col gap-6">
        <fieldset className="flex flex-col gap-3">
          <legend className="mb-1 text-sm font-semibold text-[#0b2341]">Publication year</legend>
          {['2020 - 2024', '2015 - 2019', 'Before 2015'].map((label, index) => (
            <label key={label} className="flex items-center gap-3 text-sm text-slate-600">
              <Checkbox defaultChecked={index === 0} />
              {label}
            </label>
          ))}
        </fieldset>
        <Separator />
        <fieldset className="flex flex-col gap-3">
          <legend className="mb-1 text-sm font-semibold text-[#0b2341]">Department</legend>
          {['Computer Science', 'Mathematics', 'Data Science'].map((label, index) => (
            <label key={label} className="flex items-center gap-3 text-sm text-slate-600">
              <Checkbox defaultChecked={index === 0} />
              {label}
            </label>
          ))}
        </fieldset>
        <Separator />
        <div className="flex flex-col gap-3">
          <div className="flex justify-between">
            <span className="text-sm font-semibold text-[#0b2341]">Minimum citations</span>
            <span className="text-sm font-semibold text-[#1a659b]">20+</span>
          </div>
          <Slider defaultValue={[20]} max={200} step={10} />
        </div>
        <Button variant="outline" className="border-slate-200 text-slate-600">Clear all filters</Button>
      </CardContent>
    </Card>
  )
}

function FacultyProfileCard({ profile, index }: { profile: FacultyProfile; index: number }) {
  const initials = useMemo(() => {
    const words = profile.name.split(' ').filter(Boolean)
    if (!words.length) return 'FS'
    return words.slice(0, 2).map((part) => part[0]?.toUpperCase() ?? '').join('')
  }, [profile.name])

  return (
    <Card
      className="motion-fade-up overflow-hidden border border-[#d4e3f1] bg-white shadow-[0_10px_30px_rgba(9,40,75,0.08)] transition-all duration-300 hover:-translate-y-0.5 hover:scale-[1.01] hover:shadow-[0_22px_42px_rgba(10,47,85,0.15)]"
      style={{ animationDelay: `${70 + index * 50}ms` }}
    >
      <div className="h-1.5 bg-gradient-to-r from-[#0f4e80] via-[#1d6fa7] to-[#6cb2e2]" />
      <CardContent className="p-5">
        <div className="flex items-start gap-4">
          <div className="flex size-12 shrink-0 items-center justify-center rounded-lg bg-[#0f4e80] text-sm font-semibold text-white shadow-[0_6px_18px_rgba(15,78,128,0.4)]">
            {initials}
          </div>
          <div className="min-w-0">
            <h3 className="text-lg font-semibold text-[#0b2341]">{profile.name}</h3>
            <p className="mt-1 text-sm font-medium text-[#1a659b]">{profile.department}</p>
            <p className="mt-1 line-clamp-2 text-xs leading-5 text-slate-500">{profile.affiliation}</p>
          </div>
        </div>

        <div className="mt-5 grid grid-cols-3 gap-2">
          <div className="rounded-lg border border-[#d4e3f1] bg-[#f5f9fd] px-2 py-3 text-center">
            <p className="text-base font-semibold text-[#0b2341]">{formatNumber(profile.citations_total)}</p>
            <p className="text-[11px] text-slate-500">citations</p>
          </div>
          <div className="rounded-lg border border-[#d4e3f1] bg-[#f5f9fd] px-2 py-3 text-center">
            <p className="text-base font-semibold text-[#0b2341]">{profile.h_index}</p>
            <p className="text-[11px] text-slate-500">h-index</p>
          </div>
          <div className="rounded-lg border border-[#d4e3f1] bg-[#f5f9fd] px-2 py-3 text-center">
            <p className="text-base font-semibold text-[#0b2341]">{profile.i10_index}</p>
            <p className="text-[11px] text-slate-500">i10-index</p>
          </div>
        </div>

        <div className="mt-4 flex items-center justify-between rounded-lg border border-[#d6e4f0] bg-[#f9fcff] px-3 py-2">
          <span className="inline-flex items-center gap-1.5 text-xs font-medium text-[#0f5f9a]">
            <TrendingUp className="size-3.5" />
            Publications
          </span>
          <span className="text-sm font-semibold text-[#0b2341]">{profile.publications_count}</span>
        </div>

        {profile.top_publication && (
          <div className="mt-4 rounded-lg border border-[#d6e4f0] bg-white px-3 py-2">
            <p className="text-[11px] font-semibold uppercase tracking-wide text-slate-500">Top publication</p>
            <p className="mt-1 line-clamp-2 text-xs leading-5 text-[#193c5e]">{profile.top_publication}</p>
          </div>
        )}
      </CardContent>
    </Card>
  )
}

export default function Page() {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState<SearchResult[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [mobileFilters, setMobileFilters] = useState(false)
  const [activeView, setActiveView] = useState<ActiveView>('home')
  const [profiles, setProfiles] = useState<FacultyProfile[]>([])
  const [profilesLoading, setProfilesLoading] = useState(false)
  const [profilesError, setProfilesError] = useState<string | null>(null)

  async function handleSearch(e: FormEvent) {
    e.preventDefault()
    if (!query.trim()) return

    setIsLoading(true)
    setActiveView('home')

    try {
      const params = new URLSearchParams({ query: query.trim() })
      const response = await fetch(`http://127.0.0.1:8000/search?${params.toString()}`)
      if (!response.ok) {
        throw new Error(`Server error: ${response.status}`)
      }
      const data = await response.json()
      const normalizedResults: SearchResult[] = (data.results || []).map((item: BackendSearchResult, index: number) => {
        const metadata = item.metadata || {}
        const distance = typeof item.distance === 'number' ? item.distance : 1
        const scoreFromDistance = Math.max(0, Math.min(100, Math.round((1 - distance) * 100)))
        const score = typeof item.match_score === 'number'
          ? Math.max(0, Math.min(100, Math.round(item.match_score)))
          : scoreFromDistance

        const rawAuthor = item.author_display ?? item.authors ?? metadata['author'] ?? metadata['authors'] ?? metadata['auteurs'] ?? metadata['nom_complet']
        const author = Array.isArray(rawAuthor)
          ? rawAuthor.join(', ')
          : typeof rawAuthor === 'string'
            ? rawAuthor
            : 'Unknown author'

        const rawYear = item.year ?? metadata['year'] ?? metadata['publication_year'] ?? metadata['date_publication']
        const year = rawYear ? String(rawYear) : 'N/A'

        const rawCitations = item.citations ?? metadata['citations'] ?? metadata['citation_count'] ?? 0
        const numericCitations = typeof rawCitations === 'number' ? rawCitations : Number(rawCitations)
        const citations = Number.isFinite(numericCitations) ? numericCitations : 0

        return {
          id: item.id || item.article_id || `result-${index}`,
          title: String(item.title ?? metadata['title'] ?? metadata['titre'] ?? item.article_id ?? 'Untitled'),
          author,
          year,
          citations,
          abstract: item.abstract || 'No abstract available.',
          match_score: score,
        }
      })
      setResults(normalizedResults)
    } catch (err) {
      console.error('Search request failed:', err)
      alert('Cannot reach backend server. Make sure FastAPI is running.')
    } finally {
      setIsLoading(false)
    }
  }

  async function fetchProfiles() {
    setProfilesLoading(true)
    setProfilesError(null)
    try {
      const response = await fetch('http://127.0.0.1:8000/faculty-profiles')
      if (!response.ok) {
        throw new Error(`Server error: ${response.status}`)
      }
      const data = await response.json()
      setProfiles(Array.isArray(data.profiles) ? data.profiles : [])
    } catch (err) {
      console.error('Faculty profiles request failed:', err)
      setProfilesError('Cannot load faculty profiles right now.')
    } finally {
      setProfilesLoading(false)
    }
  }

  useEffect(() => {
    if (activeView === 'faculty' && profiles.length === 0 && !profilesLoading && !profilesError) {
      void fetchProfiles()
    }
  }, [activeView, profiles.length, profilesLoading, profilesError])

  return (
    <div className="min-h-screen bg-[#f4f8fc] text-slate-800">
      <header className="sticky top-0 z-20 border-b border-[#dbe6f1] bg-white/95 backdrop-blur">
        <div className="mx-auto flex h-20 max-w-7xl items-center justify-between px-5 lg:px-8">
          <div className="flex items-center gap-3">
            <div className="relative size-11 overflow-hidden rounded-lg border border-[#d7e4ef] bg-white shadow-sm">
              <Image src="/fsbm_logo.png" alt="FSBM official logo" fill className="object-contain p-1" sizes="44px" priority />
            </div>
            <div>
              <p className="text-sm font-bold tracking-tight text-[#0b2341]">FSBM</p>
              <p className="hidden text-[11px] text-slate-500 sm:block">Universite Hassan II</p>
            </div>
          </div>

          <nav className="hidden items-center gap-7 text-sm font-medium md:flex">
            <button
              onClick={() => setActiveView('home')}
              className={`transition-colors ${activeView === 'home' ? 'text-[#0f5f9a]' : 'text-slate-600 hover:text-[#0f5f9a]'}`}
            >
              Home
            </button>
            <button
              onClick={() => setActiveView('faculty')}
              className={`transition-colors ${activeView === 'faculty' ? 'text-[#0f5f9a]' : 'text-slate-600 hover:text-[#0f5f9a]'}`}
            >
              Faculty Profiles
            </button>
            <a className="text-slate-600 hover:text-[#0f5f9a]" href="#analytics">Analytics</a>
            <a className="text-slate-600 hover:text-[#0f5f9a]" href="#about">About</a>
          </nav>

          <Button variant="ghost" size="icon" className="md:hidden" aria-label="Open menu">
            <Menu />
          </Button>
        </div>
      </header>

      <main className="mx-auto max-w-7xl px-5 pb-16 pt-10 lg:px-8 lg:pt-14">
        {activeView === 'home' && (
          <>
            <section className="mx-auto max-w-3xl text-center">
              <div className="motion-fade-up mx-auto mb-5 flex w-fit items-center gap-2 rounded-full border border-[#b6d0e7] bg-[#f0f8ff] px-3 py-1.5 text-xs font-semibold uppercase tracking-[0.16em] text-[#0f5f9a]">
                <span className="size-1.5 rounded-full bg-[#1d6fa7]" />
                Research Intelligence Platform
              </div>
              <h1 className="motion-fade-up font-serif text-4xl font-semibold tracking-tight text-[#0b2341] sm:text-5xl lg:text-6xl" style={{ animationDelay: '70ms' }}>
                Discover FSBM Research
              </h1>
              <p className="motion-fade-up mx-auto mt-5 max-w-2xl text-base leading-7 text-slate-600 sm:text-lg" style={{ animationDelay: '130ms' }}>
                Powered by NLP and semantic search to find exact meaning, not just keywords.
              </p>

              <form onSubmit={handleSearch} className="motion-fade-up relative mx-auto mt-9 max-w-2xl" style={{ animationDelay: '170ms' }}>
                <Search className="absolute left-4 top-1/2 size-5 -translate-y-1/2 text-[#1d6fa7]" />
                <Input
                  value={query}
                  onChange={(event) => setQuery(event.target.value)}
                  className="h-14 rounded-xl border-[#c9d9e9] bg-white pl-12 pr-28 text-sm shadow-[0_10px_26px_rgba(14,57,96,0.12)] transition-all focus-visible:border-[#1d6fa7] focus-visible:ring-[#1d6fa7]/25"
                  placeholder="Search for 'deep learning in medical imaging'..."
                />
                <Button
                  type="submit"
                  disabled={isLoading}
                  className="absolute right-1.5 top-1.5 h-11 rounded-lg bg-[#0f5f9a] px-5 shadow-[0_8px_18px_rgba(15,95,154,0.32)] hover:bg-[#0b2341]"
                >
                  {isLoading ? 'Searching...' : 'Search'}
                </Button>
              </form>

              <div className="motion-fade-up mt-5 flex flex-wrap justify-center gap-2" style={{ animationDelay: '220ms' }}>
                <span className="mr-1 self-center text-xs text-slate-400">Try:</span>
                {['Machine Learning', 'Data Engineering', 'Mathematical Optimization'].map((suggestion) => (
                  <button
                    key={suggestion}
                    onClick={() => setQuery(suggestion)}
                    className="rounded-full border border-[#d2e0ed] bg-white px-3.5 py-2 text-xs font-medium text-slate-600 transition-all hover:-translate-y-0.5 hover:border-[#1d6fa7] hover:text-[#1d6fa7]"
                  >
                    {suggestion}
                  </button>
                ))}
              </div>
            </section>

            <section className="mt-16">
              <div className="mb-6 flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
                <div>
                  <p className="text-xs font-semibold uppercase tracking-[0.18em] text-[#1d6fa7]">Semantic results</p>
                  <h2 className="mt-1 font-serif text-2xl font-semibold text-[#0b2341]">Results for “{query || '...'}”</h2>
                  <p className="mt-1 text-sm text-slate-500">{results.length} papers ranked by semantic relevance</p>
                </div>
                <Button
                  variant="outline"
                  className="w-fit border-[#d2e0ed] bg-white text-slate-600 md:hidden"
                  onClick={() => setMobileFilters((prev) => !prev)}
                >
                  <Filter data-icon="inline-start" /> Filters
                </Button>
              </div>

              <div className="grid gap-7 lg:grid-cols-[240px_1fr]">
                <aside className={`${mobileFilters ? 'block' : 'hidden'} lg:block`}>
                  <Filters />
                </aside>
                <div className="flex flex-col gap-4">
                  {results.length === 0 && (
                    <Card className="border border-dashed border-[#c8d9e8] bg-white">
                      <CardContent className="flex min-h-44 flex-col items-center justify-center gap-2 p-6 text-center">
                        <BookOpen className="size-6 text-[#1a659b]" />
                        <p className="text-sm font-medium text-[#0b2341]">No search results yet</p>
                        <p className="text-xs text-slate-500">Run a semantic search to populate this area with ranked papers.</p>
                      </CardContent>
                    </Card>
                  )}
                  {results.map((result, index) => (
                    <PaperCard key={result.id} result={result} index={index} />
                  ))}
                </div>
              </div>
            </section>
          </>
        )}

        {activeView === 'faculty' && (
          <section>
            <div className="motion-fade-up mb-8 flex flex-col gap-2">
              <p className="text-xs font-semibold uppercase tracking-[0.18em] text-[#1d6fa7]">Faculty profiles</p>
              <h2 className="font-serif text-3xl font-semibold text-[#0b2341]">FSBM Research Faculty</h2>
              <p className="text-sm text-slate-500">
                Comprehensive profiles with academic impact indicators across all available researchers.
              </p>
            </div>

            {profilesError && (
              <Card className="mb-5 border border-red-200 bg-red-50 text-red-900">
                <CardContent className="flex items-center justify-between gap-4 p-4">
                  <p className="text-sm">{profilesError}</p>
                  <Button size="sm" variant="outline" onClick={() => void fetchProfiles()}>Retry</Button>
                </CardContent>
              </Card>
            )}

            {profilesLoading ? (
              <div className="grid gap-5 sm:grid-cols-2 xl:grid-cols-3">
                {Array.from({ length: 6 }).map((_, index) => (
                  <div key={index} className="h-72 animate-pulse rounded-xl border border-[#d4e3f1] bg-white" />
                ))}
              </div>
            ) : (
              <div className="grid gap-5 sm:grid-cols-2 xl:grid-cols-3">
                {profiles.map((profile, index) => (
                  <FacultyProfileCard key={profile.id} profile={profile} index={index} />
                ))}
              </div>
            )}
          </section>
        )}
      </main>

      <footer className="border-t border-[#dbe6f1] bg-white">
        <div className="mx-auto flex max-w-7xl flex-col gap-2 px-5 py-6 text-xs text-slate-500 sm:flex-row sm:items-center sm:justify-between lg:px-8">
          <p>FSBM Semantic Scholar · Faculty of Sciences Ben M&apos;Sik</p>
          <p>Universite Hassan II de Casablanca</p>
        </div>
      </footer>
    </div>
  )
}
