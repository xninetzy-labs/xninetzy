import {
  useCallback,
  useRef,
  useState
} from 'react';
import { performance } from 'node:perf_hooks';

import type {
  ChatActivityKind,
  ChatActivityStatus,
  ChatRun,
  ChatRunPhase
} from '../types/chat-run.js';

const validTransitions: Record<
  ChatRunPhase,
  readonly ChatRunPhase[]
> = {
  idle: ['queued'],

  queued: [
    'planning',
    'thinking',
    'tool-running',
    'waiting-approval',
    'streaming',
    'completed',
    'cancelled',
    'timed-out',
    'failed'
  ],

  planning: [
    'thinking',
    'tool-running',
    'waiting-approval',
    'streaming',
    'completed',
    'cancelled',
    'timed-out',
    'failed'
  ],

  thinking: [
    'tool-running',
    'waiting-approval',
    'streaming',
    'completed',
    'cancelled',
    'timed-out',
    'failed'
  ],

  'tool-running': [
    'thinking',
    'waiting-approval',
    'streaming',
    'completed',
    'cancelled',
    'timed-out',
    'failed'
  ],

  'waiting-approval': [
    'tool-running',
    'thinking',
    'streaming',
    'completed',
    'cancelled',
    'timed-out',
    'failed'
  ],

  streaming: [
    'completed',
    'cancelled',
    'timed-out',
    'failed'
  ],

  completed: [],
  cancelled: [],
  'timed-out': [],
  failed: []
};

function isTerminalPhase(phase: ChatRunPhase): boolean {
  return [
    'completed',
    'cancelled',
    'timed-out',
    'failed'
  ].includes(phase);
}

function normalizeActivityKey(value: string): string {
  return value
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '');
}

function createActivityId(
  kind: ChatActivityKind,
  label: string
): string {
  return `${kind}:${normalizeActivityKey(label)}`;
}

function canTransition(
  current: ChatRunPhase,
  next: ChatRunPhase
): boolean {
  if (current === next) {
    return true;
  }

  return validTransitions[current].includes(next);
}

export function useChatRun() {
  const [run, setRun] = useState<ChatRun | null>(null);

  const currentRequestIdRef =
    useRef<string | null>(null);

  const isCurrent = useCallback(
    (requestId: string): boolean => {
      return currentRequestIdRef.current === requestId;
    },
    []
  );

  const start = useCallback((requestId: string) => {
    const now = performance.now();

    currentRequestIdRef.current = requestId;

    setRun({
      requestId,
      phase: 'queued',
      startedAt: now,
      activity: []
    });
  }, []);

  const setPhase = useCallback(
    (
      requestId: string,
      phase: ChatRunPhase
    ) => {
      if (currentRequestIdRef.current !== requestId) {
        return;
      }

      setRun((current) => {
        if (
          !current ||
          current.requestId !== requestId ||
          isTerminalPhase(current.phase)
        ) {
          return current;
        }

        if (!canTransition(current.phase, phase)) {
          return current;
        }

        if (current.phase === phase) {
          return current;
        }

        const now = performance.now();

        return {
          ...current,
          phase,

          firstTokenAt:
            phase === 'streaming' &&
            current.firstTokenAt === undefined
              ? now
              : current.firstTokenAt
        };
      });
    },
    []
  );

  const addActivity = useCallback(
    (
      requestId: string,
      kind: ChatActivityKind,
      label: string,
      status: ChatActivityStatus,
      detail?: string
    ) => {
      if (currentRequestIdRef.current !== requestId) {
        return;
      }

      setRun((current) => {
        if (
          !current ||
          current.requestId !== requestId ||
          isTerminalPhase(current.phase)
        ) {
          return current;
        }

        const now = performance.now();
        const id = createActivityId(kind, label);

        const existingIndex =
          current.activity.findIndex(
            (activity) => activity.id === id
          );

        if (existingIndex === -1) {
          return {
            ...current,

            activity: [
              ...current.activity,
              {
                id,
                kind,
                label,
                status,
                detail,

                startedAt: now,

                finishedAt:
                  status === 'active'
                    ? undefined
                    : now
              }
            ]
          };
        }

        const existing =
          current.activity[existingIndex];

        if (
          existing.status === status &&
          existing.detail === detail
        ) {
          return current;
        }

        const activity = current.activity.slice();

        activity[existingIndex] = {
          ...existing,
          label,
          status,
          detail: detail ?? existing.detail,

          finishedAt:
            status === 'active'
              ? undefined
              : existing.finishedAt ?? now
        };

        return {
          ...current,
          activity
        };
      });
    },
    []
  );

  const finish = useCallback(
    (
      requestId: string,
      phase:
        | 'completed'
        | 'cancelled'
        | 'timed-out'
        | 'failed',
      error?: string
    ) => {
      if (currentRequestIdRef.current !== requestId) {
        return;
      }

      const now = performance.now();

      setRun((current) => {
        if (
          !current ||
          current.requestId !== requestId ||
          isTerminalPhase(current.phase)
        ) {
          return current;
        }

        return {
          ...current,
          phase,
          error,
          finishedAt: now,

          activity: current.activity.map((activity) => {
            if (activity.status !== 'active') {
              return activity;
            }

            return {
              ...activity,

              status:
                phase === 'completed'
                  ? 'completed'
                  : 'failed',

              finishedAt: now
            };
          })
        };
      });
    },
    []
  );

  const reset = useCallback(() => {
    currentRequestIdRef.current = null;
    setRun(null);
  }, []);

  return {
    run,
    start,
    setPhase,
    addActivity,
    finish,
    isCurrent,
    reset
  };
}
