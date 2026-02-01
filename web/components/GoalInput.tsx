'use client';

import { useState } from 'react';
import { Play, Loader2 } from 'lucide-react';

interface GoalInputProps {
  onStart: (goal: string) => void;
  disabled: boolean;
}

export default function GoalInput({ onStart, disabled }: GoalInputProps) {
  const [goal, setGoal] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (goal.trim() && !disabled) {
      onStart(goal.trim());
      setGoal('');
    }
  };

  return (
    <div className="bg-slate-800 rounded-lg p-6">
      <h2 className="text-xl font-bold text-white mb-4">Agent Goal</h2>
      <form onSubmit={handleSubmit}>
        <textarea
          value={goal}
          onChange={(e) => setGoal(e.target.value)}
          placeholder="Enter your goal... e.g., 'Navigate to a pricing page and extract pricing information'"
          className="w-full px-4 py-3 bg-slate-700 text-white rounded-lg border border-slate-600 focus:border-primary-500 focus:outline-none resize-none"
          rows={4}
          disabled={disabled}
        />
        <button
          type="submit"
          disabled={!goal.trim() || disabled}
          className="mt-4 w-full px-4 py-3 bg-primary-600 hover:bg-primary-700 disabled:bg-slate-600 disabled:cursor-not-allowed text-white rounded-lg transition-colors flex items-center justify-center gap-2"
        >
          {disabled ? (
            <>
              <Loader2 className="animate-spin" size={20} />
              Running...
            </>
          ) : (
            <>
              <Play size={20} />
              Start Agent
            </>
          )}
        </button>
      </form>
    </div>
  );
}
