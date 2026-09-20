'use client'

import { useCallback, useEffect, useState } from 'react'
import { BookOpen, Download, SlidersHorizontal, UserRound } from 'lucide-react'
import Link from 'next/link'
import { useSearchParams } from 'next/navigation'
import researchers from '@/data/faculty_metrics.json'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Separator } from '@/components/ui/separator'

type SearchResult = {
  id: string
  title: string
  author: string
  year: string
  citations: number
  abstract: string
  match_score: number
  faculty_id: string
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

function PaperCard({ result, index }: { result: SearchResult; index: number }) {
  return (
    <Card
      className="group motion-fade-up border border-slate-200 bg-white shadow-md transition-all duration-300 hover:-translate-y-1 hover:border-blue-600 hover:shadow-xl"
      style={{ animationDelay: `${80 + index * 70}ms` }}
    >
      <CardContent className="p-5 sm:p-6">
        <div className="flex items-start justify-between gap-4">
          <div className="min-w-0">
            <h3 className="text-lg font-semibold leading-snug text-blue-900">{result.title}</h3>
            <p className="mt-2 flex items-center gap-2 text-sm text-slate-600">
              <UserRound className="size-4 text-blue-600" />
              {result.author}
            </p>
          </div>
        </div>
        <div className="mt-3 flex flex-wrap gap-2">
          <span className="rounded-full bg-blue-50 px-2 py-1 text-xs text-blue-700">{result.year}</span>
          <span className="rounded-full bg-blue-50 px-2 py-1 text-xs text-blue-700">{result.citations} citations</span>
          <span className="rounded-full bg-blue-50 px-2 py-1 text-xs text-blue-700">{result.match_score}% semantic match</span>
        </div>
        <p className="mt-4 line-clamp-3 text-sm leading-6 text-slate-600">{result.abstract}</p>
        <Separator className="my-4 bg-slate-200" />
        <div className="flex flex-wrap gap-2">
          <Button variant="outline" size="sm" className="border-slate-300 text-slate-700 hover:bg-blue-50">
            <Download data-icon="inline-start" /> View PDF
          </Button>
          <Link href={`/faculty-profiles/${result.faculty_id}`} className="inline-flex h-9 items-center justify-center rounded-md bg-blue-700 px-3 text-sm font-medium text-white transition-colors hover:bg-blue-900">
            View Faculty Profile
          </Link>
        </div>
      </CardContent>
    </Card>
  )
}

function LoadingCard() {
  return (
    <Card className="border-slate-200 bg-white">
      <CardContent className="space-y-4 p-6">
        <div className="flex items-center justify-between">
          <div className="h-5 w-2/3 animate-pulse rounded bg-slate-200" />
          <div className="h-6 w-20 animate-pulse rounded-full bg-blue-100" />
        </div>
        <div className="h-4 w-1/3 animate-pulse rounded bg-slate-100" />
        <div className="space-y-2">
          <div className="h-3 animate-pulse rounded bg-slate-100" />
          <div className="h-3 w-5/6 animate-pulse rounded bg-slate-100" />
        </div>
      </CardContent>
    </Card>
  )
}

const yearRanges = [
  { value: '2020-2024', label: '2020 - 2024' },
  { value: '2015-2019', label: '2015 - 2019' },
  { value: 'Before 2015', label: 'Before 2015' },
] as const

type FiltersProps = {
  selectedYearRanges: string[]
  onYearRangeChange: (range: string) => void
  onClear: () => void
}

function Filters({ selectedYearRanges, onYearRangeChange, onClear }: FiltersProps) {
  return (
    <Card className="border-slate-200 bg-white shadow-md">
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center gap-2 text-base text-slate-900">
          <SlidersHorizontal className="size-4 text-blue-600" /> Refine results
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-5">
        <div>
          <p className="mb-3 text-sm font-semibold text-slate-900">Publication year</p>
          {yearRanges.map(({ value, label }) => (
            <label key={label} className="mb-3 flex items-center gap-3 text-sm text-slate-600">
              <input
                type="checkbox"
                checked={selectedYearRanges.includes(value)}
                onChange={() => onYearRangeChange(value)}
                className="size-4 accent-blue-600"
              />
              {label}
            </label>
          ))}
        </div>
        <Separator />
        <Button type="button" variant="outline" onClick={onClear} className="w-full border-slate-300 text-slate-600">
          Clear all filters
        </Button>
      </CardContent>
    </Card>
  )
}

export function SearchDashboard() {
  const searchParams = useSearchParams()
  const [query, setQuery] = useState('')
  const [results, setResults] = useState<SearchResult[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [selectedYearRanges, setSelectedYearRanges] = useState<string[]>([])

  function toggleYearRange(range: string) {
    setSelectedYearRanges((current) =>
      current.includes(range)
        ? current.filter((selectedRange) => selectedRange !== range)
        : [...current, range],
    )
  }

  const filteredResults = results.filter((result) => {
    if (selectedYearRanges.length === 0) return true

    const yearMatch = result.year.match(/\b\d{4}\b/)
    const year = yearMatch ? Number(yearMatch[0]) : Number.NaN
    if (!Number.isFinite(year)) return false

    return selectedYearRanges.some((range) => {
      if (range === '2020-2024') return year >= 2020 && year <= 2024
      if (range === '2015-2019') return year >= 2015 && year <= 2019
      if (range === 'Before 2015') return year < 2015
      return false
    })
  })

  const runSearch = useCallback(async (searchQuery: string) => {
    if (!searchQuery.trim()) return
    setIsLoading(true)
    try {
      const response = await fetch(`http://127.0.0.1:8000/search?${new URLSearchParams({ query: searchQuery.trim() })}`)
      if (!response.ok) throw new Error(`Server error: ${response.status}`)
      const data = await response.json()
      const normalizedResults: SearchResult[] = (data.results || []).map((item: BackendSearchResult, index: number) => {
        const metadata = item.metadata || {}
        const distance = typeof item.distance === 'number' ? item.distance : 1
        const score = typeof item.match_score === 'number'
          ? Math.max(0, Math.min(100, Math.round(item.match_score)))
          : Math.max(0, Math.min(100, Math.round((1 - distance) * 100)))
        const rawAuthor = item.author_display ?? item.authors ?? metadata.author ?? metadata.authors ?? metadata.auteurs ?? metadata.nom_complet
        const author = Array.isArray(rawAuthor) ? rawAuthor.join(', ') : typeof rawAuthor === 'string' ? rawAuthor : 'Unknown author'
        const matchedResearcher = researchers.find((researcher) => {
          const researcherName = researcher.nom_complet.toLowerCase()
          const authorName = author.toLowerCase()
          return authorName.includes(researcherName) || researcherName.includes(authorName)
        })
        const rawCitations = item.citations ?? metadata.citations ?? metadata.citation_count ?? 0
        const citations = Number(rawCitations)
        return {
          id: item.id || item.article_id || `result-${index}`,
          title: String(item.title ?? metadata.title ?? metadata.titre ?? item.article_id ?? 'Untitled'),
          author,
          year: String(item.year ?? metadata.year ?? metadata.publication_year ?? metadata.date_publication ?? 'N/A'),
          citations: Number.isFinite(citations) ? citations : 0,
          abstract: item.abstract || 'No abstract available.',
          match_score: score,
          faculty_id: String(metadata.chercheur_id ?? metadata.researcher_id ?? matchedResearcher?.chercheur_id ?? 'upOdTrEAAAAJ'),
        }
      })
      setResults(normalizedResults)
    } catch (error) {
      console.error('Search request failed:', error)
      setResults([])
    } finally {
      setIsLoading(false)
    }
  }, [])

  useEffect(() => {
    const urlQuery = searchParams.get('query')
    if (urlQuery) {
      setQuery(urlQuery)
      void runSearch(urlQuery)
    }
  }, [runSearch, searchParams])

  return (
    <main className="flex-1 mx-auto grid w-full max-w-7xl grid-cols-1 gap-6 px-5 pb-16 pt-6 md:grid-cols-4 lg:px-8">
      <aside className="md:col-span-1 md:sticky md:top-24 md:h-fit">
        <Filters
          selectedYearRanges={selectedYearRanges}
          onYearRangeChange={toggleYearRange}
          onClear={() => setSelectedYearRanges([])}
        />
      </aside>
      <section className="md:col-span-3">
        <div className="mb-6">
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-blue-600">Semantic results</p>
          <h2 className="mt-1 font-serif text-2xl font-semibold text-slate-900">Results for “{query || '...'}”</h2>
          <p className="mt-1 text-sm text-slate-500">{isLoading ? 'Finding the most relevant papers...' : `${filteredResults.length} papers ranked by semantic relevance`}</p>
        </div>
        <div className="flex flex-col gap-4">
            {isLoading ? Array.from({ length: 3 }).map((_, index) => <LoadingCard key={index} />) : filteredResults.length ? filteredResults.map((result, index) => <PaperCard key={result.id} result={result} index={index} />) : (
              <Card className="border border-dashed border-slate-300 bg-white">
                <CardContent className="flex min-h-44 flex-col items-center justify-center gap-2 p-6 text-center">
                  <BookOpen className="size-6 text-blue-600" />
                  <p className="text-sm font-medium text-slate-900">{results.length ? 'No results match the selected years' : 'No search results yet'}</p>
                  <p className="text-xs text-slate-500">{results.length ? 'Try selecting another publication year range.' : 'Run a semantic search to populate this area with ranked papers.'}</p>
                </CardContent>
              </Card>
            )}
        </div>
      </section>
    </main>
  )
}
