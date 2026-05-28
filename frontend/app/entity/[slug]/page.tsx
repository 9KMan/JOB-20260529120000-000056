import { Suspense } from 'react'
import { notFound } from 'next/navigation'
import Link from 'next/link'
import type { Metadata } from 'next'
import { prisma } from '@/lib/prisma'
import { getEntityBySlug } from '@/lib/search'
import { generateEntityJsonLd, generateBreadcrumbJsonLd } from '@/lib/structured-data'
import { JsonLd } from '@/components/JsonLd'
import { DataQualityBadge } from '@/components/DataQualityBadge'
import type { EntityWithRelations } from '@/types/entity'

export const revalidate = 60 // ISR: Revalidate every 60s

interface Props {
  params: { slug: string }
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const entity = await getEntityBySlug(params.slug)
  if (!entity) return { title: 'Not Found' }
  
  return {
    title: entity.name,
    description: entity.description || entity.summary || undefined,
  }
}

export default async function EntityPage({ params }: Props) {
  const entity = await getEntityBySlug(params.slug) as EntityWithRelations | null
  
  if (!entity) {
    notFound()
  }

  const baseUrl = process.env.NEXT_PUBLIC_BASE_URL || 'https://platform.example.com'
  const jsonLd = generateEntityJsonLd(entity)
  const breadcrumbJsonLd = generateBreadcrumbJsonLd([
    { name: 'Home', url: baseUrl },
    { name: entity.name, url: `${baseUrl}/entity/${entity.slug}` },
  ])

  return (
    <>
      <JsonLd data={jsonLd} />
      <JsonLd data={breadcrumbJsonLd} />
      
      <main className="container mx-auto py-8 px-4">
        <nav className="text-sm mb-6">
          <Link href="/" className="text-primary hover:underline">Home</Link>
          <span className="mx-2 text-muted-foreground">/</span>
          <span className="text-muted-foreground">{entity.entityType}</span>
        </nav>

        <article>
          <header className="mb-6">
            <div className="flex items-start justify-between gap-4">
              <div>
                <h1 className="text-4xl font-bold mb-2">{entity.name}</h1>
                <div className="flex items-center gap-3">
                  <span className="text-sm px-3 py-1 bg-secondary rounded-full">
                    {entity.entityType}
                  </span>
                  <span className="text-sm text-muted-foreground">
                    Source: {entity.source}
                  </span>
                </div>
              </div>
              {entity.dataQuality && (
                <DataQualityBadge quality={entity.dataQuality} />
              )}
            </div>
          </header>

          {entity.summary && (
            <section className="mb-6">
              <p className="text-lg text-muted-foreground">{entity.summary}</p>
            </section>
          )}

          {entity.description && (
            <section className="prose max-w-none mb-8">
              <h2 className="text-2xl font-semibold mb-3">Description</h2>
              <p className="text-base leading-relaxed">{entity.description}</p>
            </section>
          )}

          {entity.attributes && entity.attributes.length > 0 && (
            <section className="mb-8">
              <h2 className="text-2xl font-semibold mb-3">Attributes</h2>
              <dl className="grid gap-2">
                {entity.attributes.map((attr) => (
                  <div key={attr.id} className="flex gap-4 p-3 bg-secondary rounded">
                    <dt className="font-medium text-muted-foreground min-w-[120px]">
                      {attr.key}
                    </dt>
                    <dd className="text-sm">{attr.value}</dd>
                  </div>
                ))}
              </dl>
            </section>
          )}

          {entity.relationsFrom && entity.relationsFrom.length > 0 && (
            <section className="mb-8">
              <h2 className="text-2xl font-semibold mb-3">Related Entities</h2>
              <ul className="space-y-2">
                {entity.relationsFrom.map((rel) => (
                  <li key={rel.id}>
                    <Link
                      href={`/entity/${rel.to.slug}`}
                      className="text-primary hover:underline"
                    >
                      {rel.to.name}
                    </Link>
                    <span className="text-sm text-muted-foreground ml-2">
                      ({rel.relationType})
                    </span>
                  </li>
                ))}
              </ul>
            </section>
          )}
        </article>
      </main>
    </>
  )
}