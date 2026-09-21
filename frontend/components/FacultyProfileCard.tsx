import { TrendingUp } from 'lucide-react'
import Link from 'next/link'
import { Card, CardContent } from '@/components/ui/card'

export type FacultyProfile = {
  id: string
  name: string
  department: string
  affiliation: string
  laboratoire: string
  citations_total: number
  h_index: number
  i10_index: number
  publications_count: number
  top_publication?: string
  chercheur_id?: string
}

function formatNumber(value: number) {
  return new Intl.NumberFormat('en-US').format(value)
}

export function FacultyProfileCard({ profile, index = 0 }: { profile: FacultyProfile; index?: number }) {
  const initials = profile.name
    .split(' ')
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase() ?? '')
    .join('') || 'FS'

  return (
    <Link href={`/faculty-profiles/${profile.chercheur_id ?? profile.id}`} className="block">
    <Card
      className="group motion-fade-up overflow-hidden border border-slate-200 bg-white shadow-md transition-all duration-300 hover:-translate-y-1 hover:border-blue-600 hover:shadow-xl"
      style={{ animationDelay: `${70 + index * 50}ms` }}
    >
      <div className="h-1.5 bg-gradient-to-r from-blue-900 via-blue-600 to-sky-400" />
      <CardContent className="p-5">
        <div className="flex items-start gap-4">
          <div className="flex size-12 shrink-0 items-center justify-center rounded-xl bg-blue-800 text-sm font-semibold text-white shadow-lg shadow-blue-900/20">
            {initials}
          </div>
          <div className="min-w-0">
            <h3 className="text-lg font-semibold text-slate-900">{profile.name}</h3>
            <p className="mt-1 text-sm font-medium text-blue-700">{profile.department}</p>
            <p className="mt-1 text-xs font-medium text-slate-500">{profile.laboratoire}</p>
            <p className="mt-1 line-clamp-2 text-xs leading-5 text-slate-500">{profile.affiliation}</p>
          </div>
        </div>

        <div className="mt-5 grid grid-cols-3 gap-2">
          {[
            [formatNumber(profile.citations_total), 'citations'],
            [String(profile.h_index), 'h-index'],
            [String(profile.i10_index), 'i10-index'],
          ].map(([value, label]) => (
            <div key={label} className="rounded-lg border border-slate-200 bg-slate-50 px-2 py-3 text-center">
              <p className="text-base font-semibold text-slate-900">{value}</p>
              <p className="text-[11px] text-slate-500">{label}</p>
            </div>
          ))}
        </div>

        <div className="mt-4 flex items-center justify-between rounded-lg border border-slate-200 bg-slate-50/70 px-3 py-2">
          <span className="inline-flex items-center gap-1.5 text-xs font-medium text-blue-700">
            <TrendingUp className="size-3.5" />
            Publications
          </span>
          <span className="text-sm font-semibold text-slate-900">{profile.publications_count}</span>
        </div>

        {profile.top_publication && (
          <div className="mt-4 rounded-lg border border-slate-200 bg-white px-3 py-2">
            <p className="text-[11px] font-semibold uppercase tracking-wide text-slate-500">Top publication</p>
            <p className="mt-1 line-clamp-2 text-xs leading-5 text-slate-700">{profile.top_publication}</p>
          </div>
        )}
      </CardContent>
    </Card>
    </Link>
  )
}
