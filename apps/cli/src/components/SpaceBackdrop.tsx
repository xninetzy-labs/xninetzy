import React from "react";
import { Box, Text } from "ink";
import { colors } from "../theme/colors.js";

export function SpaceBackdrop() {
  return (
    <Box justifyContent="center">
      <Text color={colors.indigo}>✦  ·  *  .     ✧       ·    ✦      .  *  ·  ✧</Text>
    </Box>
  );
}
