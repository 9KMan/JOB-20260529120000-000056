import { Suspense } from 'react'
import type { Metadata } from 'next'
import { searchEntities } from '@/lib/search'
import { EntityCard } from '@/components/EntityCard'
import { SearchFilters } from '@/components/SearchFilters'
import type { SearchResult } from '@/types/entity'

export const revalidate = 60

interface Props {
  searchParams: { q?: string; type?: string; page?: string }
}

export async function generateMetadata({ searchParams }: Props): Promise<Metadata> {
  const query = searchParams.q || ''
  return {
    title: query ? `Search: ${query}` : 'Search',
    description: 'Search the data platform',
  }
}

export default async function SearchPage({ searchParams }: Props) {
  const query = searchParams.q || ''
  const type = searchParams.type || ''
  const page = parseInt(searchParams.page || '1', 10)

  const { results, total } = await searchEntities({ query, type, page })
  const pageSize = 20
  const totalPages = Math.ceil(total / pageSize)

  return (
    <main className="container mx-auto py-8 px-4">
      <header className="mb-8">
        <h1 className="text-3xl font-bold mb-4">Search</h1>
        <SearchFilters
          initialQuery={query}
          initialType={type}
          onSearch={(q, t) => {
            const params = new URLSearchParams()
            if (q) params.set('q', q)
            if (t) params.set('type', t)
            window.location.href = `/search?${params.toString()}`
          }}
        />
      </header>

      <section>
        <div className="mb-4 text-muted-foreground">
          {total === 0 ? (
            <p>No results found</p>
          ) : (
            <p>Found {total} result{total !== 1 ? 's' : ''}</p>
          )}
        </div>

        <Suspense fallback={<div>Loading...</div>}>
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {(results as SearchResult[]).map((entity) => (
              <EntityCard key={entity.id} entity={entity} />
            ))}
          </div>
        </Suspense>

        {totalPages > 1 && (
          <nav className="flex justify-center gap-2 mt-8">
            {page > 1 && (
              <a
                href={`/search?q=${query}&type=${type}&page=${page - 1}`}
                className="px-4 py-2 border rounded hover:bg-secondary"
              >
                Previous
              </a>
            )}
            <span className="px-4 py-2">
              Page {page} of {totalPages}
            </span>
            {page < totalPages && (
              <a
                href={`/search?q=${query}&type=${type}&page=${page + 1}`}
                className="px-4 py-2 border rounded hover:bg-secondary"
              >
                Next
              </a>
            )}
          </nav>
        )}
      </section>
    </main>
  )
}