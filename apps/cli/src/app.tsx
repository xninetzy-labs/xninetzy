import React, { useState } from 'react';
import { Box, Text, useApp, useInput } from 'ink';
import { useStdoutDimensions } from './hooks/useStdoutDimensions.js';
import { FullScreenShell } from './components/FullScreenShell.js';
import { SpaceBackdrop } from './components/SpaceBackdrop.js';
import { Header } from './components/Header.js';
import { ChatView } from './components/ChatView.js';
import { InputBox } from './components/InputBox.js';
import { StatusBar } from './components/StatusBar.js';
import { colors } from './theme/colors.js';
import type { ChatMessage } from './types.js';
import { streamChat } from './api/client.js';
import { cliConfig } from './config/env.js';

function createMessage(
  role: ChatMessage['role'],
  content: string,
  attachments?: string[]
): ChatMessage {
  return {
    id: `${role}-${Date.now()}-${Math.random().toString(16).slice(2)}`,
    role,
    content,
    attachments: attachments && attachments.length > 0 ? attachments : undefined,
    createdAt: new Date()
  };
}

export function App() {
  const { exit } = useApp();
  const [columns, rows] = useStdoutDimensions();

  const [draft, setDraft] = useState('');
  const [attachments, setAttachments] = useState<string[]>([]);
  const [isSending, setIsSending] = useState(false);
  const [lastError, setLastError] = useState<string | null>(null);
  const [activity, setActivity] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([
    createMessage('system', `Halo, aku Xninetzy AI — siap membantu belajar, bekerja, dan mengelola OS-mu.
Backend: ${cliConfig.aiUrl}`)
  ]);

  const hasUserMessages = messages.some((message) => message.role === 'user');

  const contentWidth = Math.max(40, columns - 4);
  const compactHeader = rows < 32 || hasUserMessages;

  function addAssistantMessage(content: string) {
    setMessages((current) => [...current, createMessage('assistant', content)]);
  }

  async function handleSubmit() {
    if (isSending) return;
    const trimmed = draft.trim();
    if (!trimmed && attachments.length === 0) return;

    const pasted = attachments;
    setDraft('');
    setAttachments([]);

    if (trimmed.toLowerCase() === '/clear' && pasted.length === 0) {
      setMessages([
        createMessage('system', `Halo, aku Xninetzy AI — siap membantu belajar, bekerja, dan mengelola OS-mu.
Backend: ${cliConfig.aiUrl}`)
      ]);
      setLastError(null);
      setActivity(null);
      return;
    }

    setMessages((current) => [...current, createMessage('user', trimmed, pasted)]);
    setIsSending(true);
    setLastError(null);
    setActivity('Routing request');
    const thinkingId = "thinking-" + Date.now();
    const thinkingStarted = Date.now();
    let thinkingTimer: ReturnType<typeof setInterval> | undefined;
    const updateThinking = () => {
      const elapsed = ((Date.now() - thinkingStarted) / 1000).toFixed(1);
      const orbit = ["◐", "◓", "◑", "◒"][Math.floor(Date.now() / 180) % 4];
      setMessages((current) => current.map((message) => message.id === thinkingId ? { ...message, content: `${orbit} Thinking · ${elapsed}s · grounding and tools` } : message));
    };
    setMessages((current) => [...current, { ...createMessage("system", "◐ Thinking · 0.0s · preparing Xninetzy OS"), id: thinkingId }]);
    thinkingTimer = setInterval(updateThinking, 180);
    let streamedReply = "";
    try {
      await streamChat(
        trimmed,
        (event) => {
          if (event.type === "delta") {
            if (thinkingTimer) { clearInterval(thinkingTimer); thinkingTimer = undefined; }
            setMessages((current) => current.filter((message) => message.id !== thinkingId));
            streamedReply += event.delta;
            setActivity("Streaming response");
            setMessages((current) => {
              const last = current[current.length - 1];
              if (last?.role === "assistant" && last.id.startsWith("stream-")) {
                return [...current.slice(0, -1), { ...last, content: streamedReply }];
              }
              return [...current, { ...createMessage("assistant", streamedReply), id: "stream-" + Date.now() }];
            });
          }
          if (event.type === "status" || event.type === "tool") setActivity(event.label);
          if (event.type === "response") {
            setMessages((current) => current.filter((message) => message.id !== thinkingId));
            setActivity(null);
            setMessages((current) => [...current, createMessage("assistant", event.reply)]);
          }
        },
        pasted
      );
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Unknown AI request error';
      setLastError(message);
      setMessages((current) => [
        ...current,
        createMessage('assistant', `⚠ AI request gagal: ${message}`)
      ]);
    } finally {
      if (thinkingTimer) clearInterval(thinkingTimer);
      setMessages((current) => current.filter((message) => message.id !== thinkingId));
      setActivity(null);
      setIsSending(false);
    }
  }

  function handleRemoveLastAttachment() {
    setAttachments((current) => current.slice(0, -1));
  }

  useInput((inputChar, key) => {
    if (key.escape || (key.ctrl && inputChar === 'c')) {
      exit();
      return;
    }

    if (key.tab) {
      addAssistantMessage('Agents menu belum tersedia di client CLI ini.');
      return;
    }

    if (key.ctrl && inputChar === 'p') {
      addAssistantMessage('Command palette belum tersedia di client CLI ini.');
    }
  });

  return (
    <FullScreenShell>
      <Box width={columns} minHeight={rows} flexDirection="column">
        <Box height={hasUserMessages ? 1 : 3} />

        <SpaceBackdrop compact={compactHeader} />

        <Box height={compactHeader ? 0 : 1} />

        <Header columns={columns} compact={compactHeader} />

        <Box height={1} />

        <Box flexGrow={1} flexDirection="column" justifyContent="flex-end">
          <ChatView messages={messages} width={contentWidth} />

          <Box height={1} />

          <InputBox
            draft={draft}
            attachments={attachments}
            onDraftChange={setDraft}
            onPaste={(block) => setAttachments((current) => [...current, block])}
            onRemoveLastAttachment={handleRemoveLastAttachment}
            onSubmit={() => void handleSubmit()}
            disabled={isSending}
            width={contentWidth}
          />

          <Box height={1} />

          <StatusBar
            width={contentWidth}
            aiUrl={cliConfig.aiUrl}
            isSending={isSending}
            activity={activity}
            lastError={lastError}
          />

          <Box height={1} />

          <Box width={contentWidth} paddingX={2}>
            <Text color={colors.white}>
              ✦ drifting through your second brain space ✦
            </Text>
          </Box>

          <Box height={1} />
        </Box>
      </Box>
    </FullScreenShell>
  );
}
