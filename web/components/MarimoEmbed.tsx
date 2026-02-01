'use client';

import { useState } from 'react';
import { TrendingUp, RefreshCw, ExternalLink } from 'lucide-react';

interface MarimoEmbedProps {
  src?: string;
  execution?: any;
}

export default function MarimoEmbed({ src, execution }: MarimoEmbedProps) {
  const [isRefreshing, setIsRefreshing] = useState(false);
  const iframeSrc = src || '/api/marimo?embed=true&mode=read';
  
  const handleRefresh = () => {
    setIsRefreshing(true);
    const iframe = document.querySelector('iframe[title="Marimo Weave Dashboard"]') as HTMLIFrameElement;
    if (iframe) {
      iframe.src = iframe.src; // Force reload
      setTimeout(() => setIsRefreshing(false), 1000);
    }
  };

  if (!iframeSrc || iframeSrc.includes('<your-notebook-id>')) {
    return (
      <div className="bg-slate-800 rounded-lg p-6">
        <div className="flex items-center gap-2 mb-4">
          <TrendingUp className="text-primary-500" size={24} />
          <h2 className="text-xl font-bold text-white">Agent Improvement Dashboard</h2>
        </div>
        <div className="rounded-lg border border-slate-700 bg-slate-900/40 p-6 text-slate-300">
          <p className="text-sm mb-4">
            Connect Marimo to visualize agent improvements from Weave traces.
          </p>
          <div className="space-y-2 text-sm">
            <p>To enable:</p>
            <ol className="list-decimal list-inside space-y-1 ml-2">
              <li>Set <code className="text-slate-200 bg-slate-800 px-1 rounded">MARIMO_PROXY_URL</code> in Vercel environment variables</li>
              <li>Point it to your published Marimo notebook (e.g., <code className="text-slate-200 bg-slate-800 px-1 rounded">https://marimo.app/l/...</code>)</li>
              <li>The dashboard will show Weave traces, agent performance, and improvement suggestions</li>
            </ol>
            <div className="mt-4 p-3 bg-primary-900/20 border border-primary-700 rounded-lg">
              <p className="text-primary-300 text-xs">
                <strong>Tip:</strong> The Marimo dashboard analyzes Weave traces to show how the agent improves over time, 
                including success rates, action patterns, and optimization opportunities.
              </p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-slate-800 rounded-lg p-6">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <TrendingUp className="text-primary-500" size={24} />
          <h2 className="text-xl font-bold text-white">Agent Improvement Dashboard</h2>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={handleRefresh}
            disabled={isRefreshing}
            className="px-3 py-1.5 bg-slate-700 hover:bg-slate-600 text-white rounded-lg transition-colors flex items-center gap-2 text-sm disabled:opacity-50"
            title="Refresh dashboard"
          >
            <RefreshCw size={16} className={isRefreshing ? 'animate-spin' : ''} />
            Refresh
          </button>
          <a
            href={iframeSrc}
            target="_blank"
            rel="noopener noreferrer"
            className="px-3 py-1.5 bg-slate-700 hover:bg-slate-600 text-white rounded-lg transition-colors flex items-center gap-2 text-sm"
            title="Open in new tab"
          >
            <ExternalLink size={16} />
            Open
          </a>
        </div>
      </div>
      
      {execution && execution.status === 'completed' && (
        <div className="mb-4 p-3 bg-primary-900/20 border border-primary-700 rounded-lg">
          <p className="text-primary-300 text-sm">
            <strong>Latest run completed!</strong> Check the dashboard below to see how this execution 
            compares to previous runs and identify improvement opportunities.
          </p>
        </div>
      )}

      <div className="rounded-lg border border-slate-700 bg-slate-950/50 overflow-hidden">
        <iframe
          src={iframeSrc}
          title="Marimo Weave Dashboard"
          width="100%"
          height="700"
          sandbox="allow-scripts allow-same-origin allow-downloads allow-popups allow-downloads-without-user-activation allow-forms"
          allow="microphone"
          allowFullScreen
          className="w-full"
          style={{ border: '0', minHeight: '700px' }}
        />
      </div>
      
      <div className="mt-4 text-xs text-slate-400">
        <p>
          This dashboard shows real-time Weave traces, agent performance metrics, and improvement suggestions 
          based on your agent's execution history.
        </p>
      </div>
    </div>
  );
}
