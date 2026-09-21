'use client'

import { useMemo, useState } from 'react'
import facultyMetrics from '@/data/faculty_metrics.json'
import { FacultyProfileCard, type FacultyProfile } from '@/components/FacultyProfileCard'
import { Navbar } from '@/components/Navbar'

const profiles: FacultyProfile[] = facultyMetrics.map((researcher) => ({
  id: researcher.chercheur_id,
  chercheur_id: researcher.chercheur_id,
  name: researcher.nom_complet,
  department: 'Faculty of Sciences Ben M’Sik',
  affiliation: researcher.affiliation,
  laboratoire: researcher.laboratoire,
  citations_total: researcher.citations_total,
  h_index: researcher.h_index,
  i10_index: researcher.i10_index,
  publications_count: researcher.publications_count,
}))

export default function FacultyProfilesPage() {
  const [selectedLaboratory, setSelectedLaboratory] = useState('all')
  const laboratories = useMemo(
    () => [...new Set(profiles.map((profile) => profile.laboratoire).filter((laboratory) => laboratory && laboratory !== 'Unknown'))].sort(),
    [],
  )
  const filteredProfiles = useMemo(
    () => selectedLaboratory === 'all'
      ? profiles
      : profiles.filter((profile) => profile.laboratoire === selectedLaboratory),
    [selectedLaboratory],
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
          {filteredProfiles.map((profile, index) => <FacultyProfileCard key={profile.chercheur_id} profile={profile} index={index} />)}
        </div>
      </main>
    </div>
  )
}
