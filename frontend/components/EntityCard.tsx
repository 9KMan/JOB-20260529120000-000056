import Link from 'next/link'
import type { SearchResult } from '@/types/entity'

interface EntityCardProps {
  entity: SearchResult
}

export function EntityCard({ entity }: EntityCardProps) {
  return (
    <Link
      href={`/entity/${entity.slug}`}
      className="block p-4 border rounded-lg hover:border-primary hover:shadow-sm transition-colors"
    >
      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0 flex-1">
          <h3 className="font-semibold text-lg truncate">{entity.name}</h3>
          {entity.summary && (
            <p className="mt-1 text-sm text-muted-foreground line-clamp-2">
              {entity.summary}
            </p>
          )}
          <div className="mt-2 flex items-center gap-2">
            <span className="text-xs px-2 py-0.5 bg-secondary rounded">{entity.entityType}</span>
            <span className="text-xs text-muted-foreground">{entity.source}</span>
          </div>
        </div>
      </div>
    </Link>
  )
}