import React from 'react';
import { Box, Text } from 'ink';
import type { ChatMessage } from '../types.js';
import { describeBlock } from '../types.js';
import { colors } from '../theme/colors.js';

type ChatViewProps = {
  messages: ChatMessage[];
  width: number;
};

/** Inline markdown: **bold**, `code`, *italic* / _italic_. */
function InlineMarkdown({ text }: { text: string }) {
  const parts = text.split(/(\*\*.*?\*\*|`.*?`|\*.*?\*|_.*?_)/g);

  return (
    <>
      {parts.map((part, i) => {
        if (!part) return null;
        if (part.startsWith('**') && part.endsWith('**')) {
          return (
            <Text key={i} bold color={colors.white}>
              {part.slice(2, -2)}
            </Text>
          );
        }
        if (part.startsWith('`') && part.endsWith('`')) {
          return (
            <Text key={i} color={colors.orangeBright} backgroundColor={colors.backgroundSoft}>
              {' '}
              {part.slice(1, -1)}
              {' '}
            </Text>
          );
        }
        if (
          (part.startsWith('*') && part.endsWith('*')) ||
          (part.startsWith('_') && part.endsWith('_'))
        ) {
          return (
            <Text key={i} italic color={colors.lavender}>
              {part.slice(1, -1)}
            </Text>
          );
        }
        return <Text key={i}>{part}</Text>;
      })}
    </>
  );
}

/** A single non-code markdown line: headers, list bullets, inline styles. */
function MarkdownLine({ text }: { text: string }) {
  let lineText = text;
  let color: string = colors.text;
  let bold = false;
  let prefix = '';

  if (lineText.startsWith('### ')) {
    lineText = lineText.slice(4);
    color = colors.purpleBright;
    bold = true;
  } else if (lineText.startsWith('## ')) {
    lineText = lineText.slice(3);
    color = colors.purpleBright;
    bold = true;
  } else if (lineText.startsWith('# ')) {
    lineText = lineText.slice(2);
    color = colors.purpleBright;
    bold = true;
  }

  const trimmed = lineText.trim();
  if (trimmed.startsWith('- ') || trimmed.startsWith('* ')) {
    prefix = '  • ';
    lineText = trimmed.slice(2);
  }

  return (
    <Box flexDirection="row">
      {prefix && <Text color={colors.orange}>{prefix}</Text>}
      <Text color={color} bold={bold}>
        <InlineMarkdown text={lineText} />
      </Text>
    </Box>
  );
}

/** Fenced code block rendered as a soft-background panel. */
function CodeBlock({ lines, lang }: { lines: string[]; lang: string }) {
  return (
    <Box flexDirection="column" marginY={0} paddingX={1} borderStyle="round" borderColor={colors.borderDim}>
      {lang && (
        <Text color={colors.dim} italic>
          {lang}
        </Text>
      )}
      {lines.map((codeLine, i) => (
        <Text key={i} color={colors.orangeBright} backgroundColor={colors.backgroundSoft}>
          {codeLine || ' '}
        </Text>
      ))}
    </Box>
  );
}

type Block =
  | { kind: 'md'; text: string }
  | { kind: 'code'; lang: string; lines: string[] };

function parseBlocks(content: string): Block[] {
  const blocks: Block[] = [];
  let inCode = false;
  let codeLang = '';
  let codeLines: string[] = [];

  for (const raw of content.split('\n')) {
    if (raw.trim().startsWith('```')) {
      if (!inCode) {
        inCode = true;
        codeLang = raw.trim().slice(3).trim();
        codeLines = [];
      } else {
        blocks.push({ kind: 'code', lang: codeLang, lines: codeLines });
        inCode = false;
      }
      continue;
    }

    if (inCode) {
      codeLines.push(raw);
    } else {
      blocks.push({ kind: 'md', text: raw });
    }
  }

  if (inCode) {
    // Unclosed fence — still render what we captured.
    blocks.push({ kind: 'code', lang: codeLang, lines: codeLines });
  }

  return blocks;
}

function MessageBody({ content }: { content: string }) {
  const blocks = parseBlocks(content);
  return (
    <>
      {blocks.map((block, i) =>
        block.kind === 'code' ? (
          <CodeBlock key={i} lines={block.lines} lang={block.lang} />
        ) : (
          <MarkdownLine key={i} text={block.text} />
        )
      )}
    </>
  );
}

function AttachmentChips({ attachments }: { attachments: string[] }) {
  return (
    <Box flexDirection="column">
      {attachments.map((block, i) => (
        <Text key={i} color={colors.orangeBright}>
          ❏ pasted #{i + 1} · {describeBlock(block)}
        </Text>
      ))}
    </Box>
  );
}

export function ChatView({ messages, width }: ChatViewProps) {
  const visibleMessages = messages
    .filter((message) => message.role !== 'system')
    .slice(-10);

  if (visibleMessages.length === 0) {
    return (
      <Box width={width} flexDirection="column" paddingX={1}>
        <Text color={colors.dim}>
          Local mock session ready. No AI/API/backend calls.
        </Text>
      </Box>
    );
  }

  return (
    <Box width={width} flexDirection="column" paddingX={1}>
      {visibleMessages.map((message, index) => {
        const isUser = message.role === 'user';
        const label = isUser ? 'You' : '◎ Xninetzy';
        const labelColor = isUser ? colors.purpleBright : colors.orange;
        const alignment = isUser ? 'flex-end' : 'flex-start';
        const bubbleWidth = Math.floor(width * 0.78);
        const hasAttachments = (message.attachments?.length ?? 0) > 0;

        return (
          <Box
            key={message.id}
            flexDirection="column"
            alignItems={alignment}
            marginTop={index === 0 ? 0 : 1}
            width="100%"
          >
            <Box flexDirection="column" alignItems={alignment} width={bubbleWidth}>
              <Text bold color={labelColor}>
                {label}
              </Text>

              <Box
                flexDirection="column"
                paddingX={1}
                borderStyle="round"
                borderColor={isUser ? colors.border : colors.line}
              >
                {hasAttachments && <AttachmentChips attachments={message.attachments!} />}
                {message.content.length > 0 && <MessageBody content={message.content} />}
              </Box>
            </Box>
          </Box>
        );
      })}
    </Box>
  );
}
