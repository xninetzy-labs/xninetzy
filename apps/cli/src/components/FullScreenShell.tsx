import React from 'react';
import { Box } from 'ink';

type FullScreenShellProps = {
  children: React.ReactNode;
  columns: number;
  rows: number;
};

export function FullScreenShell({ children, columns, rows }: FullScreenShellProps) {
  return (
    <Box
      width={columns}
      height={Math.max(1, rows - 1)}
      flexDirection="column"
    >
      {children}
    </Box>
  );
}
