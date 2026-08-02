import { useEffect, useState } from 'react';
import { useStdout } from 'ink';

export interface TerminalSize {
  columns: number;
  rows: number;
}

function readTerminalSize(
  stdout: NodeJS.WriteStream
): TerminalSize {
  return {
    columns: Math.max(40, stdout.columns ?? 120),
    rows: Math.max(12, stdout.rows ?? 30)
  };
}

export function useTerminalSize(): TerminalSize {
  const { stdout } = useStdout();

  const [size, setSize] = useState<TerminalSize>(() =>
    readTerminalSize(stdout)
  );

  useEffect(() => {
    const updateSize = (): void => {
      setSize(readTerminalSize(stdout));
    };

    updateSize();
    stdout.on('resize', updateSize);

    return () => {
      stdout.off('resize', updateSize);
    };
  }, [stdout]);

  return size;
}
