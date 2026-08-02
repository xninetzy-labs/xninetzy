import React, { useCallback, useEffect, useRef, useState } from 'react';
import { Box, Static, Text, useApp, useInput, useStdout } from 'ink';
import { useStdoutDimensions } from './hooks/useStdoutDimensions.js';
import { SpaceBackdrop } from './components/SpaceBackdrop.js';
import { Header } from './components/Header.js';
import { ChatView } from './components/ChatView.js';
import { InputBox } from './components/InputBox.js';
import { StatusBar } from './components/StatusBar.js';
import { ThinkingPanel } from './components/ThinkingPanel.js';
import { colors } from './theme/colors.js';
import type { ChatMessage } from './types.js';
import { streamChat } from './api/client.js';
import { cliConfig } from './config/env.js';
import { useChatRun } from './hooks/useChatRun.js';

function createMessage(role: ChatMessage['role'], content: string, attachments?: string[]): ChatMessage {
  return { id: `${role}-${Date.now()}-${Math.random().toString(16).slice(2)}`, role, content, attachments: attachments && attachments.length > 0 ? attachments : undefined, createdAt: new Date() };
}

function createRequestId(): string {
  return `cli-${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

function phaseForEvent(label: string): "planning" | "thinking" | "tool-running" | "waiting-approval" {
  const normalized = label.toLowerCase();
  if (normalized.includes("approval") || normalized.includes("confirm")) return "waiting-approval";
  if (normalized.includes("tool") || normalized.includes("mcp") || normalized.includes("search") || normalized.includes("research") || normalized.includes("source")) return "tool-running";
  if (normalized.includes("plan") || normalized.includes("routing") || normalized.includes("workflow")) return "planning";
  return "thinking";
}

type TranscriptItem =
  | { id: "header"; kind: "header" }
  | { id: string; kind: "message"; message: ChatMessage };

export function App() {
  const { exit } = useApp();
  const { stdout } = useStdout();
  const [columns, rows] = useStdoutDimensions();
  const [draft, setDraft] = useState('');
  const [attachments, setAttachments] = useState<string[]>([]);
  const [isSending, setIsSending] = useState(false);
  const [lastError, setLastError] = useState<string | null>(null);
  const [activityExpanded, setActivityExpanded] = useState(false);
  const [transcriptEpoch, setTranscriptEpoch] = useState(0);
  const [messages, setMessages] = useState<ChatMessage[]>([
    createMessage('system', `Halo, aku Xninetzy AI - siap membantu belajar, bekerja, dan mengelola OS-mu.\nBackend: ${cliConfig.aiUrl}`)
  ]);
  const { run, start, addActivity, setPhase, finish, isCurrent, reset } = useChatRun();
  const controllerRef = useRef<AbortController | null>(null);
  const deltaBufferRef = useRef('');
  const deltaTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const assistantIdRef = useRef<string | null>(null);
  const submitRef = useRef<() => Promise<void>>(async () => undefined);
  const hasUserMessages = messages.some((message) => message.role === 'user');
  const contentWidth = Math.max(40, columns - 4);
  const activeMessageId = isSending ? assistantIdRef.current : null;
  const activeMessage = activeMessageId
    ? messages.find((message) => message.id === activeMessageId)
    : undefined;
  const transcriptItems: TranscriptItem[] = [
    { id: "header", kind: "header" },
    ...messages
      .filter((message) => message.role !== "system" && message.id !== activeMessageId)
      .map((message) => ({ id: message.id, kind: "message" as const, message })),
  ];

  const appendAssistant = useCallback((content: string) => {
    setMessages((current) => [...current, createMessage('assistant', content)]);
  }, []);

  const flushDelta = useCallback((requestId: string) => {
    deltaTimerRef.current = null;
    if (!isCurrent(requestId) || !deltaBufferRef.current) return;
    const content = deltaBufferRef.current;
    const assistantId = assistantIdRef.current ?? `stream-${requestId}`;
    assistantIdRef.current = assistantId;
    setMessages((current) => {
      const index = current.findIndex((message) => message.id === assistantId);
      if (index === -1) return [...current, { ...createMessage('assistant', content), id: assistantId }];
      const next = current.slice();
      next[index] = { ...next[index], content };
      return next;
    });
  }, [isCurrent]);

  const cancelActiveRequest = useCallback(() => {
    controllerRef.current?.abort();
  }, []);

  const handleSubmit = useCallback(async () => {
    if (isSending) return;
    const trimmed = draft.trim();
    if (!trimmed && attachments.length === 0) return;
    const pasted = attachments;
    setDraft('');
    setAttachments([]);

    if (trimmed.toLowerCase() === '/clear' && pasted.length === 0) {
      stdout.write("\x1b[2J\x1b[3J\x1b[H\x1b[48;2;17;16;27m\x1b[37m");
      setTranscriptEpoch((current) => current + 1);
      setMessages([createMessage("system", "Halo, aku Xninetzy AI - siap membantu belajar, bekerja, dan mengelola OS-mu.\nBackend: " + cliConfig.aiUrl)]);
      assistantIdRef.current = null;
      reset();
      setLastError(null);
      return;
    }

    const requestId = createRequestId();
    const controller = new AbortController();
    controllerRef.current = controller;
    deltaBufferRef.current = '';
    assistantIdRef.current = null;
    setMessages((current) => [...current, createMessage('user', trimmed, pasted)]);
    setIsSending(true);
    setLastError(null);
    setActivityExpanded(false);
    start(requestId);
    addActivity(requestId, 'request', 'Request accepted', 'active');

    try {
      await streamChat(trimmed, (event) => {
        if (!isCurrent(requestId)) return;
        if (event.type === 'run_started') {
          if (event.requestId === requestId) setPhase(requestId, 'planning');
          return;
        }
        if (event.type === 'phase') {
          if ((event.status ?? 'active') === 'active') setPhase(requestId, phaseForEvent(event.label));
          addActivity(requestId, 'phase', event.label, event.status ?? 'active', event.detail);
          return;
        }
        if (event.type === 'activity' || event.type === 'tool' || event.type === 'agent' || event.type === 'source') {
          if ((event.status ?? 'active') === 'active') setPhase(requestId, phaseForEvent(event.label));
          addActivity(requestId, event.type, event.label, event.status ?? 'active', event.detail);
          return;
        }
        if (event.type === 'delta') {
          setPhase(requestId, 'streaming');
          deltaBufferRef.current += event.delta;
          if (!deltaTimerRef.current) deltaTimerRef.current = setTimeout(() => flushDelta(requestId), 50);
          return;
        }
        if (event.type === 'response') {
          setPhase(requestId, 'streaming');
          deltaBufferRef.current = event.reply;
          flushDelta(requestId);
          return;
        }
        if (event.type === 'done') addActivity(requestId, 'response', 'Response completed', 'completed');
      }, pasted, { requestId, signal: controller.signal });
      flushDelta(requestId);
      if (isCurrent(requestId)) {
        addActivity(requestId, 'request', 'Request accepted', 'completed');
        finish(requestId, 'completed');
      }
    } catch (error) {
      if (controller.signal.aborted) {
        if (isCurrent(requestId)) {
          addActivity(requestId, 'request', 'Request cancelled', 'failed');
          finish(requestId, 'cancelled');
        }
      } else {
        const message = error instanceof Error ? error.message : 'Unknown AI request error';
        flushDelta(requestId);
        const terminalPhase = /timeout/i.test(message) ? 'timed-out' : 'failed';
        if (isCurrent(requestId)) {
          setLastError(message);
          addActivity(requestId, 'request', 'Request failed', 'failed', message);
          if (!assistantIdRef.current) appendAssistant(`AI request gagal: `);
          finish(requestId, terminalPhase, message);
        }
      }
    } finally {
      if (deltaTimerRef.current) {
        clearTimeout(deltaTimerRef.current);
        deltaTimerRef.current = null;
      }
      if (controllerRef.current === controller) controllerRef.current = null;
      setIsSending(false);
    }
  }, [addActivity, appendAssistant, attachments, draft, finish, flushDelta, isCurrent, isSending, reset, setPhase, start, stdout]);

  submitRef.current = handleSubmit;

  const handleInputSubmit = useCallback(() => {
    void submitRef.current();
  }, []);

  const handlePaste = useCallback((block: string) => {
    setAttachments((current) => [...current, block]);
  }, []);

  const handleRemoveLastAttachment = useCallback(() => {
    setAttachments((current) => current.slice(0, -1));
  }, []);

  useEffect(() => {
    return () => {
      controllerRef.current?.abort();
      if (deltaTimerRef.current) clearTimeout(deltaTimerRef.current);
    };
  }, []);

  useInput((inputChar, key) => {
    if (key.escape) {
      if (isSending) cancelActiveRequest();
      else exit();
      return;
    }
    if (key.ctrl && inputChar === 'c') {
      if (isSending) cancelActiveRequest();
      else exit();
      return;
    }
    if (key.ctrl && inputChar === 't') {
      setActivityExpanded((value) => !value);
      return;
    }
    if (key.tab && !isSending) {
      appendAssistant('Gunakan /commands untuk melihat command Xninetzy, atau /tools untuk katalog tool MCP.');
      return;
    }
    if (key.ctrl && inputChar === 'p' && !isSending) appendAssistant('Konfigurasi host: xninetzy config list|get|set|unset|validate.');
  });

  return (
    <Box width={columns} flexDirection="column">
      <Static key={transcriptEpoch} items={transcriptItems}>
        {(item) =>
          item.kind === "header" ? (
            <Box key={item.id} width={contentWidth} flexDirection="column">
              <SpaceBackdrop compact={rows < 32} />
              <Header columns={columns} compact={rows < 32} />
              <Box height={1} />
            </Box>
          ) : (
            <ChatView key={item.id} messages={[item.message]} width={contentWidth} />
          )
        }
      </Static>
      {!hasUserMessages && !activeMessage && (
        <Box width={contentWidth} paddingX={1}>
          <Text color={colors.dim}>Live AI session ready. Ketik pesan untuk mulai.</Text>
        </Box>
      )}
      {activeMessage && (
        <ChatView
          messages={[activeMessage]}
          width={contentWidth}
          maxContentLines={activityExpanded ? 2 : 6}
        />
      )}
      <ThinkingPanel run={run} expanded={activityExpanded} />
      <InputBox
        draft={draft}
        attachments={attachments}
        onDraftChange={setDraft}
        onPaste={handlePaste}
        onRemoveLastAttachment={handleRemoveLastAttachment}
        onSubmit={handleInputSubmit}
        width={contentWidth}
      />
      <Box height={1} />
      <StatusBar
        width={contentWidth}
        aiUrl={cliConfig.aiUrl}
        isSending={isSending}
        lastError={lastError}
      />
      <Box width={contentWidth} paddingX={2}>
        <Text color={colors.white}>drifting through your second brain space</Text>
      </Box>
    </Box>
  );
}