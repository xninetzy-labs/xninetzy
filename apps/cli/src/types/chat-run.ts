export type ChatRunPhase =
  | 'idle'
  | 'queued'
  | 'planning'
  | 'thinking'
  | 'tool-running'
  | 'waiting-approval'
  | 'streaming'
  | 'completed'
  | 'cancelled'
  | 'timed-out'
  | 'failed';

export type ChatActivityKind =
  | 'request'
  | 'phase'
  | 'activity'
  | 'tool'
  | 'agent'
  | 'source'
  | 'response';

export type ChatActivityStatus =
  | 'active'
  | 'completed'
  | 'failed';

export type ChatRunActivity = {
  id: string;
  kind: ChatActivityKind;
  label: string;
  status: ChatActivityStatus;
  detail?: string;

  startedAt: number;
  finishedAt?: number;
};

export type ChatRun = {
  requestId: string;
  phase: ChatRunPhase;

  startedAt: number;
  firstTokenAt?: number;
  finishedAt?: number;

  activity: ChatRunActivity[];

  error?: string;
};
