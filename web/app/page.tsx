'use client';

import { useState, useEffect } from 'react';
import AgentDashboard from '@/components/AgentDashboard';
import CredentialsModal from '@/components/CredentialsModal';
import { AgentExecution, Credentials } from '@/types';

export default function Home() {
  const [credentials, setCredentials] = useState<Credentials | null>(null);
  const [showCredentialsModal, setShowCredentialsModal] = useState(true);
  const [execution, setExecution] = useState<AgentExecution | null>(null);

  useEffect(() => {
    // Load saved credentials from localStorage
    const saved = localStorage.getItem('rvla_credentials');
    if (saved) {
      try {
        const creds = JSON.parse(saved);
        setCredentials(creds);
        setShowCredentialsModal(false);
      } catch (e) {
        console.error('Failed to load credentials:', e);
      }
    }
  }, []);

  const handleSaveCredentials = (creds: Credentials) => {
    setCredentials(creds);
    localStorage.setItem('rvla_credentials', JSON.stringify(creds));
    setShowCredentialsModal(false);
  };

  return (
    <main className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
      <div className="container mx-auto px-4 py-8">
        <header className="mb-8 text-center">
          <h1 className="text-5xl font-bold text-white mb-2">
            RLM-VLA Agent
          </h1>
          <p className="text-xl text-slate-300">
            Recursive Language Model for Vision-Language-Action Tasks
          </p>
          <p className="text-sm text-slate-400 mt-2">
            Built for WeaveHacks 3 • Powered by GPT-4o, Weave, Browserbase
          </p>
        </header>

        {showCredentialsModal && (
          <CredentialsModal
            onSave={handleSaveCredentials}
            onCancel={() => {
              if (credentials) {
                setShowCredentialsModal(false);
              }
            }}
          />
        )}

        {credentials && (
          <div className="mb-4 flex justify-end">
            <button
              onClick={() => setShowCredentialsModal(true)}
              className="px-4 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded-lg transition-colors"
            >
              Update Credentials
            </button>
          </div>
        )}

        {credentials ? (
          <AgentDashboard
            credentials={credentials}
            execution={execution}
            onUpdateExecution={setExecution}
          />
        ) : (
          <div className="text-center text-white py-20">
            <p className="text-xl mb-4">Please configure your API credentials to begin.</p>
          </div>
        )}
      </div>
    </main>
  );
}
