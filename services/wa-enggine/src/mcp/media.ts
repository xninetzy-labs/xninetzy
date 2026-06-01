export function sourceToMessageMedia(source: string): { url: string } | Buffer {
  const trimmed = source.trim();

  if (/^https?:\/\//i.test(trimmed) || /^file:\/\//i.test(trimmed)) {
    return { url: trimmed };
  }

  const base64 = trimmed.includes(",") ? trimmed.split(",").pop() ?? "" : trimmed;
  return Buffer.from(base64, "base64");
}

export function publicMessageResult(message: any): Record<string, unknown> {
  return {
    message_id: message?.key?.id ?? null,
    jid: message?.key?.remoteJid ?? null,
    from_me: message?.key?.fromMe ?? null,
    timestamp: message?.messageTimestamp ?? null,
  };
}
