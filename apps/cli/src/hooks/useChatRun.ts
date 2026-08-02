import { useCallback, useRef, useState } from 'react';
import type { ChatActivity, ChatRun, ChatRunPhase } from '../types/chat-run.js';

function activityId(kind: string, label: string, detail?: string): string {
  return [kind, label, detail || ""].join(":").toLowerCase();
}

const allowedTransitions: Record<ChatRunPhase, ReadonlySet<ChatRunPhase>> = {
  idle: new Set(["queued"]),
  queued: new Set(["planning", "thinking", "tool-running", "waiting-approval", "streaming", "completed", "failed", "cancelled", "timed-out"]),
  planning: new Set(["thinking", "tool-running", "waiting-approval", "streaming", "completed", "failed", "cancelled", "timed-out"]),
  thinking: new Set(["planning", "tool-running", "waiting-approval", "streaming", "completed", "failed", "cancelled", "timed-out"]),
  "tool-running": new Set(["planning", "thinking", "waiting-approval", "streaming", "completed", "failed", "cancelled", "timed-out"]),
  "waiting-approval": new Set(["thinking", "tool-running", "streaming", "completed", "failed", "cancelled", "timed-out"]),
  streaming: new Set(["completed", "failed", "cancelled", "timed-out"]),
  completed: new Set(),
  failed: new Set(),
  cancelled: new Set(),
  "timed-out": new Set(),
};

export function canTransition(from: ChatRunPhase, to: ChatRunPhase): boolean {
  return from === to || allowedTransitions[from].has(to);
}

export function useChatRun() {
  const [run, setRun] = useState<ChatRun | null>(null);
  const currentId = useRef<string | null>(null);

  const start = useCallback((id: string) => {
    const next: ChatRun = { id, phase: 'queued', startedAt: performance.now(), activity: [] };
    currentId.current = id;
    setRun(next);
  }, []);

  const addActivity = useCallback((id: string, kind: string, label: string, status: ChatActivity['status'], detail?: string) => {
    if (currentId.current !== id) return;
    setRun((current) => {
      if (!current || current.id !== id) return current;
      const key = activityId(kind, label, detail);
      const existing = current.activity.findIndex((activity) => activity.id === key);
      const entry: ChatActivity = { id: key, kind, label, status, detail };
      const settled = current.activity.map((item) =>
        item.kind === kind && item.status === "active" && item.id !== key
          ? { ...item, status: "completed" as const }
          : item
      );
      const activity = existing === -1
        ? [...settled, entry]
        : settled.map((item, index) => index === existing ? { ...item, ...entry } : item);
      return { ...current, activity };
    });
  }, []);

  const setPhase = useCallback((id: string, phase: ChatRunPhase) => {
    if (currentId.current !== id) return;
    setRun((current) => {
      if (!current || current.id !== id || !canTransition(current.phase, phase)) return current;
      const firstTokenAt = phase === 'streaming' && !current.firstTokenAt
        ? performance.now()
        : current.firstTokenAt;
      return { ...current, phase, firstTokenAt };
    });
  }, []);

  const finish = useCallback((id: string, phase: Extract<ChatRunPhase, 'completed' | 'failed' | 'cancelled' | 'timed-out'>, error?: string) => {
    if (currentId.current !== id) return;
    currentId.current = null;
    setRun((current) => {
      if (!current || current.id !== id || !canTransition(current.phase, phase)) return current;
      const activityStatus = phase === "completed" ? "completed" : "failed";
      const activity = current.activity.map((item) =>
        item.status === "active" ? { ...item, status: activityStatus as ChatActivity["status"] } : item
      );
      return { ...current, phase, activity, finishedAt: performance.now(), error };
    });
  }, []);

  const reset = useCallback(() => {
    currentId.current = null;
    setRun(null);
  }, []);

  const isCurrent = useCallback((id: string) => currentId.current === id, []);

  return { run, start, addActivity, setPhase, finish, isCurrent, reset };
}
