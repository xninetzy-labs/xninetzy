import React, { useEffect, useState } from 'react';
import { Box, Text } from 'ink';
import { colors } from '../theme/colors.js';

type SpaceBackdropProps = {
  compact?: boolean;
};

export function SpaceBackdrop({ compact = false }: SpaceBackdropProps) {
  const [frame, setFrame] = useState(0);

  useEffect(() => {
    if (compact) return;
    const timer = setInterval(() => setFrame((current) => (current + 1) % 3), 900);
    return () => clearInterval(timer);
  }, [compact]);

  if (compact) {
    return null;
  }

  const trails = [
    '☄          ·        ✦             ·        *          ✧        ◌',
    '   ☄       ·             ✦        ·          *        ✧        ◌',
    '      ☄    ·        ✦             ·        *          ✧        ◌'
  ];

  return (
    <Box width="100%" justifyContent="center">
      <Text color={colors.indigo}>
        {trails[frame]}
      </Text>
    </Box>
  );
}
