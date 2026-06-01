import React from "react";
import { Box, Text } from "ink";
import type { CliConfig } from "../config/env.js";
import { colors } from "../theme/colors.js";

interface StatusBarProps {
  config: CliConfig;
}

export function StatusBar({ config }: StatusBarProps) {
  return (
    <Box flexDirection="column" alignItems="center" marginTop={1}>
      <Text color={colors.lavender}>Build · Local Mock · Xninetzy Zen · max</Text>
      <Text color={colors.dim}>
        env {config.envLoaded ? "root" : "none"} · future AI {config.aiUrl}
      </Text>
      <Text color={colors.muted}>tab agents     ctrl+p commands     esc exit     ctrl+c quit</Text>
    </Box>
  );
}
