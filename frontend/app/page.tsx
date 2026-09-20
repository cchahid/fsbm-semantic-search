'use client';

import { useState } from 'react'
import type { FormEvent } from 'react'
import { BookOpen, ChevronDown, Download, Filter, GraduationCap, Menu, Search, SlidersHorizontal, UserRound } from 'lucide-react'
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

function PaperCard({ result }: { result: SearchResult }) {
  const [expanded, setExpanded] = useState(false)
  return (
    <Card className="group border-slate-200 bg-white shadow-sm transition-all hover:-translate-y-0.5 hover:border-[#c9a24d]/60 hover:shadow-md">
      <CardContent className="p-5 sm:p-6">
        <div className="flex items-start justify-between gap-4">
          <div className="min-w-0">
            <h3 className="font-serif text-lg font-semibold leading-snug text-[#0b2341] sm:text-xl">{result.title}</h3>
            <p className="mt-2 flex items-center gap-2 text-sm text-slate-500"><UserRound className="size-4" />{result.author}</p>
          </div>
          <Badge className="shrink-0 border-[#c9a24d]/30 bg-[#fbf6e9] text-[#85651e]">{result.match_score}% match</Badge>
        </div>
        <div className="mt-4 flex flex-wrap gap-2">
          <Badge variant="outline" className="font-normal">{result.year}</Badge>
          <Badge variant="outline" className="font-normal">{result.citations} citations</Badge>
        </div>
        <p className={`mt-4 text-sm leading-6 text-slate-600 ${expanded ? '' : 'line-clamp-3'}`}>{result.abstract}</p>
        <button onClick={() => setExpanded(!expanded)} className="mt-1 inline-flex items-center gap-1 text-sm font-medium text-[#0b5688] hover:text-[#0b2341]">
          {expanded ? 'Show less' : 'Read more'} <ChevronDown className={`size-4 transition-transform ${expanded ? 'rotate-180' : ''}`} />
        </button>
        <Separator className="my-5" />
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <Button variant="outline" size="sm" className="w-fit border-[#0b2341]/20 text-[#0b2341] hover:bg-[#f2f6fa]">
            <Download data-icon="inline-start" /> View PDF
          </Button>
          <div className="flex min-w-52 flex-1 items-center gap-3 sm:max-w-64">
            <span className="whitespace-nowrap text-xs font-medium text-slate-500">Semantic match</span>
            <Progress value={result.match_score} className="h-2 bg-slate-100 [&>div]:bg-[#c9a24d]" />
            <span className="text-sm font-semibold text-[#0b2341]">{result.match_score}%</span>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

function Filters() {
  return (
    <Card className="border-slate-200 bg-white shadow-sm">
      <CardHeader className="pb-3"><CardTitle className="flex items-center gap-2 text-base text-[#0b2341]"><SlidersHorizontal className="size-4 text-[#0b5688]" />Refine results</CardTitle></CardHeader>
      <CardContent className="flex flex-col gap-6">
        <fieldset className="flex flex-col gap-3"><legend className="mb-1 text-sm font-semibold text-[#0b2341]">Publication year</legend>{['2020 – 2024', '2015 – 2019', 'Before 2015'].map((label, index) => <label key={label} className="flex items-center gap-3 text-sm text-slate-600"><Checkbox defaultChecked={index === 0} />{label}</label>)}</fieldset>
        <Separator />
        <fieldset className="flex flex-col gap-3"><legend className="mb-1 text-sm font-semibold text-[#0b2341]">Department</legend>{['Computer Science', 'Mathematics', 'Data Science'].map((label, index) => <label key={label} className="flex items-center gap-3 text-sm text-slate-600"><Checkbox defaultChecked={index === 0} />{label}</label>)}</fieldset>
        <Separator />
        <div className="flex flex-col gap-3"><div className="flex justify-between"><span className="text-sm font-semibold text-[#0b2341]">Minimum citations</span><span className="text-sm font-semibold text-[#0b5688]">20+</span></div><Slider defaultValue={[20]} max={200} step={10} /></div>
        <Button variant="outline" className="border-slate-200 text-slate-600">Clear all filters</Button>
      </CardContent>
    </Card>
  )
}

function FacultyCard() {
  return <Card className="overflow-hidden border-slate-200 bg-white shadow-sm"><div className="h-2 bg-[#c9a24d]" /><CardContent className="p-5"><div className="flex items-center gap-4"><div className="flex size-12 items-center justify-center rounded-full bg-[#e8f1f7] text-[#0b5688]"><GraduationCap className="size-6" /></div><div><p className="font-semibold text-[#0b2341]">Prof. Habib Ben Lahmar</p><p className="text-xs text-slate-500">Computer Science Department</p></div></div><div className="mt-5 grid grid-cols-3 gap-2 text-center"><div><p className="text-lg font-semibold text-[#0b2341]">24</p><p className="text-[11px] text-slate-500">h-index</p></div><div><p className="text-lg font-semibold text-[#0b2341]">41</p><p className="text-[11px] text-slate-500">i10-index</p></div><div><p className="text-lg font-semibold text-[#0b2341]">1,240</p><p className="text-[11px] text-slate-500">citations</p></div></div></CardContent></Card>
}

export default function Page() {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState<SearchResult[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [mobileFilters, setMobileFilters] = useState(false)

  async function handleSearch(e: FormEvent) {
    e.preventDefault()
    if (!query.trim()) return

    setIsLoading(true)

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
      console.error("Search request failed:", err)
      alert("Cannot reach backend server. Make sure FastAPI is running.")
    } finally {
      setIsLoading(false)
    }
  }

  return <div className="min-h-screen bg-[#f7f9fb] text-slate-800">
    <header className="sticky top-0 z-10 border-b border-slate-200 bg-white/95 backdrop-blur"><div className="mx-auto flex h-18 max-w-7xl items-center justify-between px-5 lg:px-8"><div className="flex items-center gap-3"><div className="flex size-10 items-center justify-center rounded-xl bg-[#0b2341] text-[#e6c56d]"><BookOpen className="size-5" /></div><div><p className="text-sm font-bold tracking-tight text-[#0b2341]">FSBM</p><p className="hidden text-[11px] text-slate-500 sm:block">Université Hassan II</p></div></div><nav className="hidden items-center gap-8 text-sm font-medium text-slate-600 md:flex"><a className="text-[#0b5688]" href="#home">Home</a><a className="hover:text-[#0b5688]" href="#faculty">Faculty Profiles</a><a className="hover:text-[#0b5688]" href="#analytics">Analytics</a><a className="hover:text-[#0b5688]" href="#about">About</a></nav><Button variant="ghost" size="icon" className="md:hidden" aria-label="Open menu"><Menu /></Button></div></header>
    <main id="home" className="mx-auto max-w-7xl px-5 pb-16 pt-12 lg:px-8 lg:pt-16">
      <section className="mx-auto max-w-3xl text-center"><div className="mx-auto mb-5 flex w-fit items-center gap-2 rounded-full border border-[#c9a24d]/30 bg-[#fbf6e9] px-3 py-1.5 text-xs font-semibold uppercase tracking-[0.16em] text-[#85651e]"><span className="size-1.5 rounded-full bg-[#c9a24d]" />Research intelligence platform</div><h1 className="font-serif text-4xl font-semibold tracking-tight text-[#0b2341] sm:text-5xl lg:text-6xl">Discover FSBM Research</h1><p className="mx-auto mt-5 max-w-2xl text-base leading-7 text-slate-500 sm:text-lg">Powered by NLP &amp; semantic search to find exact meaning, not just keywords.</p><form onSubmit={handleSearch} className="relative mx-auto mt-9 max-w-2xl"><Search className="absolute left-4 top-1/2 size-5 -translate-y-1/2 text-[#0b5688]" /><Input value={query} onChange={(event) => setQuery(event.target.value)} className="h-14 rounded-xl border-slate-200 bg-white pl-12 pr-28 text-sm shadow-lg shadow-[#0b2341]/10 focus-visible:ring-[#0b5688]" placeholder="Search for 'deep learning in medical imaging'..." /><Button type="submit" disabled={isLoading} className="absolute right-1.5 top-1.5 h-11 rounded-lg bg-[#0b5688] px-5 hover:bg-[#0b2341]">{isLoading ? 'Searching...' : 'Search'}</Button></form><div className="mt-5 flex flex-wrap justify-center gap-2"><span className="mr-1 self-center text-xs text-slate-400">Try:</span>{['Machine Learning', 'Data Engineering', 'Mathematical Optimization'].map((suggestion) => <button key={suggestion} onClick={() => setQuery(suggestion)} className="rounded-full border border-slate-200 bg-white px-3.5 py-2 text-xs font-medium text-slate-600 transition-colors hover:border-[#0b5688] hover:text-[#0b5688]">{suggestion}</button>)}</div></section>
      <section className="mt-16"><div className="mb-6 flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between"><div><p className="text-xs font-semibold uppercase tracking-[0.18em] text-[#c09232]">Semantic results</p><h2 className="mt-1 font-serif text-2xl font-semibold text-[#0b2341]">Results for “{query}”</h2><p className="mt-1 text-sm text-slate-500">{results.length} papers ranked by semantic relevance</p></div><Button variant="outline" className="w-fit border-slate-200 bg-white text-slate-600 md:hidden" onClick={() => setMobileFilters(!mobileFilters)}><Filter data-icon="inline-start" /> Filters</Button></div><div className="grid gap-7 lg:grid-cols-[240px_1fr]"><aside className={`${mobileFilters ? 'block' : 'hidden'} lg:block`}><Filters /><div id="faculty" className="mt-6"><FacultyCard /></div></aside><div className="flex flex-col gap-4">{results.map((result) => <PaperCard key={result.id} result={result} />)}</div></div></section>
    </main><footer className="border-t border-slate-200 bg-white"><div className="mx-auto flex max-w-7xl flex-col gap-2 px-5 py-6 text-xs text-slate-500 sm:flex-row sm:items-center sm:justify-between lg:px-8"><p>FSBM Semantic Scholar · Faculty of Sciences Ben M&apos;Sik</p><p>Université Hassan II de Casablanca</p></div></footer>
  </div>
}
