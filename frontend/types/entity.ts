import type { Entity, EntityAttribute, DataQualityRecord } from '@prisma/client'

export type { Entity, EntityAttribute, DataQualityRecord }

export type EntityWithRelations = Entity & {
  attributes: EntityAttribute[]
  dataQuality: DataQualityRecord | null
}

export type SearchResult = {
  id: string
  name: string
  slug: string
  summary: string | null
  description: string | null
  entityType: string
  source: string
  status: string
  createdAt: Date
  updatedAt: Date
  rank?: number
}

export type SearchFilters = {
  query?: string
  type?: string
  page?: number
}

export type ApiResponse<T> = {
  data: T
  error?: string
}

export type PaginatedResponse<T> = {
  data: T[]
  total: number
  page: number
  pageSize: number
}