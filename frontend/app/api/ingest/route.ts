import { NextRequest, NextResponse } from 'next/server'

// This endpoint is for internal use to trigger ingestion
// In production, this should be secured with an API key or internal network restriction
export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    const { sources } = body

    if (!sources || !Array.isArray(sources)) {
      return NextResponse.json(
        { error: 'Invalid request: sources array required' },
        { status: 400 }
      )
    }

    // Forward to ETL service
    const etlUrl = process.env.ETL_URL || 'http://localhost:8000'
    
    try {
      const response = await fetch(`${etlUrl}/ingest`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ sources }),
      })

      if (!response.ok) {
        throw new Error(`ETL service returned ${response.status}`)
      }

      const result = await response.json()
      return NextResponse.json(result)
    } catch (error) {
      console.error('ETL service error:', error)
      return NextResponse.json(
        { error: 'Ingestion service unavailable' },
        { status: 503 }
      )
    }
  } catch (error) {
    console.error('Ingest route error:', error)
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    )
  }
}