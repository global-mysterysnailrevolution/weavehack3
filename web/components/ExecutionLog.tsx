'use client';

import { AgentExecution } from '@/types';
import { Terminal } from 'lucide-react';
import { useEffect, useRef } from 'react';

interface ExecutionLogProps {
  execution: AgentExecution | null;
}

export default function ExecutionLog({ execution }: ExecutionLogProps) {
  const logEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    logEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [execution?.events]);

  return (
    <div className="bg-slate-800 rounded-lg p-6">
      <div className="flex items-center gap-2 mb-4">
        <Terminal className="text-primary-500" size={20} />
        <h2 className="text-xl font-bold text-white">Execution Log</h2>
      </div>
      
      <div className="bg-slate-900 rounded-lg p-4 h-64 overflow-y-auto font-mono text-sm">
        {execution?.events.length ? (
          <>
            {execution.events.map((event, idx) => (
              <div key={idx} className="text-slate-300 mb-1">
                <span className="text-slate-500">[{idx + 1}]</span> {event}
              </div>
            ))}
            <div ref={logEndRef} />
          </>
        ) : (
          <div className="text-slate-500 text-center py-8">
            No events yet. Start the agent to see execution logs.
          </div>
        )}
      </div>
    </div>
  );
}
