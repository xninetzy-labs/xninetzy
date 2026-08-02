export type ChatRunPhase = 'idle' | 'queued' | 'planning' | 'thinking' | 'tool-running' | 'waiting-approval' | 'streaming' | 'completed' | 'failed' | 'cancelled' | 'timed-out';

export type ChatActivityStatus = 'active' | 'completed' | 'failed';

export interface ChatActivity {
  id: string;
  kind: string;
  label: string;
  status: ChatActivityStatus;
  detail?: string;
}

export interface ChatRun {
  id: string;
  phase: ChatRunPhase;
  startedAt: number;
  firstTokenAt?: number;
  finishedAt?: number;
  activity: ChatActivity[];
  error?: string;
}
