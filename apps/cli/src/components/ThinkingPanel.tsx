import React, { memo, useEffect, useState } from 'react';
import { Box, Text } from 'ink';
import type { ChatRun } from '../types/chat-run.js';
import { colors } from '../theme/colors.js';
import { cliConfig } from '../config/env.js';

type ThinkingPanelProps = {
  run: ChatRun | null;
  expanded: boolean;
};

const spinnerFrames = ['\u280b', '\u2819', '\u2839', '\u2838', '\u283c', '\u2834', '\u2826', '\u2827', '\u2807', '\u280f'];

function formatElapsed(milliseconds: number): string {
  const seconds = Math.max(0, milliseconds) / 1000;
  const minutes = Math.floor(seconds / 60);
  const remainder = seconds % 60;
  return `${String(minutes).padStart(2, '0')}:${remainder.toFixed(1).padStart(4, '0')}`;
}

function formatDuration(milliseconds: number): string {
  const seconds = Math.max(0, milliseconds) / 1000;
  if (seconds < 60) return `${seconds.toFixed(1)}s`;
  const minutes = Math.floor(seconds / 60);
  return `${minutes}m ${(seconds % 60).toFixed(1)}s`;
}

function SpinnerGlyph({ active, completed }: { active: boolean; completed: boolean }) {
  const [frame, setFrame] = useState(0);

  useEffect(() => {
    if (!active) return;
    const timer = setInterval(() => setFrame((current) => (current + 1) % spinnerFrames.length), 100);
    return () => clearInterval(timer);
  }, [active]);

  if (active) return <Text color={colors.blueBright}>{spinnerFrames[frame]}</Text>;
  return <Text color={completed ? colors.green : colors.blueBright}>{completed ? '\u2713' : '\u25ce'}</Text>;
}

function ElapsedClock({ run }: { run: ChatRun }) {
  const [now, setNow] = useState(performance.now());
  const active = !["idle", "completed", "failed", "cancelled", "timed-out"].includes(run.phase);

  useEffect(() => {
    if (!active) return;
    const timer = setInterval(() => setNow(performance.now()), 200);
    return () => clearInterval(timer);
  }, [active]);

  const endedAt = run.finishedAt ?? now;
  const elapsed = endedAt - run.startedAt;
  const deepResearch = run.activity.some((activity) => activity.label.toLowerCase().includes("research"));
  const limit = deepResearch
    ? cliConfig.deepResearchTimeoutMs
    : run.phase === "streaming"
      ? cliConfig.streamTimeoutMs
      : cliConfig.thinkTimeoutMs;
  const slow = elapsed >= cliConfig.slowRequestWarningMs;
  return <Text color={slow ? colors.yellow : colors.textSecondary}>{slow ? '\u25b3 ' : ''}{formatElapsed(elapsed)} / {formatElapsed(limit)}</Text>;
}

function titleFor(run: ChatRun, now: number): string {
  if (run.phase === 'completed') {
    const endedAt = run.finishedAt ?? now;
    const thoughtEndedAt = run.firstTokenAt ?? endedAt;
    return `Thought for ${formatDuration(thoughtEndedAt - run.startedAt)} · completed in ${formatDuration(endedAt - run.startedAt)}`;
  }
  if (run.phase === "queued") return "Xninetzy is queued";
  if (run.phase === "planning") return "Xninetzy is planning";
  if (run.phase === "tool-running") return "Xninetzy is working";
  if (run.phase === "waiting-approval") return "Xninetzy is waiting for approval";
  if (run.phase === "streaming") return "Xninetzy is responding";
  if (run.phase === 'cancelled') return 'Generation stopped';
  if (run.phase === 'timed-out') return 'Thinking timed out';
  if (run.phase === 'failed') return 'Request failed';
  return 'Xninetzy is thinking';
}

function ThinkingPanelView({ run, expanded }: ThinkingPanelProps) {
  const active = Boolean(run && !["idle", "completed", "failed", "cancelled", "timed-out"].includes(run.phase));
  const completed = run?.phase === 'completed';
  const latest = run?.activity.slice().reverse().find((activity) => activity.status === "active") ?? run?.activity.at(-1);
  const now = performance.now();
  const title = run ? titleFor(run, now) : 'Xninetzy is ready';
  const activityLabel = latest?.label ?? 'Waiting for your next request';
  const completedActivities = run?.activity.filter((activity) => activity.status === 'completed').length ?? 0;
  const activityCount = run?.activity.length ?? 0;
  const toolCount = run?.activity.filter((activity) => activity.kind === "tool").length ?? 0;
  const agentCount = run?.activity.filter((activity) => activity.kind === "agent").length ?? 0;
  const sourceCount = run?.activity.filter((activity) => activity.kind === "source").length ?? 0;

  return (
    <Box width="100%" flexDirection="column" paddingX={1} minHeight={expanded ? 7 : 4}>
      <Box borderStyle="round" borderColor={active ? colors.border : colors.borderDim} paddingX={1} flexDirection="column">
        <Box justifyContent="space-between">
          <Box>
            <SpinnerGlyph active={Boolean(active)} completed={Boolean(completed)} />
            <Text color={colors.white} bold> {title}</Text>
          </Box>
          {run && active && <ElapsedClock run={run} />}
        </Box>
        <Text color={colors.textSecondary}>{activityLabel}</Text>
        <Text color={colors.muted}>
          {completedActivities} of {activityCount} activities completed{toolCount ? " · " + toolCount + " tools" : ""}{agentCount ? " · " + agentCount + " agents" : ""}{sourceCount ? " · " + sourceCount + " sources" : ""} · Ctrl+T {expanded ? 'hide' : 'show'} details
        </Text>
      </Box>
      {expanded && run && (
        <Box marginTop={1} paddingX={1} flexDirection="column" borderStyle="single" borderColor={colors.borderDim}>
          {run.activity.length === 0 ? (
            <Text color={colors.muted}>No backend activity has been reported yet.</Text>
          ) : (
            run.activity.map((activity) => (
              <Text key={activity.id} color={activity.status === 'failed' ? colors.red : colors.textSecondary}>
                {activity.status === 'active' ? '\u2839' : activity.status === 'completed' ? '\u2713' : '\u00d7'} [{activity.kind.toUpperCase()}] {activity.label}{activity.detail ? ` · ${activity.detail}` : ''}
              </Text>
            ))
          )}
        </Box>
      )}
    </Box>
  );
}

export const ThinkingPanel = memo(ThinkingPanelView);
