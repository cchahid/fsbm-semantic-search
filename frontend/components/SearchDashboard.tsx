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
  article_id: string
  laboratoire: string
  equipe: string
  journal: string
  pdf_url: string
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
  const [isExpanded, setIsExpanded] = useState(false)
  const [pdfHref, setPdfHref] = useState<string | null>(result.pdf_url || null)

  useEffect(() => {
    const publicationId = result.article_id.startsWith(`${result.faculty_id}:`)
      ? result.article_id.slice(result.faculty_id.length + 1)
      : result.article_id
    const filename = `${result.faculty_id}_${publicationId.replaceAll(':', '_')}.pdf`
    const localPdfUrl = `http://localhost:8000/pdfs/${encodeURIComponent(filename)}`
    let cancelled = false

    async function resolvePdf() {
      try {
        const response = await fetch(localPdfUrl, { method: 'HEAD' })
        if (!cancelled && response.ok) {
          setPdfHref(localPdfUrl)
          return
        }
      } catch {
        // The external URL remains the fallback when the local API is unavailable.
      }
      if (!cancelled) setPdfHref(result.pdf_url || null)
    }

    void resolvePdf()
    return () => {
      cancelled = true
    }
  }, [result.article_id, result.faculty_id, result.pdf_url])

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
            <p className="mt-1 text-xs text-slate-500">
              {result.journal || 'Journal unavailable'}
              {result.laboratoire && result.laboratoire !== 'Unknown' ? ` · ${result.laboratoire}` : ''}
            </p>
          </div>
        </div>
        <div className="mt-3 flex flex-wrap gap-2">
          <span className="rounded-full bg-blue-50 px-2 py-1 text-xs text-blue-700">{result.year}</span>
          <span className="rounded-full bg-blue-50 px-2 py-1 text-xs text-blue-700">{result.citations} citations</span>
          <span className="rounded-full bg-blue-50 px-2 py-1 text-xs text-blue-700">{result.match_score}% semantic match</span>
        </div>
        <p className={`mt-4 text-sm leading-6 text-slate-600 ${isExpanded ? '' : 'line-clamp-3'}`}>
          {result.abstract}
        </p>
        <button
          type="button"
          onClick={() => setIsExpanded((expanded) => !expanded)}
          className="mt-1 text-sm text-blue-600 hover:underline"
          aria-expanded={isExpanded}
        >
          {isExpanded ? 'Show less' : 'Read more'}
        </button>
        <Separator className="my-4 bg-slate-200" />
        <div className="flex flex-wrap gap-2">
          {pdfHref ? (
            <a href={pdfHref} target="_blank" rel="noopener noreferrer" className="inline-flex h-9 items-center justify-center gap-2 rounded-md bg-blue-700 px-3 text-sm font-medium text-white transition-colors hover:bg-blue-900">
              <Download className="size-4" /> View PDF
            </a>
          ) : (
            <Button variant="outline" size="sm" disabled className="border-slate-300 text-slate-400">
              <Download data-icon="inline-start" /> PDF unavailable
            </Button>
          )}
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
  selectedLaboratories: string[]
  selectedTeams: string[]
  laboratories: string[]
  teams: string[]
  onYearRangeChange: (range: string) => void
  onLaboratoryChange: (value: string) => void
  onTeamChange: (value: string) => void
  onClear: () => void
}

function Filters({ selectedYearRanges, selectedLaboratories, selectedTeams, laboratories, teams, onYearRangeChange, onLaboratoryChange, onTeamChange, onClear }: FiltersProps) {
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
        <FilterCheckboxes title="Laboratoire" values={laboratories} selected={selectedLaboratories} onChange={onLaboratoryChange} />
        <Separator />
        <FilterCheckboxes title="Equipe" values={teams} selected={selectedTeams} onChange={onTeamChange} />
        <Separator />
        <Button type="button" variant="outline" onClick={onClear} className="w-full border-slate-300 text-slate-600">
          Clear all filters
        </Button>
      </CardContent>
    </Card>
  )
}

function FilterCheckboxes({ title, values, selected, onChange }: { title: string; values: string[]; selected: string[]; onChange: (value: string) => void }) {
  if (values.length === 0) return null
  return (
    <div>
      <p className="mb-3 text-sm font-semibold text-slate-900">{title}</p>
      {values.map((value) => (
        <label key={value} className="mb-3 flex items-start gap-3 text-sm text-slate-600">
          <input type="checkbox" checked={selected.includes(value)} onChange={() => onChange(value)} className="mt-0.5 size-4 accent-blue-600" />
          <span>{value}</span>
        </label>
      ))}
    </div>
  )
}

export function SearchDashboard() {
  const searchParams = useSearchParams()
  const [query, setQuery] = useState('')
  const [results, setResults] = useState<SearchResult[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [selectedYearRanges, setSelectedYearRanges] = useState<string[]>([])
  const [selectedLaboratories, setSelectedLaboratories] = useState<string[]>([])
  const [selectedTeams, setSelectedTeams] = useState<string[]>([])

  const laboratories = [...new Set(results.map((result) => result.laboratoire).filter((value) => value && value !== 'Unknown'))].sort()
  const teams = [...new Set(results.map((result) => result.equipe).filter((value) => value && value !== 'Unknown'))].sort()

  function toggleYearRange(range: string) {
    setSelectedYearRanges((current) =>
      current.includes(range)
        ? current.filter((selectedRange) => selectedRange !== range)
        : [...current, range],
    )
  }

  const filteredResults = results.filter((result) => {
    const yearMatch = result.year.match(/\b\d{4}\b/)
    const year = yearMatch ? Number(yearMatch[0]) : Number.NaN
    const matchesYear = selectedYearRanges.length === 0 || (Number.isFinite(year) && selectedYearRanges.some((range) => {
      if (range === '2020-2024') return year >= 2020 && year <= 2024
      if (range === '2015-2019') return year >= 2015 && year <= 2019
      if (range === 'Before 2015') return year < 2015
      return false
    }))
    const matchesLaboratory = selectedLaboratories.length === 0 || selectedLaboratories.includes(result.laboratoire)
    const matchesTeam = selectedTeams.length === 0 || selectedTeams.includes(result.equipe)
    return matchesYear && matchesLaboratory && matchesTeam
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
          article_id: String(item.article_id ?? item.id ?? ''),
          laboratoire: String(metadata.Laboratoire ?? metadata.laboratoire ?? 'Unknown'),
          equipe: String(metadata.Equipe ?? metadata.equipe ?? 'Unknown'),
          journal: String(metadata.journal ?? ''),
          pdf_url: String(metadata.pdf_url ?? ''),
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
          selectedLaboratories={selectedLaboratories}
          selectedTeams={selectedTeams}
          laboratories={laboratories}
          teams={teams}
          onYearRangeChange={toggleYearRange}
          onLaboratoryChange={(value) => setSelectedLaboratories((current) => current.includes(value) ? current.filter((item) => item !== value) : [...current, value])}
          onTeamChange={(value) => setSelectedTeams((current) => current.includes(value) ? current.filter((item) => item !== value) : [...current, value])}
          onClear={() => {
            setSelectedYearRanges([])
            setSelectedLaboratories([])
            setSelectedTeams([])
          }}
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
