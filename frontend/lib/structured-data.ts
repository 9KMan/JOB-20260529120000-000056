import type { EntityWithRelations } from '@/types/entity'

type SchemaOrgType = 'Product' | 'Place' | 'Person' | 'Organization' | 'Event' | 'Article'

interface JsonLdContext {
  '@context': 'https://schema.org'
}

interface JsonLdBase extends JsonLdContext {
  '@type': SchemaOrgType
  name: string
  description?: string
  url?: string
}

export function generateEntityJsonLd(entity: EntityWithRelations): JsonLdBase {
  const baseUrl = process.env.NEXT_PUBLIC_BASE_URL || 'https://platform.example.com'
  
  const jsonLd: JsonLdBase = {
    '@context': 'https://schema.org',
    '@type': entity.entityType as SchemaOrgType,
    name: entity.name,
    description: entity.description || undefined,
    url: `${baseUrl}/entity/${entity.slug}`,
  }

  // Add summary as abstract if present
  if (entity.summary) {
    (jsonLd as Record<string, unknown>).abstract = entity.summary
  }

  // Add structured attributes
  if (entity.attributes && entity.attributes.length > 0) {
    const additionalProperty = entity.attributes.map((attr) => ({
      '@type': 'PropertyValue',
      name: attr.key,
      value: attr.value,
    }))
    ;(jsonLd as Record<string, unknown>).additionalProperty = additionalProperty
  }

  // Add source information
  ;(jsonLd as Record<string, unknown>).source = entity.source

  return jsonLd
}

export function generateBreadcrumbJsonLd(
  items: Array<{ name: string; url: string }>
): Record<string, unknown> {
  return {
    '@context': 'https://schema.org',
    '@type': 'BreadcrumbList',
    itemListElement: items.map((item, index) => ({
      '@type': 'ListItem',
      position: index + 1,
      name: item.name,
      item: item.url,
    })),
  }
}

export function generateOrganizationJsonLd(): Record<string, unknown> {
  const baseUrl = process.env.NEXT_PUBLIC_BASE_URL || 'https://platform.example.com'
  
  return {
    '@context': 'https://schema.org',
    '@type': 'Organization',
    name: 'Data Platform',
    url: baseUrl,
    logo: `${baseUrl}/logo.png`,
  }
}