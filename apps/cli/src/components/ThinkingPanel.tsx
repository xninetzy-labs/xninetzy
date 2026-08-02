import React, {
  memo,
  useEffect,
  useState
} from 'react';

import { performance } from 'node:perf_hooks';
import { Box, Text } from 'ink';

import type {
  ChatRun,
  ChatRunActivity
} from '../types/chat-run.js';

import { colors } from '../theme/colors.js';
import { cliConfig } from '../config/env.js';

type ThinkingPanelProps = {
  run: ChatRun | null;
  expanded: boolean;
};

const spinnerFrames = [
  '⠋',
  '⠙',
  '⠹',
  '⠸',
  '⠼',
  '⠴',
  '⠦',
  '⠧',
  '⠇',
  '⠏'
];

function isActiveRun(run: ChatRun): boolean {
  return ![
    'idle',
    'completed',
    'failed',
    'cancelled',
    'timed-out'
  ].includes(run.phase);
}

function formatElapsed(milliseconds: number): string {
  const totalSeconds =
    Math.max(0, milliseconds) / 1000;

  const minutes = Math.floor(totalSeconds / 60);
  const seconds = totalSeconds % 60;

  return `${String(minutes).padStart(
    2,
    '0'
  )}:${seconds
    .toFixed(1)
    .padStart(4, '0')}`;
}

function formatDuration(milliseconds: number): string {
  const totalSeconds =
    Math.max(0, milliseconds) / 1000;

  if (totalSeconds < 1) {
    return `${Math.round(milliseconds)}ms`;
  }

  if (totalSeconds < 60) {
    return `${totalSeconds.toFixed(1)}s`;
  }

  const minutes = Math.floor(totalSeconds / 60);

  return `${minutes}m ${(totalSeconds % 60).toFixed(
    1
  )}s`;
}

function phaseLabel(run: ChatRun): string {
  switch (run.phase) {
    case 'queued':
      return 'waiting for execution';

    case 'planning':
      return 'building execution plan';

    case 'thinking':
      return 'reasoning over the request';

    case 'tool-running':
      return 'running tools';

    case 'waiting-approval':
      return 'waiting for approval';

    case 'streaming':
      return 'writing final response';

    default:
      return run.phase;
  }
}

function activityVisual(
  activity: ChatRunActivity,
  spinnerFrame: string
): {
  symbol: string;
  color: string;
} {
  if (activity.status === 'active') {
    return {
      symbol: spinnerFrame,
      color: colors.cyan
    };
  }

  if (activity.status === 'failed') {
    return {
      symbol: '×',
      color: colors.red
    };
  }

  if (activity.kind === 'tool') {
    return {
      symbol: '⚙',
      color: colors.blueBright
    };
  }

  if (activity.kind === 'agent') {
    return {
      symbol: '◇',
      color: colors.purpleBright
    };
  }

  if (activity.kind === 'source') {
    return {
      symbol: '↗',
      color: colors.cyanBright
    };
  }

  return {
    symbol: '✓',
    color: colors.green
  };
}

function hasDeepResearch(run: ChatRun): boolean {
  return run.activity.some((activity) => {
    const content = [
      activity.kind,
      activity.label,
      activity.detail ?? ''
    ]
      .join(' ')
      .toLowerCase();

    return (
      content.includes('deep research') ||
      content.includes('deep-research')
    );
  });
}

function hasMcpActivity(run: ChatRun): boolean {
  return run.activity.some((activity) => {
    const content = [
      activity.label,
      activity.detail ?? ''
    ]
      .join(' ')
      .toLowerCase();

    return content.includes('mcp');
  });
}

function timeoutForRun(run: ChatRun): number {
  if (hasDeepResearch(run)) {
    return cliConfig.deepResearchTimeoutMs;
  }

  if (run.phase === 'streaming') {
    return cliConfig.streamTimeoutMs;
  }

  if (run.phase === 'tool-running') {
    return hasMcpActivity(run)
      ? cliConfig.mcpCallTimeoutMs
      : cliConfig.toolTimeoutMs;
  }

  return cliConfig.thinkTimeoutMs;
}

function ThinkingPanelView({
  run,
  expanded
}: ThinkingPanelProps) {
  const [frame, setFrame] = useState(0);
  const [now, setNow] = useState(performance.now());

  const active = Boolean(run && isActiveRun(run));

  useEffect(() => {
    if (!active) {
      return;
    }

    const spinnerTimer = setInterval(() => {
      setFrame(
        (current) =>
          (current + 1) % spinnerFrames.length
      );
    }, 95);

    return () => {
      clearInterval(spinnerTimer);
    };
  }, [active]);

  useEffect(() => {
    if (!active) {
      return;
    }

    const clockTimer = setInterval(() => {
      setNow(performance.now());
    }, 180);

    return () => {
      clearInterval(clockTimer);
    };
  }, [active]);

  if (!run || !active) {
    return null;
  }

  const spinner = spinnerFrames[frame];

  const elapsed = now - run.startedAt;
  const timeout = timeoutForRun(run);

  const slow =
    elapsed >= cliConfig.slowRequestWarningMs;

  const thoughtEnd =
    run.firstTokenAt ?? now;

  const thoughtDuration =
    thoughtEnd - run.startedAt;

  const activities = expanded
    ? run.activity
    : run.activity.slice(-5);

  const hiddenCount = Math.max(
    0,
    run.activity.length - activities.length
  );

  return (
    <Box
      width="100%"
      flexDirection="column"
      paddingX={2}
      flexShrink={0}
      marginTop={1}
      marginBottom={1}
    >
      <Box justifyContent="space-between">
        <Box>
          <Text
            bold
            color={colors.orangeBright}
          >
            ✦ Thought:
          </Text>

          <Text color={colors.textSecondary}>
            {' '}{formatDuration(thoughtDuration)}
          </Text>

          <Text color={colors.dim}>
            {' '}·{' '}
          </Text>

          <Text color={colors.cyanBright}>
            {phaseLabel(run)}
          </Text>
        </Box>

        <Text
          color={
            slow
              ? colors.yellow
              : colors.muted
          }
        >
          {slow ? '△ ' : ''}
          {formatElapsed(elapsed)}
          {' / '}
          {formatElapsed(timeout)}
        </Text>
      </Box>

      {hiddenCount > 0 && (
        <Text color={colors.dim}>
          {'  '}… {hiddenCount} earlier activities hidden
        </Text>
      )}

      {activities.map((activity) => {
        const visual = activityVisual(
          activity,
          spinner
        );

        return (
          <Box
            key={activity.id}
            paddingLeft={2}
          >
            <Text color={visual.color}>
              {visual.symbol}
            </Text>

            <Text color={colors.dim}>
              {' '}
              {activity.kind}
              {' · '}
            </Text>

            <Text
              color={
                activity.status === 'failed'
                  ? colors.red
                  : colors.textSecondary
              }
            >
              {activity.label}
            </Text>

            {activity.detail && (
              <Text color={colors.muted}>
                {' '}· {activity.detail}
              </Text>
            )}
          </Box>
        );
      })}

      {run.activity.length === 0 && (
        <Box paddingLeft={2}>
          <Text color={colors.cyan}>
            {spinner}
          </Text>

          <Text color={colors.muted}>
            {' '}processing request
          </Text>
        </Box>
      )}

      {run.firstTokenAt !== undefined && (
        <Box marginTop={1}>
          <Text
            bold
            color={colors.orangeBright}
          >
            ✦ Thought:
          </Text>

          <Text color={colors.textSecondary}>
            {' '}
            {formatDuration(
              now - run.firstTokenAt
            )}
          </Text>

          <Text color={colors.dim}>
            {' '}· final synthesis{' '}
          </Text>

          <Text color={colors.cyan}>
            {spinner}
          </Text>
        </Box>
      )}

      <Text color={colors.dim}>
        {'  '}
        Ctrl+T {expanded ? 'hide' : 'show'}
        {' '}full activity
      </Text>
    </Box>
  );
}

export const ThinkingPanel = memo(
  ThinkingPanelView
);
