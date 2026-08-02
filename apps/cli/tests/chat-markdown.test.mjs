import assert from 'node:assert/strict';
import test from 'node:test';

import stringWidth from 'string-width';

import {
  buildChatRows,
  buildMessageRows,
  parseInlineMarkdown,
  selectViewportRows
} from '../dist/rendering/chat-markdown.js';

const richMessage = {
  id: 'assistant-rich',
  role: 'assistant',
  createdAt: new Date(),
  content: [
    '# REST API',
    '',
    'Readable **bold**, `inline code`, [source](https://example.com), and [K1].',
    '',
    '- [x] Validated',
    '- A long list item that must wrap without crossing the terminal boundary.',
    '',
    '> Important context',
    '',
    '| Field | Value |',
    '| --- | --- |',
    '| phase | streaming |',
    '',
    '```ts',
    'const greeting = "hello world";',
    'console.log(greeting);',
    '```'
  ].join('\n')
};

test('renders rich Markdown responsively', () => {
  for (const width of [46, 80, 120]) {
    const rows = buildMessageRows(richMessage, width);

    assert.ok(rows.some((row) => row.kind === 'heading'));
    assert.ok(rows.some((row) => row.kind === 'code'));
    assert.ok(rows.some((row) => row.prefix?.includes('✓')));
    assert.ok(rows.some((row) => row.prefix === '▎ '));
    assert.ok(rows.some((row) =>
      row.spans.some((span) => span.style === 'citation')
    ));

    for (const row of rows) {
      const availableWidth = Math.max(
        1,
        row.panelWidth - (row.rail ? 2 : 0)
      );
      const content = `${row.prefix ?? ''}${row.spans
        .map((span) => span.text)
        .join('')}`;

      assert.ok(
        stringWidth(content) <= availableWidth,
        `row ${row.key} exceeds ${availableWidth} columns at width ${width}`
      );
    }
  }
});

test('keeps the latest visual rows inside the viewport', () => {
  const messages = Array.from({ length: 8 }, (_, index) => ({
    id: `message-${index}`,
    role: index % 2 === 0 ? 'user' : 'assistant',
    createdAt: new Date(),
    content: `Message ${index} with enough text to create a readable row.`
  }));
  const rows = buildChatRows(messages, 64);
  const visible = selectViewportRows(rows, 9);

  assert.equal(visible.length, 9);
  assert.equal(visible[0]?.kind, 'meta');
  assert.match(visible[0]?.spans[0]?.text ?? '', /earlier lines hidden/);
  assert.equal(visible.at(-1)?.messageId, 'message-7');
});

test('keeps incomplete streaming syntax readable', () => {
  assert.deepEqual(parseInlineMarkdown('unfinished **bold'), [
    { text: 'unfinished **bold', style: 'plain' }
  ]);

  const rows = buildMessageRows({
    id: 'assistant-streaming',
    role: 'assistant',
    createdAt: new Date(),
    content: '```ts\nconst active = true;'
  }, 64);

  assert.ok(rows.some((row) =>
    row.spans.some((span) => span.text.includes('generating'))
  ));
  assert.ok(rows.some((row) =>
    row.spans.some((span) => span.text.includes('closing fence'))
  ));
});
