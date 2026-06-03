import React from 'react';
import { Box } from 'ink';
import { useStdoutDimensions } from '../hooks/useStdoutDimensions.js';
import { colors } from '../theme/colors.js';

type FullScreenShellProps = {
  children: React.ReactNode;
};

export function FullScreenShell({ children }: FullScreenShellProps) {
  const [columns, rows] = useStdoutDimensions();

  return (
    <Box
      width={columns}
      minHeight={rows}
      flexDirection="column"
      paddingX={1}
    >
      {children}
    </Box>
  );
}
