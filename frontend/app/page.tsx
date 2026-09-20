import { Suspense } from 'react'
import { Navbar } from '@/components/Navbar'
import { SearchDashboard } from '@/components/SearchDashboard'

export default function HomePage() {
  return (
    <div className="flex min-h-screen flex-col bg-slate-50 text-slate-800">
      <Navbar />
      <Suspense fallback={<div className="flex-1 px-5 py-6 text-sm text-slate-500 lg:px-8">Loading discovery workspace...</div>}>
        <SearchDashboard />
      </Suspense>
      <footer className="border-t border-slate-200 bg-white">
        <div className="mx-auto flex max-w-7xl flex-col gap-2 px-5 py-6 text-xs text-slate-500 sm:flex-row sm:items-center sm:justify-between lg:px-8">
          <p>FSBM Semantic Scholar · Faculty of Sciences Ben M&apos;Sik</p>
          <p>Universite Hassan II de Casablanca</p>
        </div>
      </footer>
    </div>
  )
}
