import { Suspense } from 'react'
import Link from 'next/link'
import { prisma } from '@/lib/prisma'
import { EntityCard } from '@/components/EntityCard'
import { SearchFilters } from '@/components/SearchFilters'
import type { SearchResult } from '@/types/entity'

export const revalidate = 60 // ISR: Revalidate every 60s

async function getEntities(): Promise<SearchResult[]> {
  return prisma.entity.findMany({
    where: { status: 'VALIDATED' },
    take: 20,
    orderBy: { createdAt: 'desc' },
    select: {
      id: true,
      name: true,
      slug: true,
      summary: true,
      description: true,
      entityType: true,
      source: true,
      status: true,
      createdAt: true,
      updatedAt: true,
    },
  })
}

async function getRecentEntities() {
  return getEntities()
}

function EntityList({ entities }: { entities: SearchResult[] }) {
  if (entities.length === 0) {
    return (
      <div className="text-center py-12 text-muted-foreground">
        <p className="text-lg">No entities found.</p>
        <p className="text-sm mt-1">Try adjusting your search or browse all entities.</p>
      </div>
    )
  }

  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
      {entities.map((entity) => (
        <EntityCard key={entity.id} entity={entity} />
      ))}
    </div>
  )
}

export default async function HomePage() {
  const entities = await getRecentEntities()

  return (
    <main className="container mx-auto py-8 px-4">
      <header className="mb-8">
        <h1 className="text-4xl font-bold mb-2">Data Platform</h1>
        <p className="text-muted-foreground">
          Multi-source data ingestion, search, and discovery
        </p>
      </header>

      <section className="mb-8">
        <SearchFilters onSearch={(query, type) => {
          const params = new URLSearchParams()
          if (query) params.set('q', query)
          if (type) params.set('type', type)
          window.location.href = `/search?${params.toString()}`
        }} />
      </section>

      <section>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-2xl font-semibold">Recent Entities</h2>
          <Link href="/search" className="text-sm text-primary hover:underline">
            View all →
          </Link>
        </div>
        <Suspense fallback={<div>Loading...</div>}>
          <EntityList entities={entities} />
        </Suspense>
      </section>
    </main>
  )
}