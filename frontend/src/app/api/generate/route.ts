import { NextRequest, NextResponse } from 'next/server';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { user_request, project_name, complexity, preferences } = body;

    // Call the Python backend
    const response = await fetch('http://localhost:8000/generate', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        user_request,
        project_name,
        complexity,
        preferences
      }),
    });

    if (!response.ok) {
      throw new Error(`Backend error: ${response.statusText}`);
    }

    const result = await response.json();
    return NextResponse.json(result);

  } catch (error) {
    console.error('Generation error:', error);
    return NextResponse.json(
      { error: 'Failed to generate project' },
      { status: 500 }
    );
  }
}
