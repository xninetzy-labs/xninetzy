import { useEffect, useState } from 'react';
import { useStdout } from 'ink';

type TerminalDimensions = [
  columns: number,
  rows: number
];

function readDimensions(
  stdout: NodeJS.WriteStream
): TerminalDimensions {
  return [
    Math.max(40, stdout.columns ?? 120),
    Math.max(20, stdout.rows ?? 40)
  ];
}

export function useStdoutDimensions(): TerminalDimensions {
  const { stdout } = useStdout();

  const [dimensions, setDimensions] =
    useState<TerminalDimensions>(() =>
      readDimensions(stdout)
    );

  useEffect(() => {
    const handleResize = (): void => {
      setDimensions(readDimensions(stdout));
    };

    stdout.on('resize', handleResize);

    return () => {
      stdout.off('resize', handleResize);
    };
  }, [stdout]);

  return dimensions;
}
