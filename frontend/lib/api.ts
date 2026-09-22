export type FacultyPaper = {
  article_id: string
  title: string
  year: string
}

export type FacultyProfileData = {
  id: string
  chercheur_id: string
  name: string
  nom_complet: string
  department: string
  affiliation: string
  laboratoire: string
  citations_total: number
  h_index: number
  i10_index: number
  publications_count: number
  top_publication?: string
  top_publication_citations?: number
  top_papers: FacultyPaper[]
}

type FacultyProfilesResponse = {
  count: number
  profiles: FacultyProfileData[]
}

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? 'http://127.0.0.1:8000'

export async function fetchFacultyProfiles(): Promise<FacultyProfilesResponse> {
  const response = await fetch(`${API_BASE_URL}/faculty-profiles`, { cache: 'no-store' })
  if (!response.ok) throw new Error(`Faculty profile request failed: ${response.status}`)
  return response.json() as Promise<FacultyProfilesResponse>
}
