'use client'

import { useState } from 'react'
import { Search, Filter } from 'lucide-react'

interface SearchFiltersProps {
  onSearch: (query: string, type: string) => void
  initialQuery?: string
  initialType?: string
}

const ENTITY_TYPES = ['Product', 'Place', 'Person', 'Organization', 'Event', 'Article']

export function SearchFilters({ onSearch, initialQuery = '', initialType = '' }: SearchFiltersProps) {
  const [query, setQuery] = useState(initialQuery)
  const [type, setType] = useState(initialType)

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    onSearch(query, type)
  }

  return (
    <form onSubmit={handleSubmit} className="flex flex-col sm:flex-row gap-3">
      <div className="relative flex-1">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search entities..."
          className="w-full pl-10 pr-4 py-2 border rounded-lg text-sm"
        />
      </div>
      <div className="relative">
        <Filter className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
        <select
          value={type}
          onChange={(e) => setType(e.target.value)}
          className="pl-10 pr-8 py-2 border rounded-lg text-sm appearance-none bg-white"
        >
          <option value="">All Types</option>
          {ENTITY_TYPES.map((t) => (
            <option key={t} value={t}>{t}</option>
          ))}
        </select>
      </div>
      <button
        type="submit"
        className="px-4 py-2 bg-primary text-primary-foreground rounded-lg text-sm font-medium hover:opacity-90"
      >
        Search
      </button>
    </form>
  )
}