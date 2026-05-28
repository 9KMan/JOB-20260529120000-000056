import { NextRequest, NextResponse } from 'next/server'
import { searchEntities } from '@/lib/search'

export async function GET(request: NextRequest) {
  const searchParams = request.nextUrl.searchParams
  const query = searchParams.get('q') || ''
  const type = searchParams.get('type') || ''
  const page = parseInt(searchParams.get('page') || '1', 10)

  try {
    const { results, total } = await searchEntities({ query, type, page })
    
    return NextResponse.json({
      data: results,
      total,
      page,
      pageSize: 20,
    })
  } catch (error) {
    console.error('Search error:', error)
    return NextResponse.json(
      { error: 'Search failed' },
      { status: 500 }
    )
  }
}