import React from 'react';
import { Box, Text } from 'ink';
import { colors } from '../theme/colors.js';

type SpaceBackdropProps = {
  compact?: boolean;
};

export function SpaceBackdrop({ compact = false }: SpaceBackdropProps) {
  if (compact) {
    return null;
  }

  return (
    <Box width="100%" justifyContent="center">
      <Text color={colors.indigo}>
        ·        ✦             ·        *          ✧        ◌
      </Text>
    </Box>
  );
}
