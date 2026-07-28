import { cliConfig } from '../config/env.js';

type ChatResponse = {
  reply: string;
};

function buildMessage(message: string, attachments: string[]): string {
  const parts: string[] = [];
  if (message.trim()) parts.push(message.trim());
  attachments.forEach((block, index) => {
    parts.push(`[Pasted block ${index + 1}]\n${block}`);
  });
  return parts.join('\n\n') || 'Tolong analisis konten yang saya kirim.';
}

export async function sendChat(message: string, attachments: string[] = []): Promise<string> {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), cliConfig.requestTimeoutMs);

  try {
    const response = await fetch(`${cliConfig.aiUrl.replace(/\/$/, '')}/api/chat`, {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({
        chat_id: cliConfig.chatId,
        sender_id: cliConfig.senderId,
        sender_name: cliConfig.senderName,
        message: buildMessage(message, attachments),
        chat_type: 'private',
        metadata: {
          client: 'cli',
          pastedBlockCount: attachments.length
        }
      }),
      signal: controller.signal
    });

    const body = await response.text();
    if (!response.ok) {
      throw new Error(`AI API ${response.status}: ${body.slice(0, 240)}`);
    }

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
