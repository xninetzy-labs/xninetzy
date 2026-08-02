import React, { memo, useMemo } from 'react';
import { Box, Text } from 'ink';

import type { ChatMessage } from '../types.js';
import type { ChatRun } from '../types/chat-run.js';
import type {
  ChatInlineSpan,
  ChatRenderRow,
  ChatRowTone
} from '../rendering/chat-markdown.js';
import {
  buildChatRows,
  selectViewportRows
} from '../rendering/chat-markdown.js';
import { colors } from '../theme/colors.js';

type ChatViewProps = {
  messages: ChatMessage[];
  width: number;
  maxLines: number;
  runSnapshots?: Record<string, ChatRun>;
};

function toneColor(tone: ChatRowTone | undefined): string {
  switch (tone) {
    case 'secondary':
      return colors.textSecondary;
    case 'muted':
      return colors.muted;
    case 'accent':
      return colors.cyanBright;
    case 'user':
      return colors.orangeBright;
    case 'code':
      return colors.textSecondary;
    case 'success':
      return colors.green;
    case 'warning':
      return colors.yellow;
    case 'danger':
      return colors.red;
    default:
      return colors.textPrimary;
  }
}

function InlineSpan({
  span,
  fallbackColor
}: {
  span: ChatInlineSpan;
  fallbackColor: string;
}) {
  switch (span.style) {
    case 'strong':
      return <Text bold color={colors.white}>{span.text}</Text>;
    case 'emphasis':
      return <Text italic color={colors.textSecondary}>{span.text}</Text>;
    case 'code':
      return <Text color={colors.cyanBright}>{span.text}</Text>;
    case 'link':
      return <Text underline color={colors.cyanBright}>{span.text}</Text>;
    case 'citation':
      return <Text bold color={colors.blueBright}>{span.text}</Text>;
    case 'strike':
      return <Text strikethrough color={colors.muted}>{span.text}</Text>;
    default:
      return <Text color={fallbackColor}>{span.text}</Text>;
  }
}

function RenderRow({ row }: { row: ChatRenderRow }) {
  const color = toneColor(row.tone);
  const userMessage = row.role === 'user';
  const railColor = userMessage
    ? colors.orange
    : colors.borderBright;

  return (
    <Box
      width={row.panelWidth}
      alignSelf={userMessage ? 'flex-end' : 'flex-start'}
      flexDirection="row"
    >
      {row.kind === 'blank' ? (
        <Text> </Text>
      ) : (
        <>
          {row.rail ? <Text color={railColor}>┃{' '}</Text> : null}
          <Text color={color} bold={row.bold} wrap="truncate">
            {row.prefix ? <Text color={color}>{row.prefix}</Text> : null}
            {row.spans.map((span, index) => (
              <InlineSpan
                key={`${row.key}:span:${index}`}
                span={span}
                fallbackColor={color}
              />
            ))}
          </Text>
        </>
      )}
    </Box>
  );
}

function ChatViewComponent({
  messages,
  width,
  maxLines,
  runSnapshots = {}
}: ChatViewProps) {
  const rows = useMemo(
    () => buildChatRows(
      messages,
      Math.max(24, width - 2),
      runSnapshots
    ),
    [messages, runSnapshots, width]
  );
  const visibleRows = useMemo(
    () => selectViewportRows(rows, maxLines),
    [maxLines, rows]
  );

  if (visibleRows.length === 0) {
    return null;
  }

  return (
    <Box width={width} flexDirection="column" paddingX={1}>
      {visibleRows.map((row) => (
        <RenderRow key={row.key} row={row} />
      ))}
    </Box>
  );
}

export const ChatView = memo(ChatViewComponent);
