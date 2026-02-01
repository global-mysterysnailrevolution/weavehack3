export interface Credentials {
  openai_api_key: string;
  wandb_api_key: string;
  wandb_project: string;
  wandb_entity?: string;
  redis_url?: string;
  browserbase_api_key?: string;
  browserbase_project_id?: string;
}

export interface AgentExecution {
  id: string;
  goal: string;
  status: 'idle' | 'running' | 'completed' | 'error';
  current_step: number;
  total_steps?: number;
  trajectory: Action[];
  events: string[];
  last_observation?: Observation;
  score?: number;
  error?: string;
}

export interface Action {
  type: 'act' | 'subcall' | 'done' | 'delegate_task';
  payload: Record<string, any>;
  timestamp: string;
  reasoning?: string;
}

export interface Observation {
  url: string;
  screenshot_base64?: string;
  screenshot_path?: string;
  dom_snapshot?: string;
  metadata?: Record<string, any>;
}

export interface RLMContextExamination {
  query: string;
  summary: string;
  key_findings: string[];
  suggested_actions: string[];
  relevant_snippets: string[];
}

export interface WeaveTrace {
  id: string;
  name: string;
  inputs: Record<string, any>;
  outputs: Record<string, any>;
  children: WeaveTrace[];
  timestamp: string;
}
