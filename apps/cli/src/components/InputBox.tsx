import React, { useState } from "react";
import { Box, Text } from "ink";
import TextInput from "ink-text-input";
import { colors } from "../theme/colors.js";

interface InputBoxProps {
  onSubmit: (input: string) => void;
}

export function InputBox({ onSubmit }: InputBoxProps) {
  const [value, setValue] = useState("");

  function submit(input: string) {
    onSubmit(input);
    setValue("");
  }

  return (
    <Box flexDirection="column">
      <Box borderStyle="round" borderColor={colors.violet} paddingX={1}>
        <Text color={colors.dim}>Ask anything... </Text>
        <TextInput
          value={value}
          onChange={setValue}
          onSubmit={submit}
          placeholder={'try "halo"'}
        />
      </Box>
    </Box>
  );
}
