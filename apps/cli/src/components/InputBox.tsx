import React, { memo, useEffect, useState } from 'react';
import { Box, Text, useInput } from 'ink';
import { colors } from '../theme/colors.js';
import { describeBlock } from '../types.js';

type InputBoxProps = {
  draft: string;
  attachments: string[];
  onDraftChange: (value: string) => void;
  onPaste: (block: string) => void;
  onRemoveLastAttachment: () => void;
  onSubmit: () => void;
  width: number;
  isSending: boolean;
  variant?: 'welcome' | 'session';
};

const PASTE_MIN_CHARS = 64;

function isLargePaste(input: string): boolean {
  if (input.length <= 1) return false;
  const normalized = input.replace(/\r\n?/g, '\n');
  return normalized.includes('\n') || input.length >= PASTE_MIN_CHARS;
}

function InputBoxComponent({
  draft,
  attachments,
  onDraftChange,
  onPaste,
  onRemoveLastAttachment,
  onSubmit,
  width,
  isSending,
  variant = 'session'
}: InputBoxProps) {
  const [cursor, setCursor] = useState(draft.length);

  useEffect(() => {
    setCursor((current) => Math.min(current, draft.length));
  }, [draft]);

  const borderColor = attachments.length > 0
    ? colors.orange
    : variant === 'welcome'
      ? colors.borderBright
      : colors.border;

  useInput((input, key) => {
    if (key.tab || key.escape) return;

    if (key.return) {
      onSubmit();
      return;
    }

    if (key.leftArrow) {
      setCursor((current) => Math.max(0, current - 1));
      return;
    }

    if (key.rightArrow) {
      setCursor((current) => Math.min(draft.length, current + 1));
      return;
    }

    if (key.backspace || key.delete) {
      if (cursor > 0) {
        onDraftChange(draft.slice(0, cursor - 1) + draft.slice(cursor));
        setCursor((current) => Math.max(0, current - 1));
        return;
      }

      if (cursor === 0 && attachments.length > 0) onRemoveLastAttachment();
      return;
    }

    if (key.ctrl && input === 'u') {
      onDraftChange('');
      setCursor(0);
      return;
    }

    if (!input || key.ctrl || key.meta) return;

    if (isLargePaste(input)) {
      onPaste(input);
      return;
    }

    const printable = input.replace(/[\r\n]/g, '');
    if (!printable) return;

    onDraftChange(draft.slice(0, cursor) + printable + draft.slice(cursor));
    setCursor((current) => current + printable.length);
  });

  const hasContent = draft.length > 0 || attachments.length > 0;
  const placeholder = attachments.length > 0
    ? 'Add a message for this attachment…'
    : 'Ask Xninetzy anything…';

  return (
    <Box width={width} flexDirection="column" flexShrink={0}>
      <Box width="100%" flexDirection="column" borderStyle="round" borderColor={borderColor} paddingX={1}>
        {attachments.length > 0 && (
          <Box flexWrap="wrap" marginBottom={1}>
            {attachments.map((block, index) => (
              <Box key={String(index) + '-' + String(block.length)} marginRight={1}>
                <Text bold color={colors.black} backgroundColor={colors.orangeBright}>
                  {' '}❏ {describeBlock(block)}{' '}
                </Text>
              </Box>
            ))}
          </Box>
        )}

        <Box width="100%" flexDirection="row">
          <Text color={colors.cyanBright}>›{' '}</Text>
          <Box flexGrow={1}>
            <DraftLine
              draft={draft}
              cursor={cursor}
              placeholder={placeholder}
              showPlaceholder={!hasContent}
            />
          </Box>
        </Box>

        <Box width="100%" justifyContent="space-between" marginTop={1}>
          <Box>
            <Text bold color={colors.blueBright}>Build</Text>
            <Text color={colors.dim}>{' '}· Xninetzy Neon</Text>
          </Box>
          <Text color={colors.muted}>
            {isSending ? 'request active · Esc stop' : 'Enter send · Ctrl+U clear'}
          </Text>
        </Box>
      </Box>

      {attachments.length > 0 && (
        <Box paddingX={1}>
          <Text color={colors.dim} italic>
            {attachments.length} attached · backspace removes last
          </Text>
        </Box>
      )}
    </Box>
  );
}

function DraftLine({
  draft,
  cursor,
  placeholder,
  showPlaceholder
}: {
  draft: string;
  cursor: number;
  placeholder: string;
  showPlaceholder: boolean;
}) {
  if (showPlaceholder) return <Text color={colors.muted}>{placeholder}</Text>;

  const before = draft.slice(0, cursor);
  const atCursor = draft.charAt(cursor) || ' ';
  const after = draft.slice(cursor + 1);

  return (
    <Text color={colors.white}>
      {before}
      <Text color={colors.black} backgroundColor={colors.cyanBright}>{atCursor}</Text>
      {after}
    </Text>
  );
}

export const InputBox = memo(InputBoxComponent);
