import React from "react";
import { Box, Text } from "ink";
import { colors } from "../theme/colors.js";
import type { ChatMessage } from "../types.js";

interface ChatViewProps {
  messages: ChatMessage[];
}

function roleLabel(role: ChatMessage["role"]): string {
  if (role === "user") return "You";
  if (role === "assistant") return "Xninetzy";
  return "System";
}

function roleColor(role: ChatMessage["role"]): string {
  if (role === "user") return colors.lavender;
  if (role === "assistant") return colors.violet;
  return colors.muted;
}

export function ChatView({ messages }: ChatViewProps) {
  const visibleMessages = messages.slice(-8);

  return (
    <Box
      flexDirection="column"
      minHeight={8}
      borderStyle="single"
      borderColor={colors.indigo}
      paddingX={2}
      paddingY={1}
    >
      {visibleMessages.map((message) => (
        <Box key={message.id} flexDirection="column" marginBottom={1}>
          <Text color={roleColor(message.role)} bold>
            {roleLabel(message.role)}
          </Text>
          <Text color={message.role === "system" ? colors.dim : colors.text}>
            {message.content}
          </Text>
        </Box>
      ))}
    </Box>
  );
}
