import React, { memo } from 'react';
import { Box, Text } from 'ink';
import { colors } from '../theme/colors.js';

type SpaceBackdropProps = {
  compact?: boolean;
};

function SpaceBackdropComponent({ compact = false }: SpaceBackdropProps) {
  if (compact) return null;

  return (
    <Box width="100%" justifyContent="center">
      <Text color={colors.indigo}>      comet trail - starfield - Xninetzy OS - starfield      </Text>
    </Box>
  );
}

export const SpaceBackdrop = memo(SpaceBackdropComponent);
