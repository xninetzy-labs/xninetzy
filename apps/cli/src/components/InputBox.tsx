import React, { useEffect, useState } from 'react';
import { Box, Text, useInput } from 'ink';
import { colors } from '../theme/colors.js';
import { describeBlock } from '../types.js';

type InputBoxProps = {
  /** The editable tail the user is typing (the "..." part). */
  draft: string;
  /** Collapsed large pastes, shown as chips before the editable tail. */
  attachments: string[];
  onDraftChange: (value: string) => void;
  onPaste: (block: string) => void;
  onRemoveLastAttachment: () => void;
  onSubmit: () => void;
  width: number;
};

// A multi-char chunk that looks like a paste rather than a keystroke.
const PASTE_MIN_CHARS = 64;

function isLargePaste(input: string): boolean {
  if (input.length <= 1) return false;
  return (
    input.includes('\n') ||
    input.includes('\r') ||
    input.length >= PASTE_MIN_CHARS
  );
}

/**
 * Custom controlled input.
 *
 * Unlike `ink-text-input`, big pastes are not dumped into the buffer — they are
 * lifted into collapsed chips (`[1000 lines] ▸`) and the user keeps typing a
 * short tail after them. On submit the chips + tail are combined upstream.
 */
export function InputBox({
  draft,
  attachments,
  onDraftChange,
  onPaste,
  onRemoveLastAttachment,
  onSubmit,
  width
}: InputBoxProps) {
  const [cursor, setCursor] = useState(draft.length);

  // Keep the cursor inside the draft when it changes from the outside
  // (e.g. after submit clears it).
  useEffect(() => {
    setCursor((c) => Math.min(c, draft.length));
  }, [draft]);

  useInput((input, key) => {
    if (key.return) {
      onSubmit();
      return;
    }

    if (key.leftArrow) {
      setCursor((c) => Math.max(0, c - 1));
      return;
    }
    if (key.rightArrow) {
      setCursor((c) => Math.min(draft.length, c + 1));
      return;
    }

    if (key.backspace || key.delete) {
      if (cursor > 0) {
        onDraftChange(draft.slice(0, cursor - 1) + draft.slice(cursor));
        setCursor((c) => Math.max(0, c - 1));
      } else if (attachments.length > 0) {
        // At the start of an empty tail, backspace pops the last paste chip.
        onRemoveLastAttachment();
      }
      return;
    }

    // Ctrl+U clears the editable tail (matches common shell behaviour).
    if (key.ctrl && input === 'u') {
      onDraftChange('');
      setCursor(0);
      return;
    }

    // Escape / arrows / other control keys arrive with empty input — ignore.
    if (!input || key.ctrl || key.meta) {
      return;
    }

    if (isLargePaste(input)) {
      onPaste(input);
      return;
    }

    onDraftChange(draft.slice(0, cursor) + input + draft.slice(cursor));
    setCursor((c) => c + input.length);
  });

  const hasContent = draft.length > 0 || attachments.length > 0;
  const placeholder = attachments.length > 0 ? 'Add a comment…' : 'Ask anything… "halo"';

  return (
    <Box width={width} flexDirection="column" paddingX={1}>
      <Box
        width={width - 2}
        borderStyle="round"
        borderColor={attachments.length > 0 ? colors.orange : colors.border}
        paddingX={1}
      >
        <Text color={colors.orange}>◎ </Text>

        {attachments.map((block, i) => (
          <Box key={i} marginRight={1}>
            <Text color={colors.backgroundSoft} backgroundColor={colors.orangeBright} bold>
              {' '}❏ {describeBlock(block)}{' '}
            </Text>
            <Text color={colors.dim}> ▸ </Text>
          </Box>
        ))}

        <Box flexGrow={1}>
          <DraftLine draft={draft} cursor={cursor} placeholder={placeholder} showPlaceholder={!hasContent} />
        </Box>
      </Box>

      {attachments.length > 0 && (
        <Box paddingX={1}>
          <Text color={colors.dim} italic>
            {attachments.length} pasted block{attachments.length > 1 ? 's' : ''} attached · backspace on empty line removes the last · ctrl+u clears
          </Text>
        </Box>
      )}
    </Box>
  );
}

type DraftLineProps = {
  draft: string;
  cursor: number;
  placeholder: string;
  showPlaceholder: boolean;
};

/** Renders the editable tail with a block cursor (no real terminal cursor). */
function DraftLine({ draft, cursor, placeholder, showPlaceholder }: DraftLineProps) {
  if (showPlaceholder) {
    return (
      <Text>
        <Text inverse color={colors.dim}>
          {placeholder.charAt(0)}
        </Text>
        <Text color={colors.dim}>{placeholder.slice(1)}</Text>
      </Text>
    );
  }

  const before = draft.slice(0, cursor);
  const atCursor = draft.charAt(cursor) || ' ';
  const after = draft.slice(cursor + 1);

  return (
    <Text color={colors.white}>
      {before}
      <Text inverse>{atCursor}</Text>
      {after}
    </Text>
  );
}
