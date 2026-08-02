import stringWidth from 'string-width';
import wrapAnsi from 'wrap-ansi';

import type { ChatMessage } from '../types.js';
import type { ChatRun, ChatRunActivity } from '../types/chat-run.js';

export type ChatRowTone =
  | 'primary'
  | 'secondary'
  | 'muted'
  | 'accent'
  | 'user'
  | 'code'
  | 'success'
  | 'warning'
  | 'danger';

export type InlineStyle =
  | 'plain'
  | 'strong'
  | 'emphasis'
  | 'code'
  | 'link'
  | 'citation'
  | 'strike';

export type ChatInlineSpan = {
  text: string;
  style: InlineStyle;
};

export type ChatRenderRow = {
  key: string;
  messageId: string;
  role: ChatMessage['role'];
  kind: 'blank' | 'header' | 'body' | 'heading' | 'code' | 'meta' | 'rule';
  spans: ChatInlineSpan[];
  panelWidth: number;
  prefix?: string;
  rail?: boolean;
  tone?: ChatRowTone;
  bold?: boolean;
};

type InlinePattern = {
  style: InlineStyle;
  expression: RegExp;
  content: (match: RegExpExecArray) => string;
};

const inlinePatterns: InlinePattern[] = [
  {
    style: 'code',
    expression: /`([^`\n]+)`/,
    content: (match) => match[1] ?? ''
  },
  {
    style: 'strong',
    expression: /\*\*([^*\n]+)\*\*/,
    content: (match) => match[1] ?? ''
  },
  {
    style: 'strike',
    expression: /~~([^~\n]+)~~/,
    content: (match) => match[1] ?? ''
  },
  {
    style: 'link',
    expression: /\[([^\]\n]+)\]\(([^)\s]+)\)/,
    content: (match) => `${match[1] ?? ''} ↗`
  },
  {
    style: 'citation',
    expression: /\[(?:K\d+|\d+)\]/,
    content: (match) => match[0]
  },
  {
    style: 'emphasis',
    expression: /\*([^*\n]+)\*/,
    content: (match) => match[1] ?? ''
  },
  {
    style: 'emphasis',
    expression: /_([^_\n]+)_/,
    content: (match) => match[1] ?? ''
  }
];

function appendSpan(
  spans: ChatInlineSpan[],
  text: string,
  style: InlineStyle
): void {
  if (!text) {
    return;
  }

  const previous = spans.at(-1);

  if (previous?.style === style) {
    previous.text += text;
    return;
  }

  spans.push({ text, style });
}

export function parseInlineMarkdown(text: string): ChatInlineSpan[] {
  const spans: ChatInlineSpan[] = [];
  let remaining = text;

  while (remaining) {
    let selected:
      | { pattern: InlinePattern; match: RegExpExecArray }
      | undefined;

    for (const pattern of inlinePatterns) {
      const match = pattern.expression.exec(remaining);

      if (!match) {
        continue;
      }

      if (!selected || match.index < selected.match.index) {
        selected = { pattern, match };
      }
    }

    if (!selected) {
      appendSpan(spans, remaining, 'plain');
      break;
    }

    if (selected.match.index > 0) {
      appendSpan(
        spans,
        remaining.slice(0, selected.match.index),
        'plain'
      );
    }

    appendSpan(
      spans,
      selected.pattern.content(selected.match),
      selected.pattern.style
    );

    remaining = remaining.slice(
      selected.match.index + selected.match[0].length
    );
  }

  return spans.length > 0
    ? spans
    : [{ text: '', style: 'plain' }];
}

function splitByWidth(text: string, maximumWidth: number): string[] {
  if (!text) {
    return [''];
  }

  const safeWidth = Math.max(1, maximumWidth);
  const chunks: string[] = [];
  let current = '';
  let currentWidth = 0;

  for (const character of Array.from(text)) {
    const characterWidth = Math.max(0, stringWidth(character));

    if (current && currentWidth + characterWidth > safeWidth) {
      chunks.push(current);
      current = '';
      currentWidth = 0;
    }

    current += character;
    currentWidth += characterWidth;
  }

  if (current || chunks.length === 0) {
    chunks.push(current);
  }

  return chunks;
}

function wrapInlineSpans(
  spans: ChatInlineSpan[],
  maximumWidth: number
): ChatInlineSpan[][] {
  const safeWidth = Math.max(1, maximumWidth);
  const lines: ChatInlineSpan[][] = [[]];
  let lineWidth = 0;

  const startLine = (): void => {
    if (lines.at(-1)?.length === 0) {
      return;
    }

    lines.push([]);
    lineWidth = 0;
  };

  for (const span of spans) {
    const pieces = span.text.match(/\s+|\S+/g) ?? [''];

    for (const piece of pieces) {
      const whitespace = /^\s+$/.test(piece);

      if (whitespace) {
        if (lineWidth > 0 && lineWidth < safeWidth) {
          appendSpan(lines.at(-1) ?? [], ' ', span.style);
          lineWidth += 1;
        }

        continue;
      }

      const pieceWidth = stringWidth(piece);

      if (lineWidth > 0 && lineWidth + pieceWidth > safeWidth) {
        startLine();
      }

      if (pieceWidth <= safeWidth) {
        appendSpan(lines.at(-1) ?? [], piece, span.style);
        lineWidth += pieceWidth;
        continue;
      }

      const chunks = splitByWidth(piece, safeWidth);

      chunks.forEach((chunk, index) => {
        if (index > 0) {
          startLine();
        }

        appendSpan(lines.at(-1) ?? [], chunk, span.style);
        lineWidth += stringWidth(chunk);
      });
    }
  }

  return lines.map((line) =>
    line.length > 0
      ? line
      : [{ text: '', style: 'plain' }]
  );
}

function wrapTextRows({
  key,
  messageId,
  role,
  text,
  width,
  panelWidth,
  prefix = '',
  continuationPrefix,
  kind = 'body',
  tone = 'primary',
  rail = true,
  bold = false
}: {
  key: string;
  messageId: string;
  role: ChatMessage['role'];
  text: string;
  width: number;
  panelWidth: number;
  prefix?: string;
  continuationPrefix?: string;
  kind?: ChatRenderRow['kind'];
  tone?: ChatRowTone;
  rail?: boolean;
  bold?: boolean;
}): ChatRenderRow[] {
  const continuation = continuationPrefix ?? ' '.repeat(stringWidth(prefix));
  const availableWidth = Math.max(1, width - stringWidth(prefix));
  const lines = wrapInlineSpans(
    parseInlineMarkdown(text),
    availableWidth
  );

  return lines.map((spans, index) => ({
    key: `${key}:${index}`,
    messageId,
    role,
    kind,
    spans,
    panelWidth,
    prefix: index === 0 ? prefix : continuation,
    rail,
    tone,
    bold
  }));
}

function splitTableCells(line: string): string[] {
  return line
    .trim()
    .replace(/^\|/, '')
    .replace(/\|$/, '')
    .split('|')
    .map((cell) => cell.trim());
}

function isTableDivider(line: string): boolean {
  const cells = splitTableCells(line);

  return cells.length > 0 && cells.every((cell) => /^:?-{3,}:?$/.test(cell));
}

function isTableStart(lines: string[], index: number): boolean {
  return Boolean(
    lines[index]?.includes('|') &&
      lines[index + 1] &&
      isTableDivider(lines[index + 1] ?? '')
  );
}

function fitCell(text: string, width: number): string {
  const safeWidth = Math.max(1, width);

  if (stringWidth(text) <= safeWidth) {
    return text + ' '.repeat(safeWidth - stringWidth(text));
  }

  const chunks = splitByWidth(text, Math.max(1, safeWidth - 1));
  const head = chunks[0] ?? '';
  const fitted = `${head}…`;

  return fitted + ' '.repeat(Math.max(0, safeWidth - stringWidth(fitted)));
}

function formatWideTableRow(cells: string[], width: number): string {
  const separatorWidth = Math.max(0, cells.length - 1) * 3;
  const cellWidth = Math.max(
    4,
    Math.floor((width - separatorWidth) / Math.max(1, cells.length))
  );

  return cells
    .map((cell) => fitCell(cell, cellWidth))
    .join(' │ ')
    .trimEnd();
}

function isStructuralLine(lines: string[], index: number): boolean {
  const line = lines[index] ?? '';

  return (
    /^\s*```/.test(line) ||
    /^\s{0,3}#{1,6}\s+/.test(line) ||
    /^\s*[-+*]\s+/.test(line) ||
    /^\s*\d+[.)]\s+/.test(line) ||
    /^\s*>/.test(line) ||
    /^\s{0,3}((\*\s*){3,}|(-\s*){3,}|(_\s*){3,})$/.test(line) ||
    isTableStart(lines, index)
  );
}

function parseMarkdownRows({
  content,
  messageId,
  role,
  width,
  panelWidth
}: {
  content: string;
  messageId: string;
  role: ChatMessage['role'];
  width: number;
  panelWidth: number;
}): ChatRenderRow[] {
  const normalized = content.replace(/\r\n?/g, '\n');
  const lines = normalized.split('\n');
  const rows: ChatRenderRow[] = [];
  let index = 0;

  const addBlank = (key: string): void => {
    if (rows.at(-1)?.kind === 'blank') {
      return;
    }

    rows.push({
      key,
      messageId,
      role,
      kind: 'blank',
      spans: [{ text: ' ', style: 'plain' }],
      panelWidth,
      rail: false
    });
  };

  while (index < lines.length) {
    const rawLine = lines[index] ?? '';

    if (!rawLine.trim()) {
      addBlank(`${messageId}:blank:${index}`);
      index += 1;
      continue;
    }

    const fence = rawLine.match(/^\s*```\s*([^`]*)$/);

    if (fence) {
      const language = fence[1]?.trim() || 'code';
      const startIndex = index;
      const codeLines: string[] = [];
      let closed = false;
      index += 1;

      while (index < lines.length) {
        const candidate = lines[index] ?? '';

        if (/^\s*```\s*$/.test(candidate)) {
          closed = true;
          index += 1;
          break;
        }

        codeLines.push(candidate);
        index += 1;
      }

      rows.push({
        key: `${messageId}:code-header:${startIndex}`,
        messageId,
        role,
        kind: 'meta',
        spans: [
          {
            text: `${language} · ${closed ? `${codeLines.length} lines` : 'generating'}`,
            style: 'plain'
          }
        ],
        panelWidth,
        prefix: '┌─ ',
        rail: true,
        tone: closed ? 'muted' : 'warning'
      });

      const lineNumberWidth = Math.max(2, String(Math.max(1, codeLines.length)).length);
      const codeWidth = Math.max(8, width - lineNumberWidth - 3);
      const visibleCodeLines = codeLines.length > 0 ? codeLines : [''];

      visibleCodeLines.forEach((codeLine, lineIndex) => {
        const wrapped = wrapAnsi(codeLine || ' ', codeWidth, {
          hard: true,
          trim: false,
          wordWrap: false
        }).split('\n');

        wrapped.forEach((chunk, chunkIndex) => {
          rows.push({
            key: `${messageId}:code:${startIndex}:${lineIndex}:${chunkIndex}`,
            messageId,
            role,
            kind: 'code',
            spans: [{ text: chunk || ' ', style: 'plain' }],
            panelWidth,
            prefix:
              chunkIndex === 0
                ? `${String(lineIndex + 1).padStart(lineNumberWidth, ' ')} │ `
                : `${' '.repeat(lineNumberWidth)} │ `,
            rail: true,
            tone: 'code'
          });
        });
      });

      if (!closed) {
        rows.push({
          key: `${messageId}:code-open:${startIndex}`,
          messageId,
          role,
          kind: 'meta',
          spans: [{ text: 'waiting for closing fence…', style: 'plain' }],
          panelWidth,
          prefix: '   ',
          rail: true,
          tone: 'muted'
        });
      }

      continue;
    }

    if (isTableStart(lines, index)) {
      const startIndex = index;
      const header = splitTableCells(rawLine);
      const tableRows: string[][] = [];
      index += 2;

      while (index < lines.length && (lines[index] ?? '').includes('|')) {
        tableRows.push(splitTableCells(lines[index] ?? ''));
        index += 1;
      }

      if (width >= 54 && header.length <= 4) {
        rows.push(...wrapTextRows({
          key: `${messageId}:table-header:${startIndex}`,
          messageId,
          role,
          text: formatWideTableRow(header, width),
          width,
          panelWidth,
          kind: 'heading',
          tone: 'secondary',
          bold: true
        }));

        tableRows.forEach((cells, rowIndex) => {
          rows.push(...wrapTextRows({
            key: `${messageId}:table:${startIndex}:${rowIndex}`,
            messageId,
            role,
            text: formatWideTableRow(cells, width),
            width,
            panelWidth,
            tone: 'secondary'
          }));
        });
      } else {
        tableRows.forEach((cells, rowIndex) => {
          const text = cells
            .map((cell, cellIndex) => `${header[cellIndex] ?? `Column ${cellIndex + 1}`}: ${cell}`)
            .join(' · ');

          rows.push(...wrapTextRows({
            key: `${messageId}:table:${startIndex}:${rowIndex}`,
            messageId,
            role,
            text,
            width,
            panelWidth,
            prefix: '• ',
            tone: 'secondary'
          }));
        });
      }

      continue;
    }

    const heading = rawLine.match(/^\s{0,3}(#{1,6})\s+(.+)$/);

    if (heading) {
      const level = heading[1]?.length ?? 1;
      rows.push(...wrapTextRows({
        key: `${messageId}:heading:${index}`,
        messageId,
        role,
        text: heading[2] ?? '',
        width,
        panelWidth,
        prefix: level <= 2 ? '◆ ' : '◇ ',
        kind: 'heading',
        tone: 'accent',
        bold: true
      }));
      index += 1;
      continue;
    }

    if (/^\s{0,3}((\*\s*){3,}|(-\s*){3,}|(_\s*){3,})$/.test(rawLine)) {
      rows.push({
        key: `${messageId}:rule:${index}`,
        messageId,
        role,
        kind: 'rule',
        spans: [{ text: '─'.repeat(Math.max(8, Math.min(width, 48))), style: 'plain' }],
        panelWidth,
        rail: true,
        tone: 'muted'
      });
      index += 1;
      continue;
    }

    const quote = rawLine.match(/^\s*>\s?(.*)$/);

    if (quote) {
      rows.push(...wrapTextRows({
        key: `${messageId}:quote:${index}`,
        messageId,
        role,
        text: quote[1] ?? '',
        width,
        panelWidth,
        prefix: '▎ ',
        tone: 'secondary'
      }));
      index += 1;
      continue;
    }

    const unordered = rawLine.match(/^(\s*)[-+*]\s+(?:\[([ xX])\]\s+)?(.+)$/);

    if (unordered) {
      const depth = Math.min(3, Math.floor((unordered[1]?.length ?? 0) / 2));
      const task = unordered[2];
      const marker = task
        ? task.toLowerCase() === 'x'
          ? '✓ '
          : '○ '
        : '• ';
      const prefix = `${'  '.repeat(depth)}${marker}`;

      rows.push(...wrapTextRows({
        key: `${messageId}:list:${index}`,
        messageId,
        role,
        text: unordered[3] ?? '',
        width,
        panelWidth,
        prefix,
        tone: task?.toLowerCase() === 'x' ? 'success' : 'primary'
      }));
      index += 1;
      continue;
    }

    const ordered = rawLine.match(/^(\s*)(\d+)[.)]\s+(.+)$/);

    if (ordered) {
      const depth = Math.min(3, Math.floor((ordered[1]?.length ?? 0) / 2));
      const prefix = `${'  '.repeat(depth)}${ordered[2]}. `;

      rows.push(...wrapTextRows({
        key: `${messageId}:ordered:${index}`,
        messageId,
        role,
        text: ordered[3] ?? '',
        width,
        panelWidth,
        prefix
      }));
      index += 1;
      continue;
    }

    const paragraphStart = index;
    const paragraphLines = [rawLine.trim()];
    index += 1;

    while (
      index < lines.length &&
      (lines[index] ?? '').trim() &&
      !isStructuralLine(lines, index)
    ) {
      paragraphLines.push((lines[index] ?? '').trim());
      index += 1;
    }

    rows.push(...wrapTextRows({
      key: `${messageId}:paragraph:${paragraphStart}`,
      messageId,
      role,
      text: paragraphLines.join(' '),
      width,
      panelWidth
    }));
  }

  while (rows.at(-1)?.kind === 'blank') {
    rows.pop();
  }

  return rows;
}

function activityIcon(activity: ChatRunActivity): string {
  if (activity.status === 'failed') {
    return '×';
  }

  if (activity.kind === 'source') {
    return '↗';
  }

  if (activity.kind === 'agent') {
    return '◇';
  }

  if (activity.kind === 'tool') {
    return '⚙';
  }

  return '✓';
}

function formatDuration(milliseconds: number): string {
  const seconds = Math.max(0, milliseconds) / 1000;

  if (seconds < 1) {
    return `${Math.round(milliseconds)}ms`;
  }

  if (seconds < 60) {
    return `${seconds.toFixed(1)}s`;
  }

  return `${Math.floor(seconds / 60)}m ${(seconds % 60).toFixed(1)}s`;
}

function buildRunRows(
  messageId: string,
  panelWidth: number,
  width: number,
  run: ChatRun
): ChatRenderRow[] {
  const finishedAt = run.finishedAt ?? run.firstTokenAt ?? run.startedAt;
  const thoughtEnd = run.firstTokenAt ?? finishedAt;
  const summary = [
    `Thought for ${formatDuration(thoughtEnd - run.startedAt)}`,
    `completed in ${formatDuration(finishedAt - run.startedAt)}`
  ];
  const toolCount = run.activity.filter((activity) => activity.kind === 'tool').length;
  const sourceCount = run.activity.filter((activity) => activity.kind === 'source').length;

  if (toolCount > 0) {
    summary.push(`${toolCount} ${toolCount === 1 ? 'tool' : 'tools'}`);
  }

  if (sourceCount > 0) {
    summary.push(`${sourceCount} ${sourceCount === 1 ? 'source' : 'sources'}`);
  }

  const rows = wrapTextRows({
    key: `${messageId}:run-summary`,
    messageId,
    role: 'assistant',
    text: summary.join(' · '),
    width,
    panelWidth,
    prefix: '└─ ',
    kind: 'meta',
    tone: run.phase === 'failed' ? 'danger' : run.phase === 'timed-out' ? 'warning' : 'muted',
    rail: false
  });

  const activities = run.activity
    .filter((activity) =>
      activity.kind === 'tool' ||
      activity.kind === 'agent' ||
      activity.kind === 'source'
    )
    .slice(-3);

  activities.forEach((activity, index) => {
    rows.push(...wrapTextRows({
      key: `${messageId}:run-activity:${activity.id}:${index}`,
      messageId,
      role: 'assistant',
      text: `${activity.kind} · ${activity.label}${activity.detail ? ` · ${activity.detail}` : ''}`,
      width,
      panelWidth,
      prefix: `${activityIcon(activity)} `,
      kind: 'meta',
      tone: activity.status === 'failed' ? 'danger' : 'muted',
      rail: false
    }));
  });

  return rows;
}

function messagePanelWidth(role: ChatMessage['role'], width: number): number {
  const available = Math.max(24, width - 2);

  return role === 'user'
    ? Math.min(72, available)
    : Math.min(104, available);
}

export function buildMessageRows(
  message: ChatMessage,
  width: number,
  run?: ChatRun
): ChatRenderRow[] {
  const panelWidth = messagePanelWidth(message.role, width);
  const bodyWidth = Math.max(12, panelWidth - 2);
  const headerText = message.role === 'user' ? 'You' : 'Xninetzy';
  const rows: ChatRenderRow[] = [
    {
      key: `${message.id}:header`,
      messageId: message.id,
      role: message.role,
      kind: 'header',
      spans: [{ text: headerText, style: 'strong' }],
      panelWidth,
      prefix: message.role === 'user' ? '› ' : '◎ ',
      rail: false,
      tone: message.role === 'user' ? 'user' : 'accent',
      bold: true
    }
  ];

  message.attachments?.forEach((attachment, index) => {
    const lineCount = attachment.replace(/\r\n?/g, '\n').split('\n').length;
    rows.push({
      key: `${message.id}:attachment:${index}`,
      messageId: message.id,
      role: message.role,
      kind: 'meta',
      spans: [{ text: `attachment ${index + 1} · ${lineCount} lines`, style: 'plain' }],
      panelWidth,
      prefix: '  ',
      rail: true,
      tone: 'muted'
    });
  });

  const bodyRows = parseMarkdownRows({
    content: message.content,
    messageId: message.id,
    role: message.role,
    width: bodyWidth,
    panelWidth
  });

  rows.push(...(
    bodyRows.length > 0
      ? bodyRows
      : [{
          key: `${message.id}:empty`,
          messageId: message.id,
          role: message.role,
          kind: 'body' as const,
          spans: [{ text: 'Waiting for response…', style: 'plain' as const }],
          panelWidth,
          rail: true,
          tone: 'muted' as const
        }]
  ));

  if (run && message.role === 'assistant') {
    rows.push(...buildRunRows(message.id, panelWidth, bodyWidth, run));
  }

  rows.push({
    key: `${message.id}:after`,
    messageId: message.id,
    role: message.role,
    kind: 'blank',
    spans: [{ text: ' ', style: 'plain' }],
    panelWidth,
    rail: false
  });

  return rows;
}

export function buildChatRows(
  messages: ChatMessage[],
  width: number,
  runSnapshots: Record<string, ChatRun> = {}
): ChatRenderRow[] {
  return messages
    .filter((message) => message.role !== 'system')
    .slice(-20)
    .flatMap((message) =>
      buildMessageRows(message, width, runSnapshots[message.id])
    );
}

export function selectViewportRows(
  rows: ChatRenderRow[],
  maximumLines: number
): ChatRenderRow[] {
  const safeMaximum = Math.max(1, maximumLines);
  const normalized = rows.slice();

  while (normalized.at(-1)?.kind === 'blank') {
    normalized.pop();
  }

  if (normalized.length <= safeMaximum) {
    return normalized;
  }

  const selected = normalized.slice(-safeMaximum);

  if (safeMaximum < 3) {
    return selected;
  }

  const hiddenCount = normalized.length - selected.length + 1;
  const first = selected[0];

  if (!first) {
    return selected;
  }

  return [
    {
      key: `viewport:hidden:${first.messageId}:${hiddenCount}`,
      messageId: first.messageId,
      role: first.role,
      kind: 'meta',
      spans: [{ text: `${hiddenCount} earlier lines hidden`, style: 'plain' }],
      panelWidth: first.panelWidth,
      prefix: '… ',
      rail: false,
      tone: 'muted'
    },
    ...selected.slice(1)
  ];
}
