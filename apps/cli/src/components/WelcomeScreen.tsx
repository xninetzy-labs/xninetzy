import React, { memo } from 'react';
import { Box, Text } from 'ink';
import { colors } from '../theme/colors.js';
import { StaticStarBackdrop } from './StaticStarBackdrop.js';

type WelcomeScreenProps = {
  columns: number;
  rows: number;
  children: React.ReactNode;
};

const largeLogo = [
  '██╗  ██╗███╗   ██╗██╗███╗   ██╗███████╗████████╗███████╗██╗   ██╗',
  '╚██╗██╔╝████╗  ██║██║████╗  ██║██╔════╝╚══██╔══╝╚══███╔╝╚██╗ ██╔╝',
  ' ╚███╔╝ ██╔██╗ ██║██║██╔██╗ ██║█████╗     ██║     ███╔╝  ╚████╔╝ ',
  ' ██╔██╗ ██║╚██╗██║██║██║╚██╗██║██╔══╝     ██║    ███╔╝    ╚██╔╝  ',
  '██╔╝ ██╗██║ ╚████║██║██║ ╚████║███████╗   ██║   ███████╗   ██║   ',
  '╚═╝  ╚═╝╚═╝  ╚═══╝╚═╝╚═╝  ╚═══╝╚══════╝   ╚═╝   ╚══════╝   ╚═╝   '
];

function logoColor(index: number): string {
  return [colors.cyanBright, colors.blueBright, colors.indigo, colors.purpleBright][index % 4] ?? colors.purpleBright;
}

function WelcomeScreenComponent({ columns, rows, children }: WelcomeScreenProps) {
  const showLargeLogo = columns >= 94;
  const height = Math.max(1, rows - 1);

  return (
    <Box width={columns} height={height} position="relative" overflow="hidden">
      <StaticStarBackdrop width={columns} height={height} density={0.012} />
      <Box
        width={columns}
        height={height}
        flexDirection="column"
        alignItems="center"
        justifyContent="center"
      >
        <Box flexDirection="column" alignItems="center" marginBottom={3}>
          {showLargeLogo ? (
            largeLogo.map((line, index) => (
              <Text key={String(index) + '-' + line} bold color={logoColor(index)}>
                {line}
              </Text>
            ))
          ) : (
            <Text bold color={colors.cyanBright}>X N I N E T Z Y</Text>
          )}
          <Box marginTop={1}>
            <Text color={colors.dim}>comet trail</Text>
            <Text color={colors.borderDim}>{' '}·{' '}</Text>
            <Text color={colors.blueBright}>neon intelligence</Text>
            <Text color={colors.borderDim}>{' '}·{' '}</Text>
            <Text color={colors.dim}>live tools</Text>
            <Text color={colors.borderDim}>{' '}·{' '}</Text>
            <Text color={colors.purpleBright}>memory OS</Text>
          </Box>
          <Box marginTop={1}>
            <Text color={colors.orangeBright}>───── ◎ event horizon ◎ ─────</Text>
          </Box>
        </Box>
        {children}
        <Box marginTop={2}>
          <Text color={colors.dim}>✦ your second brain workspace</Text>
        </Box>
      </Box>
    </Box>
  );
}

export const WelcomeScreen = memo(WelcomeScreenComponent);
