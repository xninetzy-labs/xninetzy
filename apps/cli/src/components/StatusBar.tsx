import React, { memo } from 'react';
import { Box, Text } from 'ink';
import { colors } from '../theme/colors.js';

type StatusBarProps = {
  width: number;
  aiUrl: string;
  isSending: boolean;
  lastError: string | null;
};

function StatusBarComponent({ width, aiUrl, isSending, lastError }: StatusBarProps) {
  const state = isSending ? 'request active' : 'ready';
  const detail = lastError ? `last error - ${lastError}` : 'Ctrl+T activity  Tab commands  Ctrl+P config  Esc cancel or exit';

  return (
    <Box width={width} minHeight={3} flexDirection="column" paddingX={2}>
      <Text color={colors.white}>Build - Live AI - Xninetzy Labs - <Text color={isSending ? colors.indigo : colors.purpleBright}>{state}</Text></Text>
      <Text color={colors.dim}>AI {aiUrl}</Text>
      <Text color={lastError ? colors.orangeBright : colors.muted}>{detail}</Text>
    </Box>
  );
}

export const StatusBar = memo(StatusBarComponent);
