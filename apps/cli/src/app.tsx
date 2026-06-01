import React, { useCallback, useState } from "react";
import { Box, Text, useApp, useInput } from "ink";
import { ChatView } from "./components/ChatView.js";
import { Header } from "./components/Header.js";
import { InputBox } from "./components/InputBox.js";
import { SpaceBackdrop } from "./components/SpaceBackdrop.js";
import { StatusBar } from "./components/StatusBar.js";
import { cliConfig } from "./config/env.js";
import { getMockReply } from "./mock.js";
import { colors } from "./theme/colors.js";
import type { ChatMessage } from "./types.js";

function createMessage(role: ChatMessage["role"], content: string): ChatMessage {
  return {
    id: `${role}-${Date.now()}-${Math.random().toString(16).slice(2)}`,
    role,
    content,
    createdAt: new Date(),
  };
}

export function App() {
  const { exit } = useApp();
  const [messages, setMessages] = useState<ChatMessage[]>([
    createMessage(
      "system",
      `Local mock session ready. No AI/API/backend calls. Env: ${
        cliConfig.envLoaded ? "root .env loaded" : "not loaded"
      }.`,
    ),
  ]);

  const submitMessage = useCallback((rawInput: string) => {
    const input = rawInput.trim();
    if (!input) return;

    const userMessage = createMessage("user", input);
    const assistantMessage = createMessage("assistant", getMockReply(input));
    setMessages((current) => [...current, userMessage, assistantMessage]);
  }, []);

  const pushSystemMessage = useCallback((content: string) => {
    setMessages((current) => [...current, createMessage("system", content)]);
  }, []);

  useInput((input, key) => {
    if (key.escape || (key.ctrl && input === "c")) {
      exit();
      return;
    }

    if (key.tab) {
      pushSystemMessage("Agents menu belum aktif di mock UI.");
      return;
    }

    if (key.ctrl && input === "p") {
      pushSystemMessage("Command palette belum aktif di mock UI.");
    }
  });

  return (
    <Box
      flexDirection="column"
      minHeight={28}
      paddingX={2}
      paddingY={1}
      borderStyle="round"
      borderColor={colors.purple}
    >
      <SpaceBackdrop />
      <Header />
      <Box marginTop={1}>
        <ChatView messages={messages} />
      </Box>
      <Box marginTop={1} flexDirection="column">
        <InputBox onSubmit={submitMessage} />
        <StatusBar config={cliConfig} />
      </Box>
      <Box marginTop={1} justifyContent="center">
        <Text color={colors.lavender}>✦ drifting through your second brain space ✦</Text>
      </Box>
    </Box>
  );
}
