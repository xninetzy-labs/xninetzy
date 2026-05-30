export function maskJid(jid?: string | null): string | undefined {
  if (!jid) return undefined;
  return jid.replace(/(\d{4})\d+(\d{3})/, "$1****$2");
}

export function maskPhone(phone?: string | null): string | undefined {
  if (!phone) return undefined;
  return phone.replace(/\D/g, "").replace(/(\d{4})\d+(\d{3})/, "$1****$2");
}

export function safePreview(text?: string | null): string | undefined {
  if (!text) return undefined;
  return text.slice(0, 80);
}

export function createTraceId(messageId?: string | null): string {
  return `wa_${messageId || Date.now()}_${Math.random().toString(36).slice(2, 8)}`;
}
