export function getMockReply(input: string): string {
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
