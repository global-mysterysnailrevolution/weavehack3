import { NextRequest } from 'next/server';

export const runtime = 'nodejs';
export const dynamic = 'force-dynamic';

export async function POST(req: NextRequest) {
  try {
    const { goal, credentials } = await req.json();

    // For now, return a mock response
    // In production, this would connect to a Python backend API
    // or use Vercel serverless functions to run Python
    
    const encoder = new TextEncoder();
    const stream = new ReadableStream({
      async start(controller) {
        // Send start event
        controller.enqueue(encoder.encode(`data: ${JSON.stringify({ type: 'start', goal })}\n\n`));
        await new Promise(resolve => setTimeout(resolve, 500));

        // In production, this would connect to the actual Python backend
        // For now, return a minimal response indicating the agent is processing
        controller.enqueue(encoder.encode(`data: ${JSON.stringify({ 
          type: 'action', 
          step: 1, 
          action: { 
            type: 'act', 
            payload: { 
              command: 'process', 
              target: goal 
            } 
          } 
        })}\n\n`));
        await new Promise(resolve => setTimeout(resolve, 500));

        controller.enqueue(encoder.encode(`data: ${JSON.stringify({ 
          type: 'observation', 
          observation: { 
            status: 'processing',
            goal: goal,
            metadata: {} 
          } 
        })}\n\n`));
        await new Promise(resolve => setTimeout(resolve, 500));

        controller.enqueue(encoder.encode(`data: ${JSON.stringify({ 
          type: 'events', 
          events: [`process:${goal.substring(0, 50)}...`] 
        })}\n\n`));
        await new Promise(resolve => setTimeout(resolve, 500));

        controller.enqueue(encoder.encode(`data: ${JSON.stringify({ 
          type: 'complete', 
          score: 0.85, 
          total_steps: 1 
        })}\n\n`));

        controller.close();
      },
    });

    return new Response(stream, {
      headers: {
        'Content-Type': 'text/event-stream',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
      },
    });
  } catch (error: any) {
    return new Response(
      JSON.stringify({ error: error.message }),
      { status: 500, headers: { 'Content-Type': 'application/json' } }
    );
  }
}
