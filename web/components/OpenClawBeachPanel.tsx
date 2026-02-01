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
  const [logs, setLogs] = useState<string[]>([]);
  const [score, setScore] = useState<number | null>(null);
  const [suggestions, setSuggestions] = useState<string[]>([]);

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
            if (data.type === 'openclaw_log') {
              setLogs((prev) => [...prev, data.message]);
            } else if (data.type === 'openclaw_event') {
              setLogs((prev) => [...prev, JSON.stringify(data.payload)]);
            } else if (data.type === 'openclaw_score') {
              setScore(data.score);
            } else if (data.type === 'openclaw_suggestions') {
              setSuggestions(Array.isArray(data.suggestions) ? data.suggestions : []);
            } else if (data.type === 'openclaw_complete') {
              setLogs((prev) => [...prev, `Complete (exit ${data.exit_code})`]);
            } else if (data.type === 'error') {
              setLogs((prev) => [...prev, `Error: ${data.error}`]);
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

      <div className="rounded-lg border border-slate-700 bg-slate-900/40 p-3 text-xs text-slate-300 max-h-48 overflow-y-auto">
        {logs.length === 0 ? (
          <p>No OpenClaw logs yet.</p>
        ) : (
          logs.map((line, idx) => <div key={`${idx}-${line}`}>{line}</div>)
        )}
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
