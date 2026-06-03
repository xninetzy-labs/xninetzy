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

function getMockReply(input: string): string {
  const normalized = input.toLowerCase().trim();

  if (normalized === '/help') {
    return [
      '### Xninetzy Mock Commands',
      '- `/help` — show this help',
      '- `/status` — show local session status',
      '- `/clear` — clear chat',
      '',
      '**Note:** Local mock session active.'
    ].join('\n');
  }

  if (normalized === '/status') {
    return [
      '◎ **Status:** OK',
      '◎ **Mode:** Local Mock',
      '◎ **Version:** `0.1.0-alpha`',
      '',
      'No AI/API/backend calls are being made.'
    ].join('\n');
  }

  if (
    normalized.includes('halo') ||
    normalized.includes('hai') ||
    normalized.includes('hello')
  ) {
    return 'hei yoi this is **xninetzy**. How can I help you today?';
  }

  return 'xninetzy mock mode aktif — `AI belum disambungkan`.';
}

export function App() {
  const { exit } = useApp();
  const [columns, rows] = useStdoutDimensions();

  const [draft, setDraft] = useState('');
  const [attachments, setAttachments] = useState<string[]>([]);
  const [messages, setMessages] = useState<ChatMessage[]>([
    createMessage('system', 'Local mock session ready. No AI/API/backend calls.')
  ]);

  const hasUserMessages = messages.some((message) => message.role === 'user');

  const contentWidth = Math.max(40, columns - 4);
  const compactHeader = rows < 32 || hasUserMessages;

  function addAssistantMessage(content: string) {
    setMessages((current) => [...current, createMessage('assistant', content)]);
  }

  function handleSubmit() {
    const trimmed = draft.trim();
    if (!trimmed && attachments.length === 0) return;

    const pasted = attachments;
    setDraft('');
    setAttachments([]);

    if (trimmed.toLowerCase() === '/clear' && pasted.length === 0) {
      setMessages([
        createMessage('system', 'Local mock session ready. No AI/API/backend calls.')
      ]);
      return;
    }

    setMessages((current) => [
      ...current,
      createMessage('user', trimmed, pasted),
      createMessage('assistant', getMockReply(trimmed || '(pasted content)'))
    ]);
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
      addAssistantMessage('Agents menu belum aktif — **mock UI only**.');
      return;
    }

    if (key.ctrl && inputChar === 'p') {
      addAssistantMessage('Command palette belum aktif — `mock UI only`.');
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
            onSubmit={handleSubmit}
            width={contentWidth}
          />

          <Box height={1} />

          <StatusBar width={contentWidth} />

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
