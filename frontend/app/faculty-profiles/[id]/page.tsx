import Link from 'next/link'
import { ArrowLeft, BookOpen, GraduationCap, Quote, TrendingUp } from 'lucide-react'
import facultyMetrics from '@/data/faculty_metrics.json'
import { Card, CardContent } from '@/components/ui/card'
import { Navbar } from '@/components/Navbar'

type ProfilePageProps = {
  params: Promise<{ id: string }>
}

export function generateStaticParams() {
  return facultyMetrics.map((researcher) => ({ id: researcher.chercheur_id }))
}

export default async function FacultyProfilePage({ params }: ProfilePageProps) {
  const { id } = await params
  const researcher = facultyMetrics.find((candidate) => candidate.chercheur_id === id)

  if (!researcher) {
    return (
      <main className="mx-auto max-w-3xl px-5 py-16 text-center">
        <h1 className="text-2xl font-semibold text-slate-900">Researcher not found</h1>
        <Link href="/faculty-profiles" className="mt-5 inline-flex h-10 items-center justify-center rounded-md bg-blue-700 px-4 text-sm font-medium text-white hover:bg-blue-900">Back to directory</Link>
      </main>
    )
  }

  const metrics = [
    { label: 'H-index', value: researcher.h_index.toLocaleString(), icon: TrendingUp },
    { label: 'i10-index', value: researcher.i10_index.toLocaleString(), icon: GraduationCap },
    { label: 'Total citations', value: researcher.citations_total.toLocaleString(), icon: Quote },
  ]

  return (
    <div className="min-h-screen bg-slate-50 text-slate-800">
      <Navbar />
      <main className="px-5 py-6 lg:px-8">
      <div className="mx-auto max-w-7xl">
        <Link href="/faculty-profiles" className="mb-6 inline-flex h-10 items-center justify-center gap-2 rounded-md px-3 text-sm font-medium text-slate-600 hover:bg-white hover:text-blue-700">
          <ArrowLeft className="size-4" /> Back to directory
        </Link>
        <section className="rounded-2xl border border-blue-100 bg-gradient-to-br from-blue-950 to-blue-700 p-7 text-white shadow-lg">
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-blue-200">Faculty researcher</p>
          <h1 className="mt-2 text-3xl font-semibold sm:text-4xl">{researcher.nom_complet}</h1>
          <p className="mt-3 text-sm text-blue-100">{researcher.affiliation}</p>
          <p className="mt-2 text-xs text-blue-200">Researcher ID: {researcher.chercheur_id}</p>
        </section>
        <div className="mt-6 grid gap-4 sm:grid-cols-3">
          {metrics.map(({ label, value, icon: Icon }) => (
            <Card key={label} className="border-slate-200 bg-white">
              <CardContent className="flex items-center gap-4 p-5">
                <div className="rounded-lg bg-blue-50 p-3 text-blue-700"><Icon className="size-5" /></div>
                <div><p className="text-2xl font-semibold text-slate-900">{value}</p><p className="text-sm text-slate-500">{label}</p></div>
              </CardContent>
            </Card>
          ))}
        </div>
        <section className="mt-6 rounded-xl border border-slate-200 bg-white p-6">
          <h2 className="flex items-center gap-2 text-lg font-semibold text-slate-900"><BookOpen className="size-5 text-blue-700" /> Top papers</h2>
          <div className="mt-4 space-y-3">
            {researcher.top_papers.map((paper) => (
              <div key={paper.article_id} className="rounded-lg border border-slate-200 bg-slate-50 p-4">
                <p className="font-medium text-slate-900">{paper.title}</p>
                <p className="mt-1 text-xs text-slate-500">{paper.year}</p>
              </div>
            ))}
          </div>
        </section>
      </div>
      </main>
    </div>
  )
}
