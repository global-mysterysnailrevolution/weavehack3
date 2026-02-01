'use client';

import { Action } from '@/types';
import { Activity } from 'lucide-react';

interface ActionHistoryProps {
  actions: Action[];
}

export default function ActionHistory({ actions }: ActionHistoryProps) {
  return (
    <div className="bg-slate-800 rounded-lg p-6">
      <div className="flex items-center gap-2 mb-4">
        <Activity className="text-primary-500" size={20} />
        <h2 className="text-xl font-bold text-white">Action History</h2>
      </div>

      <div className="space-y-2 max-h-64 overflow-y-auto">
        {actions.length > 0 ? (
          actions.map((action, idx) => (
            <div
              key={idx}
              className="bg-slate-700 rounded-lg p-3 border-l-4 border-primary-500"
            >
              <div className="flex items-center justify-between mb-2">
                <span className="text-primary-400 font-medium text-sm">
                  {action.type.toUpperCase()}
                </span>
                <span className="text-slate-400 text-xs">
                  {new Date(action.timestamp).toLocaleTimeString()}
                </span>
              </div>
              
              {action.reasoning && (
                <p className="text-slate-300 text-sm mb-2">{action.reasoning}</p>
              )}

              <pre className="bg-slate-900 p-2 rounded text-xs text-slate-400 overflow-x-auto">
                {JSON.stringify(action.payload, null, 2)}
              </pre>
            </div>
          ))
        ) : (
          <div className="text-slate-500 text-center py-8">
            No actions yet. Actions will appear here as the agent executes.
          </div>
        )}
      </div>
    </div>
  );
}
