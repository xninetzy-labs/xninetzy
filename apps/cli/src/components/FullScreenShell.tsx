import React from 'react';
import { Box } from 'ink';

type FullScreenShellProps = {
  children: React.ReactNode;
  columns: number;
  rows: number;
  height?: number;
};

export function FullScreenShell({
  children,
  columns,
  rows,
  height
}: FullScreenShellProps) {
  return (
    <Box
      width={Math.max(1, columns)}
      height={Math.max(1, height ?? rows - 1)}
      flexDirection="column"
      flexShrink={0}
      overflow="hidden"
    >
      {children}
    </Box>
  );
}
