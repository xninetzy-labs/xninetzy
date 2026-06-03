import React from 'react';
import { Box, Text } from 'ink';
import { colors } from '../theme/colors.js';

type StatusBarProps = {
  width: number;
};

export function StatusBar({ width }: StatusBarProps) {
  return (
    <Box width={width} flexDirection="column" paddingX={2}>
      <Text color={colors.white}>
        Build · Local Mock · Xninetzy Labs · <Text color={colors.orange}>max</Text>
      </Text>
      <Text color={colors.dim}>
        env root · future AI http://ai:8000
      </Text>
      <Text color={colors.muted}>
        tab agents     ctrl+p commands     esc exit     ctrl+c quit
      </Text>
    </Box>
  );
}
