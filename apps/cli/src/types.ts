export type ChatMessageRole =
  | 'system'
  | 'user'
  | 'assistant';

export type ChatMessage = {
  id: string;
  role: ChatMessageRole;
  content: string;
  attachments?: string[];
  createdAt: Date;
};

export function describeBlock(block: string): string {
  const normalized = block.replace(/\r\n?/g, '\n');
  const lineCount = normalized.split('\n').length;
  const characterCount = block.length;

  if (lineCount > 1) {
    return `${lineCount.toLocaleString()} lines`;
  }

  return `${characterCount.toLocaleString()} chars`;
}
