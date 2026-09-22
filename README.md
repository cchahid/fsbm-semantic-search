# FSBM Semantic Search

FSBM Semantic Search is a research-discovery platform for the Faculty of Sciences
Ben M'Sik. It combines Google Scholar collection, dataset cleaning, OpenAlex
enrichment, sentence embeddings, ChromaDB vector search, a FastAPI API, and a
Next.js/Tailwind interface.

The repository contains both the reproducible data workflow and the application
that consumes its outputs:

```text
researcher list
    -> Google Scholar scraper
    -> raw researcher JSON
    -> OpenAlex enrichment & PDF download
    -> cleaner + department mapping
    -> clean Parquet
    -> embeddings Parquet
    -> ChromaDB collection
    -> FastAPI /search
    -> Next.js discovery UI
```

## Repository layout

```text
.
├── backend/
│   ├── requirements.txt          Backend-only Python dependencies
│   └── src/
│       ├── main.py                FastAPI app, Chroma search, profile API, PDF serving
│       ├── api/routes.py          Reserved API route module
│       ├── core/config.py         Backend configuration helpers
│       ├── core/elastic.py        Elasticsearch integration
│       └── services/search_service.py
├── data_pipeline/
│   ├── data/
│   │   ├── target_researchers.json  Input Scholar IDs and names
│   │   ├── raw/                  Bronze data, enrichment, manifests, and PDFs
│   │   ├── processed/             Silver/Gold Parquet datasets
│   │   └── references/            Faculty-to-laboratory mapping CSV
│   └── src/
│       ├── scholar_scraper.py     Scrapes one Scholar profile
│       ├── orchestrator.py        Runs/resumes profile collection
│       ├── id_resolver.py         Resolves Scholar IDs from names
│       ├── openalex_enricher.py   Adds open-access URLs and references
│       ├── pdf_downloader.py      Downloads available PDFs
│       ├── cleaner.py             Builds the clean article dataset
│       └── export_frontend_data.py Creates frontend faculty metrics JSON
├── frontend/
│   ├── app/
│   │   ├── page.tsx               Search/discovery page
│   │   ├── layout.tsx             Global layout and fonts
│   │   └── faculty-profiles/
│   │       ├── page.tsx           Faculty directory and laboratory filter
│   │       └── [id]/page.tsx      Static researcher dashboard route
│   ├── components/
│   │   ├── Navbar.tsx             Sticky navigation and search form
│   │   ├── SearchDashboard.tsx    Search request, filters, cards, PDF fallback
│   │   ├── FacultyProfileCard.tsx Directory card
│   │   └── ui/                    Shared Tailwind UI primitives
│   ├── data/faculty_metrics.json  Generated frontend-safe researcher data
│   └── package.json               Next.js scripts and dependencies
├── nlp_engine/
│   ├── src/
│   │   ├── generate_vectors.py    Clean Parquet -> embedding Parquet
│   │   ├── chroma_indexer.py      Embeddings -> ChromaDB
│   │   └── elastic_indexer.py     Optional Elasticsearch indexing
│   └── chroma_data/               Local persistent Chroma database
├── requirements.txt               Full Python environment snapshot
├── docker-compose.yml              Container orchestration placeholder
└── .env.example                   Environment variable template
```

## Data layers and formats

### Input and raw layer

`data_pipeline/data/target_researchers.json` identifies the faculty profiles to
collect. `orchestrator.py` calls `scholar_scraper.py` and incrementally writes
`data_pipeline/data/raw/fsbm_researchers_raw.json`. The raw records contain
researcher metrics (`citations_totales`, `h_index`, `i10_index`) and publication
records such as title, authors, year, journal, citations, and abstract.

`openalex_enricher.py` reads the clean fsbm_researchers_ram.json file and caches per-article
OpenAlex results in `data_pipeline/data/raw/openalex_enrichment.json`. The
enrichment may include an open-access `pdf_url` and referenced work IDs.

`pdf_downloader.py` uses that cache to download available PDFs to
`data_pipeline/data/raw/pdf's`. Files are named from the article ID after
replacing the colon separator with an underscore. `download_status.json` makes
the downloader resumable.

### Processed layer

`cleaner.py` flattens the nested raw JSON, removes duplicate article IDs,
normalizes abstracts, joins `references/fsbm_departments.csv`, and merges
OpenAlex fields. It writes:

- `fsbm_researchers_clean.parquet` (article metadata and cleaned text)
- fields including `chercheur_id`, `article_id`, `titre`, `auteurs`,
  `date_publication`, `citations`, `journal`, `abstract_clean`,
  `Etablissement`, `Laboratoire`, `Equipe`, `pdf_url`, and `references`

`export_frontend_data.py` reads the clean Parquet, groups publications by
researcher, merges global metrics from the raw JSON, selects top papers, and
writes `frontend/data/faculty_metrics.json`. This file is imported by the
legacy/static consumers. The running frontend reads the same cleaned Parquet
through the backend `/faculty-profiles` endpoint.

### Dataset and results

The latest completed pipeline run produced the following corpus. The
ineligible count is the difference between the unique raw publication records
and the records loaded by the vectorization step.

| Measure | Final corpus |
| --- | ---: |
| Collected researcher profiles | 89 |
| Raw publication records | 1,066 |
| Unique publication records | 1,066 |
| Eligible for embeddings | 993 |
| Ineligible for embeddings | 73 |
| Final embedding vectors | 993 x 2,560 |
| Final ChromaDB records | 993 |

The vectorization run used `zeroentropy/zembed-1-embedding` and reported a
vector dimension of `2,560`. The ChromaDB index was built from the same 993
vectorized records and stored in `nlp_engine/chroma_data`.

### Vector layer

`generate_vectors.py` reads the clean Parquet and embeds
`Title + Abstract` with `zeroentropy/zembed-1-embedding`, falling back to
`all-MiniLM-L6-v2` if the primary model cannot load. The result is written to
`data_pipeline/data/processed/fsbm_researchers_vectors.parquet`.

`nlp_engine/src/chroma_indexer.py` reads that vector dataset and upserts the
documents into the persistent `fsbm_publications` Chroma collection. Metadata
includes canonical search fields (`title`, `authors`, `year`, `citations`,
`chercheur_id`, `Laboratoire`, `Equipe`, `journal`, and `pdf_url`) plus legacy
aliases used by older records.

## Running the pipeline

Use the data-pipeline virtual environment for pandas, Parquet, and scraping
dependencies. From the repository root:

```powershell
cd data_pipeline
.\.venv\Scripts\Activate.ps1
python src\orchestrator.py
python src\openalex_enricher.py
python src\pdf_downloader.py
python src\cleaner.py
python src\export_frontend_data.py
```

Generate vectors and index them with the NLP environment:

```powershell
cd nlp_engine
.\.venv\Scripts\Activate.ps1
python src\generate_vectors.py
python src\chroma_indexer.py
```

The scraper and OpenAlex jobs make network requests and can be rate-limited.
Both the scraper and enrichment/downloader persist progress so they can be
rerun rather than starting from zero.

## Running the applications

### FastAPI backend

The backend reads `nlp_engine/chroma_data`, loads the raw article lookup at
startup, and exposes:

| Method | Route | Purpose |
| --- | --- | --- |
| `GET` | `/` | Health/status response |
| `GET` | `/search?query=...&top_k=5` | Semantic publication search |
| `GET` | `/faculty-profiles` | Faculty summary data |
| `GET` | `/pdfs/<filename>` | Local PDF static file |

Start it from the repository root with the backend environment:

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
uvicorn src.main:app --reload --port 8000
```

The API mounts `data_pipeline/data/raw/pdf's` and falls back to the alternate
`data_pipeline/data/raw/pdfs` directory when necessary. A local PDF is served
when present; the frontend uses the metadata `pdf_url` when it is not.

### Next.js frontend

```powershell
cd frontend
npm install
npm run dev
```

Open `http://localhost:3000`. The frontend calls the API at
`http://localhost:8000` by default. `SearchDashboard` owns search loading,
year/laboratory/team filtering, expandable abstracts, and PDF links. The
faculty directory filters by laboratory and links to static dynamic routes
generated from `faculty_metrics.json`.

For a production build:

```powershell
npm run build
npm run start
```

## Search request flow

1. The navbar submits a query to the client search dashboard.
2. FastAPI encodes the query with the same embedding model used at indexing
   time and queries ChromaDB using cosine similarity.
3. API results combine Chroma metadata with the raw/enrichment lookup when
   metadata is incomplete.
4. The frontend applies local filters for publication year, laboratory, and
   team, while keeping category selections combinable.
5. Each result card displays publication metadata, can expand its abstract, and
   links to a local PDF or the external URL when available.

## Git and data files

`.gitkeep` only keeps an otherwise empty directory in Git; it does not control
whether neighboring files are tracked. The current `.gitignore` excludes
virtual environments, Python caches, `.env`, and generated frontend/build
directories. It does not ignore the tracked Parquet, JSON, or PDF data.

To verify and push data changes:

```powershell
git status --short
git ls-files data_pipeline/data
git add data_pipeline/data frontend/data/faculty_metrics.json
git commit -m "Update research data"
git push
```

Large future datasets should use Git LFS or external object storage instead of
blindly committing them to normal Git history. Never commit API keys or local
`.env` files.

## Known limitations

- Google Scholar and OpenAlex are external services and can rate-limit or
  change response formats.
- Only publications with usable abstracts enter the clean/vector datasets.
- A publication can exist in Parquet without having either a downloaded local
  PDF or an external open-access URL.
- The Chroma database is a local generated index and must be rebuilt when
  embeddings or metadata change.