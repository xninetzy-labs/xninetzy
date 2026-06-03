export type ChatRole = 'user' | 'assistant' | 'system';

export interface ChatMessage {
  id: string;
  role: ChatRole;
  content: string;
  /** Large pasted blocks shown collapsed as chips instead of dumped inline. */
  attachments?: string[];
  createdAt: Date;
}

/** Summarize a pasted block for a collapsed chip label, e.g. "1000 lines". */
export function describeBlock(block: string): string {
  const lines = block.split(/\r?\n/).length;
  if (lines > 1) {
    return `${lines.toLocaleString()} lines`;
  }
  return `${block.length.toLocaleString()} chars`;
}
