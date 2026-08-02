import React, {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState
} from 'react';

import { performance } from 'node:perf_hooks';

import {
  Box,
  useApp,
  useInput
} from 'ink';

import { useTerminalSize } from './hooks/useTerminalSize.js';

import { FullScreenShell } from './components/FullScreenShell.js';
import { WelcomeScreen } from './components/WelcomeScreen.js';
import { Header } from './components/Header.js';
import { MessageViewport } from './components/MessageViewport.js';
import { InputBox } from './components/InputBox.js';
import { StatusBar } from './components/StatusBar.js';
import { ThinkingPanel } from './components/ThinkingPanel.js';

import type { ChatMessage } from './types.js';

import type {
  ChatActivityKind,
  ChatActivityStatus,
  ChatRun
} from './types/chat-run.js';

import { streamChat } from './api/client.js';
import { cliConfig } from './config/env.js';
import { useChatRun } from './hooks/useChatRun.js';

function createMessage(
  role: ChatMessage['role'],
  content: string,
  attachments?: string[]
): ChatMessage {
  return {
    id: `${role}-${Date.now()}-${Math.random()
      .toString(16)
      .slice(2)}`,

    role,
    content,

    attachments:
      attachments &&
      attachments.length > 0
        ? attachments
        : undefined,

    createdAt: new Date()
  };
}

function createRequestId(): string {
  return `cli-${Date.now()}-${Math.random()
    .toString(16)
    .slice(2)}`;
}

function phaseForEvent(
  label: string
):
  | 'planning'
  | 'thinking'
  | 'tool-running'
  | 'waiting-approval' {
  const normalized = label.toLowerCase();

  if (
    normalized.includes('approval') ||
    normalized.includes('confirm')
  ) {
    return 'waiting-approval';
  }

  if (
    normalized.includes('tool') ||
    normalized.includes('mcp') ||
    normalized.includes('search') ||
    normalized.includes('research') ||
    normalized.includes('source') ||
    normalized.includes('retrieve')
  ) {
    return 'tool-running';
  }

  if (
    normalized.includes('plan') ||
    normalized.includes('routing') ||
    normalized.includes('workflow')
  ) {
    return 'planning';
  }

  return 'thinking';
}

function isTerminalRun(run: ChatRun): boolean {
  return [
    'completed',
    'cancelled',
    'timed-out',
    'failed'
  ].includes(run.phase);
}

function cloneRun(run: ChatRun): ChatRun {
  return {
    ...run,

    activity: run.activity.map((activity) => ({
      ...activity
    }))
  };
}

function hasDeepResearch(run: ChatRun): boolean {
  return run.activity.some((activity) => {
    const content = [
      activity.label,
      activity.detail ?? ''
    ]
      .join(' ')
      .toLowerCase();

    return (
      content.includes('deep research') ||
      content.includes('deep-research')
    );
  });
}

function hasMcpActivity(run: ChatRun): boolean {
  return run.activity.some((activity) => {
    const content = [
      activity.label,
      activity.detail ?? ''
    ]
      .join(' ')
      .toLowerCase();

    return content.includes('mcp');
  });
}

function timeoutForRun(run: ChatRun): number {
  if (hasDeepResearch(run)) {
    return cliConfig.deepResearchTimeoutMs;
  }

  if (run.phase === 'streaming') {
    return cliConfig.streamTimeoutMs;
  }

  if (run.phase === 'tool-running') {
    return hasMcpActivity(run)
      ? cliConfig.mcpCallTimeoutMs
      : cliConfig.toolTimeoutMs;
  }

  return cliConfig.thinkTimeoutMs;
}

export function App() {
  const { exit } = useApp();

  const { columns, rows } =
    useTerminalSize();

  const [draft, setDraft] =
    useState('');

  const [attachments, setAttachments] =
    useState<string[]>([]);

  const [isSending, setIsSending] =
    useState(false);

  const [lastError, setLastError] =
    useState<string | null>(null);

  const [
    activityExpanded,
    setActivityExpanded
  ] = useState(false);

  const [messages, setMessages] =
    useState<ChatMessage[]>([
      createMessage(
        'system',
        `Xninetzy Neon AI\nBackend: ${cliConfig.aiUrl}`
      )
    ]);

  const [runSnapshots, setRunSnapshots] =
    useState<Record<string, ChatRun>>({});

  const {
    run,
    start,
    addActivity,
    setPhase,
    finish,
    isCurrent,
    reset
  } = useChatRun();

  const controllerRef =
    useRef<AbortController | null>(null);

  const deltaBufferRef =
    useRef('');

  const deltaTimerRef =
    useRef<
      ReturnType<typeof setTimeout> | null
    >(null);

  const assistantIdRef =
    useRef<string | null>(null);

  const submitRef =
    useRef<() => Promise<void>>(
      async () => undefined
    );

  const lastEventAtRef =
    useRef<number>(performance.now());

  const timeoutReasonRef =
    useRef<string | null>(null);

  const contentWidth =
    Math.max(40, columns - 4);

  const welcomeInputWidth =
    Math.min(
      92,
      Math.max(44, columns - 12)
    );

  const layout = useMemo(() => {
    const screenHeight = Math.max(12, rows - 1);
    const headerHeight = 2;
    const composerHeight = 5;
    const footerHeight = 3;
    const minimumMessageHeight = 6;
    const availableActivityHeight = Math.max(
      0,
      screenHeight -
        headerHeight -
        composerHeight -
        footerHeight -
        minimumMessageHeight
    );
    const activityHeight = isSending
      ? Math.min(7, availableActivityHeight)
      : 0;
    const messageHeight = Math.max(
      1,
      screenHeight -
        headerHeight -
        composerHeight -
        footerHeight -
        activityHeight
    );

    return {
      screenHeight,
      headerHeight,
      composerHeight,
      footerHeight,
      activityHeight,
      messageHeight
    };
  }, [isSending, rows]);

  const hasConversation =
    messages.some(
      (message) =>
        message.role === 'user' ||
        message.role === 'assistant'
    );

  const activeMessageId =
    isSending
      ? assistantIdRef.current
      : null;

  const activeMessage =
    activeMessageId
      ? messages.find(
          (message) =>
            message.id === activeMessageId
        )
      : undefined;

  const settledMessages = useMemo(() => {
    return messages.filter(
      (message) =>
        message.id !== activeMessageId
    );
  }, [
    activeMessageId,
    messages
  ]);

  const markBackendActivity = useCallback(() => {
    lastEventAtRef.current = performance.now();
  }, []);

  const appendAssistant = useCallback(
    (content: string): string => {
      const message = createMessage(
        'assistant',
        content
      );

      setMessages((current) => [
        ...current,
        message
      ]);

      return message.id;
    },
    []
  );

  const flushDelta = useCallback(
    (requestId: string) => {
      deltaTimerRef.current = null;

      if (
        !isCurrent(requestId) ||
        !deltaBufferRef.current
      ) {
        return;
      }

      const content = deltaBufferRef.current;

      const assistantId =
        assistantIdRef.current ??
        `stream-${requestId}`;

      assistantIdRef.current = assistantId;

      setMessages((current) => {
        const index = current.findIndex(
          (message) =>
            message.id === assistantId
        );

        if (index === -1) {
          return [
            ...current,
            {
              ...createMessage(
                'assistant',
                content
              ),
              id: assistantId
            }
          ];
        }

        if (current[index].content === content) {
          return current;
        }

        const next = current.slice();

        next[index] = {
          ...next[index],
          content
        };

        return next;
      });
    },
    [isCurrent]
  );

  const cancelActiveRequest =
    useCallback(() => {
      timeoutReasonRef.current = null;
      controllerRef.current?.abort();
    }, []);

  const handleSubmit =
    useCallback(async () => {
      if (isSending) {
        return;
      }

      const trimmed = draft.trim();

      if (
        !trimmed &&
        attachments.length === 0
      ) {
        return;
      }

      const pasted = attachments.slice();

      setDraft('');
      setAttachments([]);

      if (
        trimmed.toLowerCase() === '/clear' &&
        pasted.length === 0
      ) {
        controllerRef.current?.abort();

        setMessages([
          createMessage(
            'system',
            `Xninetzy Neon AI\nBackend: ${cliConfig.aiUrl}`
          )
        ]);

        setRunSnapshots({});

        assistantIdRef.current = null;
        deltaBufferRef.current = '';
        timeoutReasonRef.current = null;

        reset();

        setLastError(null);
        setActivityExpanded(false);

        return;
      }

      const requestId = createRequestId();
      const controller = new AbortController();

      controllerRef.current = controller;

      deltaBufferRef.current = '';
      assistantIdRef.current = null;
      timeoutReasonRef.current = null;

      lastEventAtRef.current = performance.now();

      setMessages((current) => [
        ...current,
        createMessage(
          'user',
          trimmed,
          pasted
        )
      ]);

      setIsSending(true);
      setLastError(null);
      setActivityExpanded(false);

      start(requestId);

      addActivity(
        requestId,
        'request',
        'Request accepted',
        'active'
      );

      try {
        await streamChat(
          trimmed,

          (event) => {
            if (!isCurrent(requestId)) {
              return;
            }

            markBackendActivity();

            if (
              'requestId' in event &&
              event.requestId &&
              event.requestId !== requestId
            ) {
              return;
            }

            if (event.type === 'run_started') {
              setPhase(
                requestId,
                'planning'
              );

              return;
            }

            if (event.type === 'phase') {
              const status =
                event.status ??
                'active';

              if (status === 'active') {
                setPhase(
                  requestId,
                  phaseForEvent(event.label)
                );
              }

              addActivity(
                requestId,
                'phase',
                event.label,
                status as ChatActivityStatus,
                event.detail
              );

              return;
            }

            if (
              event.type === 'activity' ||
              event.type === 'tool' ||
              event.type === 'agent' ||
              event.type === 'source'
            ) {
              const status =
                event.status ??
                'active';

              if (status === 'active') {
                setPhase(
                  requestId,
                  phaseForEvent(event.label)
                );
              }

              addActivity(
                requestId,
                event.type as ChatActivityKind,
                event.label,
                status as ChatActivityStatus,
                event.detail
              );

              return;
            }

            if (event.type === 'delta') {
              setPhase(
                requestId,
                'streaming'
              );

              deltaBufferRef.current +=
                event.delta;

              if (!deltaTimerRef.current) {
                deltaTimerRef.current =
                  setTimeout(() => {
                    flushDelta(requestId);
                  }, 40);
              }

              return;
            }

            if (event.type === 'response') {
              setPhase(
                requestId,
                'streaming'
              );

              deltaBufferRef.current =
                event.reply;

              flushDelta(requestId);

              return;
            }

            if (event.type === 'done') {
              addActivity(
                requestId,
                'response',
                'Response completed',
                'completed'
              );
            }
          },

          pasted,

          {
            requestId,
            signal: controller.signal
          }
        );

        flushDelta(requestId);

        if (isCurrent(requestId)) {
          if (!assistantIdRef.current) {
            assistantIdRef.current =
              appendAssistant(
                'Permintaan selesai tanpa konten jawaban.'
              );
          }

          addActivity(
            requestId,
            'request',
            'Request accepted',
            'completed'
          );

          finish(
            requestId,
            'completed'
          );
        }
      } catch (error) {
        const timeoutReason =
          timeoutReasonRef.current;

        if (controller.signal.aborted) {
          if (isCurrent(requestId)) {
            if (timeoutReason) {
              addActivity(
                requestId,
                'request',
                'Request timed out',
                'failed',
                timeoutReason
              );

              if (!assistantIdRef.current) {
                assistantIdRef.current =
                  appendAssistant(
                    `Request dihentikan karena timeout: ${timeoutReason}`
                  );
              }

              setLastError(timeoutReason);

              finish(
                requestId,
                'timed-out',
                timeoutReason
              );
            } else {
              addActivity(
                requestId,
                'request',
                'Request cancelled',
                'failed'
              );

              if (!assistantIdRef.current) {
                assistantIdRef.current =
                  appendAssistant(
                    'Request dibatalkan. Output parsial dipertahankan.'
                  );
              }

              finish(
                requestId,
                'cancelled'
              );
            }
          }
        } else {
          const message =
            error instanceof Error
              ? error.message
              : 'Unknown AI request error';

          flushDelta(requestId);

          const terminalPhase:
            | 'timed-out'
            | 'failed' =
            /timeout/i.test(message)
              ? 'timed-out'
              : 'failed';

          if (isCurrent(requestId)) {
            setLastError(message);

            addActivity(
              requestId,
              'request',
              'Request failed',
              'failed',
              message
            );

            if (!assistantIdRef.current) {
              assistantIdRef.current =
                appendAssistant(
                  `AI request gagal: ${message}`
                );
            }

            finish(
              requestId,
              terminalPhase,
              message
            );
          }
        }
      } finally {
        if (deltaTimerRef.current) {
          clearTimeout(
            deltaTimerRef.current
          );

          deltaTimerRef.current = null;
        }

        if (
          controllerRef.current === controller
        ) {
          controllerRef.current = null;
        }

        timeoutReasonRef.current = null;

        setIsSending(false);
      }
    }, [
      addActivity,
      appendAssistant,
      attachments,
      draft,
      finish,
      flushDelta,
      isCurrent,
      isSending,
      markBackendActivity,
      reset,
      setPhase,
      start
    ]);

  submitRef.current = handleSubmit;

  const handleInputSubmit = useCallback(() => {
    void submitRef.current();
  }, []);

  const handlePaste = useCallback(
    (block: string) => {
      setAttachments((current) => [
        ...current,
        block
      ]);
    },
    []
  );

  const handleRemoveLastAttachment =
    useCallback(() => {
      setAttachments((current) =>
        current.slice(0, -1)
      );
    }, []);

  useEffect(() => {
    if (
      !isSending ||
      !run ||
      isTerminalRun(run)
    ) {
      return;
    }

    const interval = setInterval(() => {
      if (!controllerRef.current) {
        return;
      }

      const now = performance.now();

      const phaseTimeout =
        timeoutForRun(run);

      const phaseElapsed =
        now - run.startedAt;

      const inactivityElapsed =
        now - lastEventAtRef.current;

      if (
        inactivityElapsed >=
        cliConfig.inactivityTimeoutMs
      ) {
        timeoutReasonRef.current =
          `No backend activity for ${Math.round(
            inactivityElapsed / 1000
          )} seconds`;

        controllerRef.current.abort();

        return;
      }

      if (phaseElapsed >= phaseTimeout) {
        timeoutReasonRef.current =
          `${run.phase} exceeded ${Math.round(
            phaseTimeout / 1000
          )} seconds`;

        controllerRef.current.abort();
      }
    }, 500);

    return () => {
      clearInterval(interval);
    };
  }, [
    isSending,
    run
  ]);

  useEffect(() => {
    if (
      !run ||
      !isTerminalRun(run)
    ) {
      return;
    }

    const messageId =
      assistantIdRef.current;

    if (!messageId) {
      return;
    }

    setRunSnapshots((current) => {
      const existing = current[messageId];

      if (
        existing &&
        existing.phase === run.phase &&
        existing.finishedAt === run.finishedAt
      ) {
        return current;
      }

      return {
        ...current,
        [messageId]: cloneRun(run)
      };
    });
  }, [run]);

  useEffect(() => {
    return () => {
      controllerRef.current?.abort();

      if (deltaTimerRef.current) {
        clearTimeout(
          deltaTimerRef.current
        );
      }
    };
  }, []);

  useInput((input, key) => {
    if (key.escape) {
      if (isSending) {
        cancelActiveRequest();
      } else {
        exit();
      }

      return;
    }

    if (
      key.ctrl &&
      input === 'c'
    ) {
      if (isSending) {
        cancelActiveRequest();
      } else {
        exit();
      }

      return;
    }

    if (
      key.ctrl &&
      input === 't'
    ) {
      setActivityExpanded(
        (current) => !current
      );

      return;
    }

    if (
      key.tab &&
      !isSending
    ) {
      appendAssistant(
        'Gunakan /commands untuk melihat command Xninetzy atau /tools untuk melihat tool MCP.'
      );

      return;
    }

    if (
      key.ctrl &&
      input === 'p' &&
      !isSending
    ) {
      appendAssistant(
        'Konfigurasi: xninetzy config list|get|set|unset|validate.'
      );
    }
  });

  if (!hasConversation) {
    return (
      <WelcomeScreen
        columns={columns}
        rows={rows}
      >
        <InputBox
          draft={draft}
          attachments={attachments}
          onDraftChange={setDraft}
          onPaste={handlePaste}
          onRemoveLastAttachment={
            handleRemoveLastAttachment
          }
          onSubmit={handleInputSubmit}
          width={welcomeInputWidth}
          isSending={isSending}
          variant="welcome"
        />
      </WelcomeScreen>
    );
  }

  return (
    <FullScreenShell
      columns={columns}
      rows={rows}
      height={layout.screenHeight}
    >
      <Box
        width={contentWidth}
        height={layout.headerHeight}
        minHeight={layout.headerHeight}
        flexShrink={0}
        overflow="hidden"
      >
        <Header
          width={contentWidth}
          isSending={isSending}
        />
      </Box>

      <MessageViewport
        messages={
          activeMessage
            ? [...settledMessages, activeMessage]
            : settledMessages
        }
        width={contentWidth}
        height={layout.messageHeight}
        runSnapshots={runSnapshots}
      />

      {run && !isTerminalRun(run) && (
        <Box
          width={contentWidth}
          height={layout.activityHeight}
          minHeight={layout.activityHeight}
          flexShrink={0}
          overflow="hidden"
        >
          <ThinkingPanel
            run={run}
            expanded={activityExpanded}
          />
        </Box>
      )}

      <Box
        width={contentWidth}
        height={layout.composerHeight}
        minHeight={layout.composerHeight}
        flexShrink={0}
        overflow="hidden"
        paddingX={1}
      >
        <InputBox
          draft={draft}
          attachments={attachments}
          onDraftChange={setDraft}
          onPaste={handlePaste}
          onRemoveLastAttachment={
            handleRemoveLastAttachment
          }
          onSubmit={handleInputSubmit}
          width={Math.max(
            38,
            contentWidth - 2
          )}
          isSending={isSending}
          variant="session"
        />
      </Box>

      <Box
        width={contentWidth}
        height={layout.footerHeight}
        minHeight={layout.footerHeight}
        flexShrink={0}
        overflow="hidden"
      >
        <StatusBar
          width={contentWidth}
          aiUrl={cliConfig.aiUrl}
        />
      </Box>
    </FullScreenShell>
  );

}
