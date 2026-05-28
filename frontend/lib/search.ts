import { prisma } from './prisma'
import { Prisma } from '@prisma/client'
import type { SearchFilters, SearchResult } from '@/types/entity'

export async function searchEntities(
  filters: SearchFilters
): Promise<{ results: SearchResult[]; total: number }> {
  const { query, type, page = 1 } = filters
  const pageSize = 20
  const skip = (page - 1) * pageSize

  const where = type ? { entityType: type, status: 'VALIDATED' as const } : { status: 'VALIDATED' as const }

  if (!query?.trim()) {
    const [results, total] = await Promise.all([
      prisma.entity.findMany({
        where,
        take: pageSize,
        skip,
        orderBy: { createdAt: 'desc' },
      }),
      prisma.entity.count({ where }),
    ])
    return { results, total }
  }

  // PostgreSQL full-text search with ranking
  const results = await prisma.$queryRaw<SearchResult[]>`
    SELECT *,
           ts_rank("searchVector", plainto_tsquery('english', ${query})) AS rank
    FROM "Entity"
    WHERE "searchVector" @@ plainto_tsquery('english', ${query})
      AND status = 'VALIDATED'
      ${type ? Prisma.sql`AND "entityType" = ${type}` : Prisma.sql``}
    ORDER BY rank DESC
    LIMIT ${pageSize} OFFSET ${skip}
  `

  const countQuery = Prisma.sql`
    SELECT COUNT(*)::int as count
    FROM "Entity"
    WHERE "searchVector" @@ plainto_tsquery('english', ${query})
      AND status = 'VALIDATED'
      ${type ? Prisma.sql`AND "entityType" = ${type}` : Prisma.sql``}
  `
  const [{ count: total }] = await prisma.$queryRaw<[{ count: number }]>(countQuery)

  return { results, total }
}

export async function getEntityBySlug(slug: string) {
  return prisma.entity.findUnique({
    where: { slug },
    include: {
      attributes: true,
      dataQuality: true,
      relationsFrom: {
        include: {
          to: true,
        },
      },
      relationsTo: {
        include: {
          from: true,
        },
      },
    },
  })
}

export async function getEntities(opts: { take?: number; skip?: number } = {}) {
  const { take = 20, skip = 0 } = opts
  return prisma.entity.findMany({
    where: { status: 'VALIDATED' },
    take,
    skip,
    orderBy: { createdAt: 'desc' },
  })
}