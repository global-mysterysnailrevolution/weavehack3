'use client';

import { useState, useEffect } from 'react';
import AgentDashboard from '@/components/AgentDashboard';
import CredentialsModal from '@/components/CredentialsModal';
import { AgentExecution, Credentials } from '@/types';
import Image from 'next/image';

export default function Home() {
  const [credentials, setCredentials] = useState<Credentials | null>(null);
  const [showCredentialsModal, setShowCredentialsModal] = useState(false);
  const [execution, setExecution] = useState<AgentExecution | null>(null);
  const [backgroundImageError, setBackgroundImageError] = useState(false);
  const [logoImageError, setLogoImageError] = useState(false);

  useEffect(() => {
    // Always try to load from environment variables first (private env vars)
    const loadCredentialsFromEnv = async () => {
      try {
        const response = await fetch('/api/dev/seed-credentials');
        if (response.ok) {
          const envCreds = await response.json();
          // Check if we have the minimum required credentials
          if (envCreds.openai_api_key && envCreds.wandb_api_key && envCreds.wandb_project) {
            console.log('✅ Using credentials from environment variables');
            setCredentials(envCreds as Credentials);
            // Don't save to localStorage - always use fresh env vars
            setShowCredentialsModal(false);
            return;
          } else {
            console.warn('⚠️ Environment variables incomplete:', {
              hasOpenAI: !!envCreds.openai_api_key,
              hasWandb: !!envCreds.wandb_api_key,
              hasProject: !!envCreds.wandb_project
            });
          }
        }
      } catch (e) {
        console.error('Failed to fetch environment credentials:', e);
      }

      // Fallback to localStorage only if env vars are not available
      const saved = localStorage.getItem('rvla_credentials');
      if (saved) {
        try {
          const creds = JSON.parse(saved);
          if (creds.openai_api_key && creds.wandb_api_key && creds.wandb_project) {
            console.log('Using credentials from localStorage (fallback)');
            setCredentials(creds);
            setShowCredentialsModal(false);
            return;
          }
        } catch (e) {
          console.error('Failed to load credentials from localStorage:', e);
        }
      }
      
      // Only show modal if we don't have credentials from env vars or localStorage
      setShowCredentialsModal(true);
    };

    loadCredentialsFromEnv();
  }, []);

  const handleSaveCredentials = (creds: Credentials) => {
    setCredentials(creds);
    localStorage.setItem('rvla_credentials', JSON.stringify(creds));
    setShowCredentialsModal(false);
  };

  return (
    <main className="min-h-screen relative">
      {/* Background image */}
      <div className="fixed inset-0 z-0">
        {!backgroundImageError && (
          <div className="relative w-full h-full">
            <Image
              src="/fisherman-background.svg"
              alt="Fisherman with lobster"
              fill
              className="object-cover"
              priority
              style={{ objectFit: 'cover' }}
              onError={() => setBackgroundImageError(true)}
            />
          </div>
        )}
        {/* Overlay for better text readability */}
        <div className="absolute inset-0 bg-black bg-opacity-40"></div>
        {/* Fallback gradient background */}
        <div className={`absolute inset-0 bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 ${backgroundImageError ? 'z-10' : ''}`}></div>
      </div>

      {/* Content */}
      <div className="relative z-10 container mx-auto px-4 py-8">
        <header className="mb-8 text-center">
          {/* Lobsterpot Logo */}
          {!logoImageError && (
            <div className="flex justify-center mb-4">
              <div className="relative w-[200px] h-[100px]">
                <Image
                  src="/lobsterpot-logo.svg"
                  alt="Lobster Pot Logo"
                  fill
                  className="object-contain"
                  priority
                  onError={() => setLogoImageError(true)}
                />
              </div>
            </div>
          )}
          <h1 className="text-5xl font-bold text-white mb-2 drop-shadow-lg">
            RLM-VLA Agent
          </h1>
          <p className="text-xl text-slate-200 drop-shadow-md">
            Recursive Language Model for Vision-Language-Action Tasks
          </p>
          <p className="text-sm text-slate-300 mt-2 drop-shadow-md">
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
          <div className="mb-4 flex justify-between items-center">
            <div className="text-sm text-slate-300">
              {process.env.NODE_ENV === 'development' && (
                <span className="px-2 py-1 bg-green-900/50 text-green-300 rounded text-xs">
                  Using environment variables
                </span>
              )}
            </div>
            <button
              onClick={() => setShowCredentialsModal(true)}
              className="px-4 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded-lg transition-colors backdrop-blur-sm bg-opacity-80 text-sm"
            >
              Override Credentials
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
            <p className="text-xl mb-4 drop-shadow-lg">Please configure your API credentials to begin.</p>
          </div>
        )}
      </div>
    </main>
  );
}
