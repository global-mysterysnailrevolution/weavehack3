'use client';

import { useState } from 'react';
import { Credentials } from '@/types';
import { X } from 'lucide-react';

interface CredentialsModalProps {
  onSave: (credentials: Credentials) => void;
  onCancel: () => void;
}

export default function CredentialsModal({ onSave, onCancel }: CredentialsModalProps) {
  const [formData, setFormData] = useState<Partial<Credentials>>({
    wandb_project: 'weavehacks-rvla',
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (formData.openai_api_key && formData.wandb_api_key && formData.wandb_project) {
      onSave(formData as Credentials);
    }
  };

  const handleChange = (field: keyof Credentials, value: string) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-slate-800 rounded-lg p-6 max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-2xl font-bold text-white">Configure API Credentials</h2>
          <button
            onClick={onCancel}
            className="text-slate-400 hover:text-white transition-colors"
          >
            <X size={24} />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-1">
              OpenAI API Key <span className="text-red-400">*</span>
            </label>
            <input
              type="password"
              value={formData.openai_api_key || ''}
              onChange={(e) => handleChange('openai_api_key', e.target.value)}
              className="w-full px-3 py-2 bg-slate-700 text-white rounded-lg border border-slate-600 focus:border-primary-500 focus:outline-none"
              placeholder="sk-..."
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-300 mb-1">
              Weights & Biases API Key <span className="text-red-400">*</span>
            </label>
            <input
              type="password"
              value={formData.wandb_api_key || ''}
              onChange={(e) => handleChange('wandb_api_key', e.target.value)}
              className="w-full px-3 py-2 bg-slate-700 text-white rounded-lg border border-slate-600 focus:border-primary-500 focus:outline-none"
              placeholder="Your W&B API key"
              required
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-1">
                W&B Project <span className="text-red-400">*</span>
              </label>
              <input
                type="text"
                value={formData.wandb_project || ''}
                onChange={(e) => handleChange('wandb_project', e.target.value)}
                className="w-full px-3 py-2 bg-slate-700 text-white rounded-lg border border-slate-600 focus:border-primary-500 focus:outline-none"
                placeholder="weavehacks-rvla"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-300 mb-1">
                W&B Entity (optional)
              </label>
              <input
                type="text"
                value={formData.wandb_entity || ''}
                onChange={(e) => handleChange('wandb_entity', e.target.value)}
                className="w-full px-3 py-2 bg-slate-700 text-white rounded-lg border border-slate-600 focus:border-primary-500 focus:outline-none"
                placeholder="Your username"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-300 mb-1">
              Redis URL (optional)
            </label>
            <input
              type="text"
              value={formData.redis_url || ''}
              onChange={(e) => handleChange('redis_url', e.target.value)}
              className="w-full px-3 py-2 bg-slate-700 text-white rounded-lg border border-slate-600 focus:border-primary-500 focus:outline-none"
              placeholder="redis://..."
            />
            <p className="text-xs text-slate-400 mt-1">
              Leave empty to use in-memory storage
            </p>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-1">
                Browserbase API Key (optional)
              </label>
              <input
                type="password"
                value={formData.browserbase_api_key || ''}
                onChange={(e) => handleChange('browserbase_api_key', e.target.value)}
                className="w-full px-3 py-2 bg-slate-700 text-white rounded-lg border border-slate-600 focus:border-primary-500 focus:outline-none"
                placeholder="bb_..."
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-300 mb-1">
                Browserbase Project ID (optional)
              </label>
              <input
                type="text"
                value={formData.browserbase_project_id || ''}
                onChange={(e) => handleChange('browserbase_project_id', e.target.value)}
                className="w-full px-3 py-2 bg-slate-700 text-white rounded-lg border border-slate-600 focus:border-primary-500 focus:outline-none"
                placeholder="Project ID"
              />
            </div>
          </div>

          <div className="flex justify-end gap-3 pt-4">
            <button
              type="button"
              onClick={onCancel}
              className="px-4 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded-lg transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-4 py-2 bg-primary-600 hover:bg-primary-700 text-white rounded-lg transition-colors"
            >
              Save & Start
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
