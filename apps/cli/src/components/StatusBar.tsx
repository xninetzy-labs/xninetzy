import React from 'react';
import { Box, Text } from 'ink';
import { colors } from '../theme/colors.js';

type StatusBarProps = {
  width: number;
  aiUrl: string;
  isSending: boolean;
  lastError: string | null;
};

export function StatusBar({ width, aiUrl, isSending, lastError }: StatusBarProps) {
  return (
    <Box width={width} flexDirection="column" paddingX={2}>
      <Text color={colors.white}>
        Build · Live AI · Xninetzy Labs ·{' '}
        <Text color={isSending ? colors.orange : colors.purpleBright}>
          {isSending ? 'thinking' : 'ready'}
        </Text>
      </Text>
      <Text color={colors.dim}>
        AI {aiUrl}
      </Text>
      {lastError && <Text color={colors.orange}>last error · {lastError}</Text>}
      <Text color={colors.muted}>
        tab agents     ctrl+p commands     esc exit     ctrl+c quit
      </Text>
    </Box>
  );
}
