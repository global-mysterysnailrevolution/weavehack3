'use client';

import { AgentExecution } from '@/types';
import { Network } from 'lucide-react';

interface RLMVisualizationProps {
  execution: AgentExecution | null;
}

export default function RLMVisualization({ execution }: RLMVisualizationProps) {
  // Extract RLM-related events
  const rlmEvents = execution?.events.filter((e) =>
    e.includes('rlm') || e.includes('context_examination') || e.includes('subcall')
  ) || [];

  return (
    <div className="bg-slate-800 rounded-lg p-6">
      <div className="flex items-center gap-2 mb-4">
        <Network className="text-primary-500" size={20} />
        <h2 className="text-xl font-bold text-white">RLM Context Examination</h2>
      </div>

      <div className="space-y-3">
        {rlmEvents.length > 0 ? (
          rlmEvents.map((event, idx) => (
            <div
              key={idx}
              className="bg-slate-700 rounded-lg p-3 border-l-4 border-purple-500"
            >
              <p className="text-slate-300 text-sm">{event}</p>
            </div>
          ))
        ) : (
          <div className="text-slate-500 text-center py-8 text-sm">
            RLM context examination events will appear here when the agent
            processes long contexts or makes recursive subcalls.
          </div>
        )}
      </div>

      {execution && execution.trajectory.some((a) => a.type === 'subcall') && (
        <div className="mt-4 p-3 bg-purple-900/30 border border-purple-700 rounded-lg">
          <p className="text-purple-300 text-sm">
            <strong>RLM Active:</strong> The agent is using recursive decomposition
            to handle complex tasks.
          </p>
        </div>
      )}
    </div>
  );
}
