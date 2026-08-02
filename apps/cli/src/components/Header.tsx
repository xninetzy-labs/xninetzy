import React, { memo } from 'react';
import { Box, Text } from 'ink';
import { colors } from '../theme/colors.js';

type HeaderProps = {
  columns: number;
  compact?: boolean;
};

const logo = [
  '██╗  ██╗███╗   ██╗██╗███╗   ██╗███████╗████████╗███████╗██╗   ██╗',
  '╚██╗██╔╝████╗  ██║██║████╗  ██║██╔════╝╚══██╔══╝╚══███╔╝╚██╗ ██╔╝',
  ' ╚███╔╝ ██╔██╗ ██║██║██╔██╗ ██║█████╗     ██║     ███╔╝  ╚████╔╝ ',
  ' ██╔██╗ ██║╚██╗██║██║██║╚██╗██║██╔══╝     ██║    ███╔╝    ╚██╔╝  ',
  '██╔╝ ██╗██║ ╚████║██║██║ ╚████║███████╗   ██║   ███████╗   ██║   ',
  '╚═╝  ╚═╝╚═╝  ╚═══╝╚═╝╚═╝  ╚═══╝╚══════╝   ╚═╝   ╚══════╝   ╚═╝   '
];

function HeaderComponent({ columns, compact = false }: HeaderProps) {
  const useCompact = compact || columns < 96;

  return (
    <Box flexDirection="column" alignItems="center" width="100%">
      {useCompact ? (
        <Text bold color={colors.purpleBright}>X N I N E T Z Y</Text>
      ) : (
        <Box flexDirection="column" alignItems="center">
          {logo.map((line, index) => (
            <Text key={index} bold color={colors.purpleBright}>
              {line}
            </Text>
          ))}
        </Box>
      )}

      <Text color={colors.white}>
        future-ready AI session shell · live backend · cosmos
      </Text>

      <Text color={colors.orange}>
        ───── ◎ event horizon ◎ ─────
      </Text>
    </Box>
  );
}

export const Header = memo(HeaderComponent);
