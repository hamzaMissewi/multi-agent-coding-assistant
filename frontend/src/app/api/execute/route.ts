import { NextRequest, NextResponse } from 'next/server';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { project_path } = body;

    // Call the Python backend for project execution
    const response = await fetch('http://localhost:8000/execute', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ project_path }),
    });

    if (!response.ok) {
      throw new Error(`Backend error: ${response.statusText}`);
    }

    const result = await response.json();
    return NextResponse.json(result);

  } catch (error) {
    console.error('Execution error:', error);
    return NextResponse.json(
      { error: 'Failed to execute project' },
      { status: 500 }
    );
  }
}
