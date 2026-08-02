import { cliConfig } from '../config/env.js';

type ChatResponse = {
  reply: string;
};

export type ChatStreamEvent =
  | { type: 'run_started'; requestId: string }
  | { type: 'phase'; label: string; status?: 'active' | 'completed' | 'failed'; detail?: string }
  | { type: 'activity' | 'tool' | 'agent' | 'source'; label: string; status?: 'active' | 'completed' | 'failed'; detail?: string }
  | { type: 'delta'; delta: string }
  | { type: 'response'; reply: string }
  | { type: 'done' };

export type StreamChatOptions = {
  requestId: string;
  signal?: AbortSignal;
};

type StreamPayload = {
  requestId?: string;
  label?: string;
  reply?: string;
  delta?: string;
  status?: 'active' | 'completed' | 'failed';
  detail?: string;
};

function buildMessage(message: string, attachments: string[]): string {
  const parts: string[] = [];
  if (message.trim()) parts.push(message.trim());
  attachments.forEach((block, index) => {
    parts.push(`[Pasted block ${index + 1}]\n${block}`);
  });
  return parts.join('\n\n') || 'Tolong analisis konten yang saya kirim.';
}

function requestBody(message: string, attachments: string[], realtime = false, requestId?: string): string {
  return JSON.stringify({
    chat_id: cliConfig.chatId,
    sender_id: cliConfig.senderId,
    sender_name: cliConfig.senderName,
    message: buildMessage(message, attachments),
    chat_type: 'private',
    metadata: {
      client: 'cli',
      realtime,
      ...(requestId ? { clientRequestId: requestId } : {}),
      pastedBlockCount: attachments.length
    }
  });
}

function requestHeaders(stream = false): Record<string, string> {
  return {
    'content-type': 'application/json',
    ...(stream ? { accept: 'text/event-stream' } : {}),
    ...(cliConfig.aiApiKey ? { authorization: `Bearer ${cliConfig.aiApiKey}` } : {})
  };
}

function timeoutError(): Error {
  return new Error(`AI request timeout setelah ${cliConfig.requestTimeoutMs}ms`);
}

export async function sendChat(message: string, attachments: string[] = []): Promise<string> {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), cliConfig.requestTimeoutMs);
  try {
    const response = await fetch(`${cliConfig.aiUrl.replace(/\/$/, '')}/api/chat`, {
      method: 'POST',
      headers: requestHeaders(),
      body: requestBody(message, attachments),
      signal: controller.signal
    });
    const body = await response.text();
    if (!response.ok) throw new Error(`AI API ${response.status}: ${body.slice(0, 240)}`);
    const parsed = JSON.parse(body) as ChatResponse;
    if (typeof parsed.reply !== 'string' || !parsed.reply.trim()) {
      throw new Error('AI API mengembalikan reply kosong');
    }
    return parsed.reply;
  } catch (error) {
    if (error instanceof Error && error.name === 'AbortError') throw timeoutError();
    throw error;
  } finally {
    clearTimeout(timeout);
  }
}

export async function streamChat(
  message: string,
  onEvent: (event: ChatStreamEvent) => void,
  attachments: string[] = [],
  options: StreamChatOptions
): Promise<void> {
  const controller = new AbortController();
  let timeoutReason: string | null = null;
  let inactivityTimer: ReturnType<typeof setTimeout> | null = null;
  let thinkTimer: ReturnType<typeof setTimeout> | null = null;
  let totalTimer: ReturnType<typeof setTimeout> | null = null;
  let deepResearch = false;
  const abortFromCaller = () => controller.abort();
  const abortFor = (reason: string) => {
    timeoutReason = reason;
    controller.abort();
  };
  const resetInactivity = () => {
    if (inactivityTimer) clearTimeout(inactivityTimer);
    inactivityTimer = setTimeout(
      () => abortFor('AI stream inactivity timeout'),
      cliConfig.inactivityTimeoutMs
    );
  };

  options.signal?.addEventListener('abort', abortFromCaller, { once: true });
  thinkTimer = setTimeout(
    () => abortFor('AI thinking timeout sebelum token pertama'),
    cliConfig.thinkTimeoutMs
  );
  totalTimer = setTimeout(
    () => abortFor('AI stream total timeout'),
    cliConfig.streamTimeoutMs
  );
  resetInactivity();

  try {
    const response = await fetch(`${cliConfig.aiUrl.replace(/\/$/, '')}/api/chat/stream`, {
      method: 'POST',
      headers: requestHeaders(true),
      body: requestBody(message, attachments, true, options.requestId),
      signal: controller.signal
    });
    if (!response.ok || !response.body) throw new Error(`AI stream ${response.status}`);

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    while (true) {
      const chunk = await reader.read();
      if (chunk.done) break;
      resetInactivity();
      buffer += decoder.decode(chunk.value, { stream: true });
      const blocks = buffer.replace(/\r\n/g, '\n').split('\n\n');
      buffer = blocks.pop() ?? '';

      for (const block of blocks) {
        const type = /^event: (.+)$/m.exec(block)?.[1];
        const raw = /^data: (.+)$/m.exec(block)?.[1] ?? '{}';
        let payload: StreamPayload;
        try {
          payload = JSON.parse(raw) as StreamPayload;
        } catch {
          continue;
        }
        if (!deepResearch && payload.label?.toLowerCase().includes("research")) {
          deepResearch = true;
          if (thinkTimer) clearTimeout(thinkTimer);
          if (totalTimer) clearTimeout(totalTimer);
          thinkTimer = null;
          totalTimer = setTimeout(
            () => abortFor("Deep research timeout"),
            cliConfig.deepResearchTimeoutMs
          );
        }
        if (type === 'run_started' && payload.requestId) onEvent({ type, requestId: payload.requestId });
        if ((type === 'phase' || type === 'status') && payload.label) {
          onEvent({ type: 'phase', label: payload.label, status: payload.status, detail: payload.detail });
        }
        if ((type === 'activity' || type === 'tool' || type === 'agent' || type === 'source') && payload.label) {
          onEvent({ type, label: payload.label, status: payload.status, detail: payload.detail });
        }
        if (type === 'delta' && payload.delta) {
          if (thinkTimer) clearTimeout(thinkTimer);
          thinkTimer = null;
          onEvent({ type, delta: payload.delta });
        }
        if (type === 'response' && payload.reply) {
          if (thinkTimer) clearTimeout(thinkTimer);
          thinkTimer = null;
          onEvent({ type, reply: payload.reply });
        }
        if (type === 'done') onEvent({ type });
      }
    }
  } catch (error) {
    if (error instanceof Error && error.name === 'AbortError') {
      if (options.signal?.aborted) throw new Error('AI stream dibatalkan');
      throw new Error(timeoutReason ?? 'AI stream dibatalkan');
    }
    throw error;
  } finally {
    if (thinkTimer) clearTimeout(thinkTimer);
    if (totalTimer) clearTimeout(totalTimer);
    if (inactivityTimer) clearTimeout(inactivityTimer);
    options.signal?.removeEventListener('abort', abortFromCaller);
  }
}
