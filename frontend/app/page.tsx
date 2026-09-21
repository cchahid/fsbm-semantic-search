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
      <footer className="w-full bg-white border-t border-gray-200 mt-auto">
        <div className="max-w-7xl mx-auto w-full px-4 sm:px-6 lg:px-8 py-6 flex items-center justify-between">
          <p className="text-sm text-gray-500">FSBM Semantic Scholar · Faculty of Sciences Ben M&apos;Sik</p>
          <p className="text-sm text-gray-500">Universite Hassan II de Casablanca</p>
        </div>
      </footer>
    </div>
  )
}
