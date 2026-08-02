import React, { memo } from 'react';
import { Box, Text } from 'ink';

import { colors } from '../theme/colors.js';

type HeaderProps = {
  width: number;
  isSending: boolean;
};

function HeaderComponent({
  width,
  isSending
}: HeaderProps) {
  return (
    <Box
      width={width}
      flexDirection="column"
      paddingX={1}
    >
      <Box
        width="100%"
        justifyContent="space-between"
      >
        <Box>
          <Text bold color={colors.cyanBright}>
            XNINETZY
          </Text>

          <Text color={colors.dim}>
            {' '}· neon intelligence shell
          </Text>
        </Box>

        <Text
          color={
            isSending
              ? colors.cyan
              : colors.muted
          }
        >
          {isSending
            ? '● live request'
            : '○ ready'}
        </Text>
      </Box>

      <Text color={colors.borderDim}>
        {'─'.repeat(Math.max(1, width - 2))}
      </Text>
    </Box>
  );
}

export const Header = memo(HeaderComponent);
