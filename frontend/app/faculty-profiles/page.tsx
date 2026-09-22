'use client'

import { useEffect, useMemo, useState } from 'react'
import { FacultyProfileCard, type FacultyProfile } from '@/components/FacultyProfileCard'
import { Navbar } from '@/components/Navbar'
import { fetchFacultyProfiles } from '@/lib/api'

export default function FacultyProfilesPage() {
  const [profiles, setProfiles] = useState<FacultyProfile[]>([])
  const [selectedLaboratory, setSelectedLaboratory] = useState('all')
  const [isLoading, setIsLoading] = useState(true)
  const [loadError, setLoadError] = useState<string | null>(null)

  useEffect(() => {
    fetchFacultyProfiles()
      .then((data) => setProfiles(data.profiles))
      .catch((error) => {
        console.error('Faculty profile request failed:', error)
        setLoadError('Unable to load faculty profiles. Check that the backend is running.')
      })
      .finally(() => setIsLoading(false))
  }, [])

  const laboratories = useMemo(
    () => [...new Set(profiles.map((profile) => profile.laboratoire).filter((laboratory) => laboratory && laboratory !== 'Unknown'))].sort(),
    [profiles],
  )
  const filteredProfiles = useMemo(
    () => selectedLaboratory === 'all'
      ? profiles
      : profiles.filter((profile) => profile.laboratoire === selectedLaboratory),
    [profiles, selectedLaboratory],
  )

  return (
    <div className="min-h-screen bg-slate-50 text-slate-800">
      <Navbar />
      <main className="mx-auto max-w-7xl px-5 pb-16 pt-6 lg:px-8">
        <div className="mb-6 flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
          <div>
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-blue-600">Faculty profiles</p>
          <h1 className="mt-1 text-3xl font-semibold text-slate-900">Researcher directory</h1>
          </div>
          <select
            value={selectedLaboratory}
            onChange={(event) => setSelectedLaboratory(event.target.value)}
            aria-label="Filter faculty by laboratory"
            className="h-10 w-full rounded-lg border border-slate-300 bg-white px-3 text-sm outline-none focus:border-blue-600 focus:ring-2 focus:ring-blue-600/20 sm:max-w-xs"
          >
            <option value="all">All laboratories</option>
            {laboratories.map((laboratory) => <option key={laboratory} value={laboratory}>{laboratory}</option>)}
          </select>
        </div>
        <div className="grid gap-5 sm:grid-cols-2 xl:grid-cols-3">
          {isLoading ? (
            <p className="text-sm text-slate-500">Loading faculty profiles...</p>
          ) : loadError ? (
            <p className="text-sm text-red-600">{loadError}</p>
          ) : filteredProfiles.length === 0 ? (
            <p className="text-sm text-slate-500">No faculty profiles found.</p>
          ) : filteredProfiles.map((profile, index) => <FacultyProfileCard key={profile.chercheur_id} profile={profile} index={index} />)}
        </div>
      </main>
    </div>
  )
}
