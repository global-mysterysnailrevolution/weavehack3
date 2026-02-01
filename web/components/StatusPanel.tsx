'use client';

import { AgentExecution } from '@/types';
import { CheckCircle, XCircle, Loader2, Circle, ChefHat } from 'lucide-react';

interface StatusPanelProps {
  execution: AgentExecution | null;
  onCookLonger?: () => void;
}

export default function StatusPanel({ execution, onCookLonger }: StatusPanelProps) {
  const getStatusIcon = () => {
    if (!execution) return <Circle className="text-slate-400" size={24} />;
    
    switch (execution.status) {
      case 'running':
        return <Loader2 className="text-primary-500 animate-spin" size={24} />;
      case 'completed':
        return <CheckCircle className="text-green-500" size={24} />;
      case 'error':
        return <XCircle className="text-red-500" size={24} />;
      default:
        return <Circle className="text-slate-400" size={24} />;
    }
  };

  const getStatusText = () => {
    if (!execution) return 'Idle';
    return execution.status.charAt(0).toUpperCase() + execution.status.slice(1);
  };

  return (
    <div className="bg-slate-800 rounded-lg p-6">
      <h2 className="text-xl font-bold text-white mb-4">Status</h2>
      
      <div className="space-y-4">
        <div className="flex items-center gap-3">
          {getStatusIcon()}
          <span className="text-white font-medium">{getStatusText()}</span>
        </div>

        {execution && (
          <>
            <div className="text-sm text-slate-300">
              <div className="mb-2">Step: {execution.current_step}</div>
              {execution.total_steps && (
                <div className="mb-2">Total Steps: {execution.total_steps}</div>
              )}
              {execution.score !== undefined && (
                <div className="mb-2">Score: {execution.score.toFixed(2)}</div>
              )}
            </div>

            {execution.status === 'running' && execution.total_steps && (
              <div className="w-full bg-slate-700 rounded-full h-2">
                <div
                  className="bg-primary-500 h-2 rounded-full transition-all duration-300"
                  style={{
                    width: `${(execution.current_step / execution.total_steps) * 100}%`,
                  }}
                />
              </div>
            )}

            {execution.error && (
              <div className="mt-4 p-3 bg-red-900/30 border border-red-700 rounded-lg">
                <p className="text-red-400 text-sm">{execution.error}</p>
              </div>
            )}

            {execution.status === 'completed' && onCookLonger && (
              <button
                onClick={onCookLonger}
                className="mt-4 w-full px-4 py-3 bg-orange-600 hover:bg-orange-700 text-white rounded-lg transition-colors flex items-center justify-center gap-2 font-medium"
              >
                <ChefHat size={20} />
                Cook Longer
              </button>
            )}
          </>
        )}
      </div>
    </div>
  );
}
