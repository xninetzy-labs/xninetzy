import React, { memo } from 'react';
import { Box } from 'ink';

import type { ChatMessage } from '../types.js';
import type { ChatRun } from '../types/chat-run.js';
import { ChatView } from './ChatView.js';

type MessageViewportProps = {
  messages: ChatMessage[];
  width: number;
  height: number;
  runSnapshots?: Record<string, ChatRun>;
};

function MessageViewportComponent({
  messages,
  width,
  height,
  runSnapshots
}: MessageViewportProps) {
  const maxLines = Math.max(1, height - 1);

  return (
    <Box
      width={width}
      height={height}
      minHeight={Math.min(6, height)}
      flexGrow={1}
      flexShrink={1}
      flexDirection="column"
      justifyContent="flex-end"
      overflow="hidden"
      paddingBottom={1}
    >
      <ChatView
        messages={messages}
        width={width}
        runSnapshots={runSnapshots}
        maxLines={maxLines}
      />
    </Box>
  );
}

export const MessageViewport = memo(
  MessageViewportComponent
);
