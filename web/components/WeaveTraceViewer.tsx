'use client';

import { AgentExecution, Credentials } from '@/types';
import { GitBranch } from 'lucide-react';

interface WeaveTraceViewerProps {
  execution: AgentExecution | null;
  credentials: Credentials;
}

export default function WeaveTraceViewer({
  execution,
  credentials,
}: WeaveTraceViewerProps) {
  const getWeaveUrl = () => {
    const entity = credentials.wandb_entity || 'your-entity';
    const project = credentials.wandb_project;
    return `https://wandb.ai/${entity}/${project}/weave`;
  };

  return (
    <div className="bg-slate-800 rounded-lg p-6">
      <div className="flex items-center gap-2 mb-4">
        <GitBranch className="text-primary-500" size={20} />
        <h2 className="text-xl font-bold text-white">Weave Traces</h2>
      </div>

      <div className="space-y-4">
        <p className="text-slate-300 text-sm">
          All agent operations are automatically traced to Weave. View the full
          call tree and execution details in the Weave UI.
        </p>

        <a
          href={getWeaveUrl()}
          target="_blank"
          rel="noopener noreferrer"
          className="block w-full px-4 py-3 bg-primary-600 hover:bg-primary-700 text-white rounded-lg transition-colors text-center"
        >
          Open Weave Dashboard
        </a>

        {execution && (
          <div className="mt-4 p-3 bg-slate-700 rounded-lg">
            <p className="text-slate-300 text-sm mb-2">
              <strong>Current Execution ID:</strong> {execution.id}
            </p>
            <p className="text-slate-400 text-xs">
              All traces for this execution are logged with this ID.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
