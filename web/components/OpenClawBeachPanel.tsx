import { useMemo, useState } from 'react';
import { Credentials, AgentExecution } from '@/types';

interface OpenClawBeachPanelProps {
  credentials: Credentials;
  execution: AgentExecution | null;
  onUpdateExecution: (update: (prev: AgentExecution | null) => AgentExecution) => void;
}

type OpenClawMode = 'beach' | 'sea';

export default function OpenClawBeachPanel({
  credentials,
  execution,
  onUpdateExecution,
}: OpenClawBeachPanelProps) {
  const [goal, setGoal] = useState('');
  const [isRunning, setIsRunning] = useState(false);
  const [iteration, setIteration] = useState(0);
  const [logs, setLogs] = useState<Array<{ timestamp: string; type: string; message: string; data?: any }>>([]);
  const [score, setScore] = useState<number | null>(null);
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [showFullLogs, setShowFullLogs] = useState(false);
  const [filterType, setFilterType] = useState<string>('all');

  const apiBase = process.env.NEXT_PUBLIC_API_BASE_URL || '';
  const openclawBase = useMemo(() => {
    if (!apiBase) return '';
    return apiBase.replace(/\/$/, '');
  }, [apiBase]);

  const runOpenClaw = async (mode: OpenClawMode, nextIteration: number) => {
    if (!goal.trim()) return;
    setIsRunning(true);
    setLogs([]);
    setScore(null);
    setSuggestions([]);

    const execId = execution?.id || `exec_${Date.now()}`;
    onUpdateExecution((prev) => ({
      ...(prev || {
        id: execId,
        goal,
        status: 'running',
        current_step: 0,
        trajectory: [],
        events: [],
      }),
      status: 'running',
    }));

    const endpoint = openclawBase
      ? `${openclawBase}/api/openclaw/${mode}`
      : `/api/openclaw/${mode}`;

    try {
      const response = await fetch(endpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          goal,
          iteration: nextIteration,
          credentials,
        }),
      });

      if (!response.ok) {
        throw new Error(`OpenClaw ${mode} failed: ${response.status}`);
      }

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();
      if (!reader) {
        throw new Error('No response stream');
      }

      let buffer = '';
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (!line.startsWith('data: ')) continue;
          const payload = line.slice(6);
          try {
            const data = JSON.parse(payload);
            const timestamp = new Date().toISOString();
            
            if (data.type === 'openclaw_log') {
              setLogs((prev) => [...prev, {
                timestamp,
                type: 'log',
                message: data.message,
              }]);
            } else if (data.type === 'openclaw_event') {
              setLogs((prev) => [...prev, {
                timestamp,
                type: 'event',
                message: `Event: ${data.payload?.type || 'unknown'}`,
                data: data.payload,
              }]);
            } else if (data.type === 'openclaw_start') {
              setLogs((prev) => [...prev, {
                timestamp,
                type: 'start',
                message: `Starting ${data.mode} mode (iteration ${data.iteration})`,
                data: { mode: data.mode, goal: data.goal, iteration: data.iteration },
              }]);
            } else if (data.type === 'openclaw_score') {
              setScore(data.score);
              setLogs((prev) => [...prev, {
                timestamp,
                type: 'score',
                message: `Score: ${data.score.toFixed(2)}`,
                data: { score: data.score },
              }]);
            } else if (data.type === 'openclaw_suggestions') {
              setSuggestions(Array.isArray(data.suggestions) ? data.suggestions : []);
              setLogs((prev) => [...prev, {
                timestamp,
                type: 'suggestions',
                message: `Generated ${data.suggestions?.length || 0} suggestions`,
                data: { suggestions: data.suggestions },
              }]);
            } else if (data.type === 'openclaw_complete') {
              setLogs((prev) => [...prev, {
                timestamp,
                type: 'complete',
                message: `Complete (exit code: ${data.exit_code})`,
                data: { exit_code: data.exit_code, mode: data.mode },
              }]);
            } else if (data.type === 'error') {
              setLogs((prev) => [...prev, {
                timestamp,
                type: 'error',
                message: `Error: ${data.error}`,
                data: { error: data.error },
              }]);
            } else {
              // Capture any other event types
              setLogs((prev) => [...prev, {
                timestamp,
                type: data.type || 'unknown',
                message: JSON.stringify(data),
                data,
              }]);
            }

            onUpdateExecution((prev) => ({
              ...(prev || {
                id: execId,
                goal,
                status: 'running',
                current_step: 0,
                trajectory: [],
                events: [],
              }),
              events: [
                ...(prev?.events || []),
                `[${mode}] ${data.type}: ${data.message || data.error || ''}`.trim(),
              ],
            }));
          } catch (err) {
            setLogs((prev) => [...prev, `Parse error: ${String(err)}`]);
          }
        }
      }

      setIteration(nextIteration);
      onUpdateExecution((prev) => ({
        ...(prev || {
          id: execId,
          goal,
          status: 'running',
          current_step: 0,
          trajectory: [],
          events: [],
        }),
        status: prev?.status === 'error' ? 'error' : 'completed',
      }));
    } catch (err: any) {
      onUpdateExecution((prev) => ({
        ...(prev || {
          id: execId,
          goal,
          status: 'running',
          current_step: 0,
          trajectory: [],
          events: [],
        }),
        status: 'error',
        error: err.message,
      }));
    } finally {
      setIsRunning(false);
    }
  };

  return (
    <div className="bg-slate-800 rounded-lg p-6 space-y-4">
      <div>
        <h2 className="text-xl font-bold text-white">OpenClaw Beach</h2>
        <p className="text-sm text-slate-300">
          Iterate in the sandbox (the beach) before releasing to the sea.
        </p>
      </div>

      <textarea
        value={goal}
        onChange={(e) => setGoal(e.target.value)}
        placeholder="Enter OpenClaw task... e.g., Verify shopbiolinkdepot pricing and compare vendors"
        className="w-full px-4 py-3 bg-slate-700 text-white rounded-lg border border-slate-600 focus:border-primary-500 focus:outline-none resize-none"
        rows={4}
        disabled={isRunning}
      />

      <div className="grid grid-cols-1 gap-3">
        <button
          type="button"
          onClick={() => runOpenClaw('beach', 0)}
          disabled={!goal.trim() || isRunning}
          className="px-4 py-3 bg-amber-500 hover:bg-amber-600 disabled:bg-slate-600 disabled:cursor-not-allowed text-white rounded-lg transition-colors"
        >
          Run on the Beach
        </button>
        <button
          type="button"
          onClick={() => runOpenClaw('beach', iteration + 1)}
          disabled={!goal.trim() || isRunning}
          className="px-4 py-3 bg-amber-700 hover:bg-amber-800 disabled:bg-slate-600 disabled:cursor-not-allowed text-white rounded-lg transition-colors"
        >
          Cook Longer (Iterate)
        </button>
        <button
          type="button"
          onClick={() => runOpenClaw('sea', iteration)}
          disabled={!goal.trim() || isRunning}
          className="px-4 py-3 bg-emerald-600 hover:bg-emerald-700 disabled:bg-slate-600 disabled:cursor-not-allowed text-white rounded-lg transition-colors"
        >
          Release to Sea
        </button>
      </div>

      <div className="rounded-lg border border-slate-700 bg-slate-900/40 p-3 space-y-2">
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-2">
            <span className="text-sm font-semibold text-white">OpenClaw Activity Log</span>
            <span className="text-xs text-slate-400">({logs.length} entries)</span>
          </div>
          <div className="flex items-center gap-2">
            <select
              value={filterType}
              onChange={(e) => setFilterType(e.target.value)}
              className="px-2 py-1 bg-slate-700 text-white text-xs rounded border border-slate-600"
            >
              <option value="all">All</option>
              <option value="log">Logs</option>
              <option value="event">Events</option>
              <option value="start">Start</option>
              <option value="score">Scores</option>
              <option value="suggestions">Suggestions</option>
              <option value="complete">Complete</option>
              <option value="error">Errors</option>
            </select>
            <button
              onClick={() => setShowFullLogs(!showFullLogs)}
              className="px-2 py-1 bg-slate-700 hover:bg-slate-600 text-white text-xs rounded transition-colors"
            >
              {showFullLogs ? 'Collapse' : 'Expand'}
            </button>
          </div>
        </div>
        
        <div className={`bg-slate-950 rounded p-2 font-mono text-xs overflow-y-auto ${showFullLogs ? 'max-h-96' : 'max-h-48'}`}>
          {logs.length === 0 ? (
            <p className="text-slate-500 text-center py-4">No OpenClaw activity yet.</p>
          ) : (
            logs
              .filter(log => filterType === 'all' || log.type === filterType)
              .map((log, idx) => (
                <div key={idx} className="mb-2 pb-2 border-b border-slate-800 last:border-0">
                  <div className="flex items-start gap-2">
                    <span className="text-slate-500 text-[10px] mt-1 whitespace-nowrap">
                      {new Date(log.timestamp).toLocaleTimeString()}
                    </span>
                    <span className={`px-1.5 py-0.5 rounded text-[10px] font-semibold ${
                      log.type === 'error' ? 'bg-red-900/50 text-red-300' :
                      log.type === 'start' ? 'bg-blue-900/50 text-blue-300' :
                      log.type === 'complete' ? 'bg-green-900/50 text-green-300' :
                      log.type === 'score' ? 'bg-yellow-900/50 text-yellow-300' :
                      log.type === 'suggestions' ? 'bg-purple-900/50 text-purple-300' :
                      log.type === 'event' ? 'bg-cyan-900/50 text-cyan-300' :
                      'bg-slate-800 text-slate-400'
                    }`}>
                      {log.type.toUpperCase()}
                    </span>
                    <div className="flex-1 min-w-0">
                      <div className="text-slate-300 break-words">{log.message}</div>
                      {log.data && (
                        <details className="mt-1">
                          <summary className="text-slate-500 text-[10px] cursor-pointer hover:text-slate-400">
                            View details
                          </summary>
                          <pre className="mt-1 p-2 bg-slate-900 rounded text-[10px] text-slate-400 overflow-x-auto">
                            {JSON.stringify(log.data, null, 2)}
                          </pre>
                        </details>
                      )}
                    </div>
                  </div>
                </div>
              ))
          )}
        </div>
      </div>

      <div className="rounded-lg border border-slate-700 bg-slate-900/40 p-3 text-sm text-slate-200 space-y-2">
        <div>
          <span className="text-slate-400">Safety/Quality Score:</span>{' '}
          {score === null ? '—' : score.toFixed(2)}
        </div>
        <div>
          <span className="text-slate-400">Patch Suggestions:</span>
          {suggestions.length === 0 ? (
            <div className="text-slate-400">—</div>
          ) : (
            <ul className="list-disc list-inside text-slate-200">
              {suggestions.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </div>
  );
}
