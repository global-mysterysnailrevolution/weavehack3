'use client';

import { Observation } from '@/types';
import { Eye } from 'lucide-react';

interface ObservationViewerProps {
  observation: Observation | undefined;
}

export default function ObservationViewer({ observation }: ObservationViewerProps) {
  return (
    <div className="bg-slate-800 rounded-lg p-6">
      <div className="flex items-center gap-2 mb-4">
        <Eye className="text-primary-500" size={20} />
        <h2 className="text-xl font-bold text-white">Current Observation</h2>
      </div>

      {observation ? (
        <div className="space-y-4">
          <div>
            <p className="text-sm text-slate-400 mb-1">URL</p>
            <p className="text-white text-sm break-all">{observation.url}</p>
          </div>

          {observation.screenshot_base64 && (
            <div>
              <p className="text-sm text-slate-400 mb-2">Screenshot</p>
              <img
                src={`data:image/png;base64,${observation.screenshot_base64}`}
                alt="Current page screenshot"
                className="w-full rounded-lg border border-slate-600"
              />
            </div>
          )}

          {observation.metadata && Object.keys(observation.metadata).length > 0 && (
            <div>
              <p className="text-sm text-slate-400 mb-2">Metadata</p>
              <pre className="bg-slate-900 p-3 rounded-lg text-xs text-slate-300 overflow-x-auto">
                {JSON.stringify(observation.metadata, null, 2)}
              </pre>
            </div>
          )}
        </div>
      ) : (
        <div className="text-slate-500 text-center py-8">
          No observation yet. The agent will capture screenshots as it navigates.
        </div>
      )}
    </div>
  );
}
