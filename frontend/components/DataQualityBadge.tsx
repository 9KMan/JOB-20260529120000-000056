import type { DataQualityRecord } from '@prisma/client'

interface DataQualityBadgeProps {
  quality: DataQualityRecord
}

export function DataQualityBadge({ quality }: DataQualityBadgeProps) {
  const score = Math.round(quality.overall * 100)
  
  const getColor = (s: number) => {
    if (s >= 80) return 'text-green-600 bg-green-50 border-green-200'
    if (s >= 60) return 'text-yellow-600 bg-yellow-50 border-yellow-200'
    return 'text-red-600 bg-red-50 border-red-200'
  }

  return (
    <div className={`inline-flex items-center gap-2 px-3 py-1 rounded-full border text-sm ${getColor(score)}`}>
      <span className="font-medium">Quality: {score}%</span>
      <div className="flex gap-3 text-xs opacity-80">
        <span title="Freshness">F: {Math.round(quality.freshness * 100)}%</span>
        <span title="Completeness">C: {Math.round(quality.completeness * 100)}%</span>
        <span title="Consistency">S: {Math.round(quality.consistency * 100)}%</span>
      </div>
    </div>
  )
}