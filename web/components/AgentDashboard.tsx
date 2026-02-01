'use client';

import { useState, useEffect } from 'react';
import { Credentials, AgentExecution } from '@/types';
import GoalInput from './GoalInput';
import OpenClawBeachPanel from './OpenClawBeachPanel';
import ExecutionLog from './ExecutionLog';
import ObservationViewer from './ObservationViewer';
import ActionHistory from './ActionHistory';
import RLMVisualization from './RLMVisualization';
import WeaveTraceViewer from './WeaveTraceViewer';
import MarimoEmbed from './MarimoEmbed';
import StatusPanel from './StatusPanel';

interface AgentDashboardProps {
  credentials: Credentials;
  execution: AgentExecution | null;
  onUpdateExecution: (update: AgentExecution | ((prev: AgentExecution | null) => AgentExecution)) => void;
}

export default function AgentDashboard({
  credentials,
  execution,
  onUpdateExecution,
}: AgentDashboardProps) {
  const [isRunning, setIsRunning] = useState(false);
  const marimoUrl = process.env.NEXT_PUBLIC_MARIMO_URL;

  const handleStartExecution = async (goal: string) => {
    setIsRunning(true);
    const execId = `exec_${Date.now()}`;
    
    const newExecution: AgentExecution = {
      id: execId,
      goal,
      status: 'running',
      current_step: 0,
      trajectory: [],
      events: [],
    };
    
    onUpdateExecution(newExecution);

      try {
      // Call backend API (works with Railway rewrites or direct backend URL)
      const apiBase = process.env.NEXT_PUBLIC_API_BASE_URL || '';
      const apiUrl = apiBase ? `${apiBase.replace(/\/$/, '')}/api/agent/run` : '/api/agent/run';
      const response = await fetch(apiUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          goal,
          credentials,
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to start agent');
      }

      // Stream updates
      const reader = response.body?.getReader();
      const decoder = new TextDecoder();

      if (reader) {
        let buffer = '';
        
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split('\n');
          buffer = lines.pop() || ''; // Keep incomplete line in buffer

          for (const line of lines) {
            if (line.startsWith('data: ')) {
              try {
                const data = JSON.parse(line.slice(6));
                
                // Update execution state based on update type
                if (data.type === 'start') {
                  onUpdateExecution((prev) => ({
                    ...(prev || newExecution),
                    goal: data.goal,
                    status: 'running',
                  }));
                } else if (data.type === 'action') {
                  onUpdateExecution((prev) => ({
                    ...(prev || newExecution),
                    current_step: data.step,
                    trajectory: [
                      ...(prev?.trajectory || []),
                      {
                        ...data.action,
                        timestamp: new Date().toISOString(),
                      },
                    ],
                    status: 'running',
                  }));
                } else if (data.type === 'observation') {
                  onUpdateExecution((prev) => ({
                    ...(prev || newExecution),
                    last_observation: data.observation,
                    status: 'running',
                  }));
                } else if (data.type === 'events') {
                  onUpdateExecution((prev) => ({
                    ...(prev || newExecution),
                    events: data.events,
                    status: 'running',
                  }));
                } else if (data.type === 'complete') {
                  onUpdateExecution((prev) => ({
                    ...(prev || newExecution),
                    status: 'completed',
                    score: data.score,
                    total_steps: data.total_steps,
                  }));
                } else if (data.type === 'error') {
                  onUpdateExecution((prev) => ({
                    ...(prev || newExecution),
                    status: 'error',
                    error: data.error,
                  }));
                }
              } catch (e) {
                console.error('Failed to parse update:', e, line);
              }
            }
          }
        }
      }

      // Ensure final state is set
      onUpdateExecution((prev) => ({
        ...(prev || newExecution),
        status: prev?.status === 'error' ? 'error' : 'completed',
      }));
    } catch (error: any) {
      onUpdateExecution({
        ...newExecution,
        status: 'error',
        error: error.message,
      });
    } finally {
      setIsRunning(false);
    }
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
      {/* Left Column: Input & Status */}
      <div className="lg:col-span-1 space-y-6">
        <GoalInput
          onStart={handleStartExecution}
          disabled={isRunning}
        />
        <OpenClawBeachPanel
          credentials={credentials}
          execution={execution}
          onUpdateExecution={onUpdateExecution}
        />
        
        <StatusPanel execution={execution} />
      </div>

      {/* Middle Column: Execution & Observations */}
      <div className="lg:col-span-1 space-y-6">
        <ExecutionLog execution={execution} />
        <ObservationViewer observation={execution?.last_observation} />
      </div>

      {/* Right Column: History & Visualization */}
      <div className="lg:col-span-1 space-y-6">
        <ActionHistory actions={execution?.trajectory || []} />
        <RLMVisualization execution={execution} />
        <WeaveTraceViewer execution={execution} credentials={credentials} />
        <MarimoEmbed src={marimoUrl} />
      </div>
    </div>
  );
}
