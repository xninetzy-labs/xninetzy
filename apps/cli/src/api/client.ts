import { cliConfig } from '../config/env.js';

type ChatResponse = {
  reply: string;
};

export type ChatStreamEvent =
  | { type: 'status'; label: string }
  | { type: 'tool'; label: string }
  | { type: 'delta'; delta: string }
  | { type: 'response'; reply: string }
  | { type: 'done' };

function buildMessage(message: string, attachments: string[]): string {
  const parts: string[] = [];
  if (message.trim()) parts.push(message.trim());
  attachments.forEach((block, index) => {
    parts.push(`[Pasted block ${index + 1}]\n${block}`);
  });
  return parts.join('\n\n') || 'Tolong analisis konten yang saya kirim.';
}

function requestBody(message: string, attachments: string[], realtime = false): string {
  return JSON.stringify({
    chat_id: cliConfig.chatId,
    sender_id: cliConfig.senderId,
    sender_name: cliConfig.senderName,
    message: buildMessage(message, attachments),
    chat_type: 'private',
    metadata: {
      client: 'cli',
      realtime,
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
    let parsed: ChatResponse;
    try {
      parsed = JSON.parse(body) as ChatResponse;
    } catch {
      throw new Error('AI API mengembalikan JSON yang tidak valid');
    }
    if (typeof parsed.reply !== 'string' || !parsed.reply.trim()) {
      throw new Error('AI API mengembalikan reply kosong');
    }
    return parsed.reply;
  } catch (error) {
    if (error instanceof Error && error.name === 'AbortError') {
      throw new Error(`AI request timeout setelah ${cliConfig.requestTimeoutMs}ms`);
    }
    throw error;
  } finally {
    clearTimeout(timeout);
  }
}

export async function streamChat(
  message: string,
  onEvent: (event: ChatStreamEvent) => void,
  attachments: string[] = []
): Promise<void> {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), cliConfig.requestTimeoutMs);
  try {
    const response = await fetch(`${cliConfig.aiUrl.replace(/\/$/, '')}/api/chat/stream`, {
      method: 'POST',
      headers: requestHeaders(true),
      body: requestBody(message, attachments, true),
      signal: controller.signal
    });
    if (!response.ok || !response.body) throw new Error(`AI stream ${response.status}`);
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';
    while (true) {
      const chunk = await reader.read();
      if (chunk.done) break;
      buffer += decoder.decode(chunk.value, { stream: true });
      const blocks = buffer.split('\n\n');
      buffer = blocks.pop() ?? '';
      for (const block of blocks) {
        const type = /^event: (.+)$/m.exec(block)?.[1];
        const raw = /^data: (.+)$/m.exec(block)?.[1] ?? '{}';
        let payload: { label?: string; reply?: string; delta?: string };
        try {
          payload = JSON.parse(raw) as { label?: string; reply?: string; delta?: string };
        } catch {
          continue;
        }
        if (type === 'status' && payload.label) onEvent({ type, label: payload.label });
        if (type === 'tool' && payload.label) onEvent({ type, label: payload.label });
        if (type === 'delta' && payload.delta) onEvent({ type, delta: payload.delta });
        if (type === 'response' && payload.reply) onEvent({ type, reply: payload.reply });
        if (type === 'done') onEvent({ type });
      }
    }
  } catch (error) {
    if (error instanceof Error && error.name === 'AbortError') {
      throw new Error(`AI stream timeout setelah ${cliConfig.requestTimeoutMs}ms`);
    }
    if (error instanceof TypeError || (error instanceof Error && error.message === 'fetch failed')) {
      const reply = await sendChat(message, attachments);
      onEvent({ type: 'status', label: 'Fallback JSON response' });
      onEvent({ type: 'response', reply });
      onEvent({ type: 'done' });
      return;
    }
    throw error;
  } finally {
    clearTimeout(timeout);
  }
}
