import React, { useMemo } from 'react';
import { Box, Text } from 'ink';
import { colors } from '../theme/colors.js';

type StaticStarBackdropProps = {
  width: number;
  height: number;
  density?: number;
};

function createRandom(seed: number): () => number {
  let value = seed >>> 0;
  return () => {
    value += 0x6d2b79f5;
    let result = value;
    result = Math.imul(result ^ (result >>> 15), result | 1);
    result ^= result + Math.imul(result ^ (result >>> 7), result | 61);
    return ((result ^ (result >>> 14)) >>> 0) / 4_294_967_296;
  };
}

function starTone(index: number): string {
  return [colors.starDark, colors.starDark, colors.starDim, colors.starDim, colors.starSoft][index] ?? colors.starDim;
}

export function StaticStarBackdrop({
  width,
  height,
  density = 0.012
}: StaticStarBackdropProps) {
  const stars = useMemo(() => {
    const safeWidth = Math.max(1, width);
    const safeHeight = Math.max(1, height);
    const canvas = Array.from({ length: safeHeight }, () => Array<string>(safeWidth).fill(' '));
    const random = createRandom(safeWidth * 73_856_093 + safeHeight * 19_349_663);
    const starCount = Math.max(16, Math.floor(safeWidth * safeHeight * density));
    const symbols = ['.', '.', '.', '·', '·', '*'];

    for (let index = 0; index < starCount; index += 1) {
      const x = Math.floor(random() * safeWidth);
      const y = Math.floor(random() * safeHeight);
      canvas[y][x] = symbols[Math.floor(random() * symbols.length)] ?? '.';
    }

    return canvas.map((row) => row.join(''));
  }, [width, height, density]);

  return (
    <Box position="absolute" width={width} height={height} flexDirection="column">
      {stars.map((line, index) => (
        <Text key={String(index) + '-' + line} color={starTone(index % 5)} wrap="truncate">
          {line}
        </Text>
      ))}
    </Box>
  );
}
