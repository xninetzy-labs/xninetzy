import React, { useEffect, useState } from 'react';
import { Box, Text } from 'ink';
import { colors } from '../theme/colors.js';

type StatusBarProps = {
  width: number;
  aiUrl: string;
  isSending: boolean;
  activity: string | null;
  lastError: string | null;
};

export function StatusBar({ width, aiUrl, isSending, activity, lastError }: StatusBarProps) {
  const [frame, setFrame] = useState(0);
  useEffect(() => { if (!isSending) return; const timer = setInterval(() => setFrame((value) => (value + 1) % 4), 180); return () => clearInterval(timer); }, [isSending]);
  const orbit = ["◐", "◓", "◑", "◒"][frame];
  return (
    <Box width={width} flexDirection="column" paddingX={2}>
      <Text color={colors.white}>
        Build · Live AI · Xninetzy Labs ·{' '}
        <Text color={isSending ? colors.orange : colors.purpleBright}>
          {isSending ? orbit + ' thinking' : 'ready'}
        </Text>
      </Text>
      <Text color={colors.dim}>
        AI {aiUrl}
      </Text>
      {activity && <Text color={colors.purpleBright}>activity · {activity}</Text>}
      {isSending && <Text color={colors.indigo}>✦ ◌ · ✧ · ◌ · ✦  processing safely  ✦</Text>}
      {lastError && <Text color={colors.orange}>last error · {lastError}</Text>}
      <Text color={colors.muted}>
        tab agents     ctrl+p commands     esc exit     ctrl+c quit
      </Text>
    </Box>
  );
}
