import React, { memo } from 'react';
import { Box, Text } from 'ink';

import { colors } from '../theme/colors.js';
import { cliConfig } from '../config/env.js';

type StatusBarProps = {
  width: number;
  aiUrl: string;
};

function StatusBarComponent({
  width,
  aiUrl
}: StatusBarProps) {
  return (
    <Box
      width={width}
      flexDirection="column"
      paddingX={1}
      flexShrink={0}
    >
      <Text color={colors.borderDim}>
        {'─'.repeat(Math.max(1, width - 2))}
      </Text>

      <Box
        width="100%"
        justifyContent="space-between"
      >
        <Text color={colors.muted}>
          ~/code/xninetzy
        </Text>

        <Text color={colors.muted}>
          Ctrl+T activity
          {'  '}Ctrl+P config
          {'  '}Esc exit
        </Text>
      </Box>

      <Box
        width="100%"
        justifyContent="space-between"
      >
        <Box>
          <Text color={colors.dim}>
            AI {aiUrl}
          </Text>

          <Text color={colors.dim}>
            {' '}·{' '}
          </Text>

          <Text
            color={
              cliConfig.envLoaded
                ? colors.green
                : colors.yellow
            }
          >
            {cliConfig.envLoaded
              ? 'env loaded'
              : 'env defaults'}
          </Text>
        </Box>

        <Text color={colors.green}>
          ● ready
        </Text>
      </Box>
    </Box>
  );
}

export const StatusBar = memo(
  StatusBarComponent
);
