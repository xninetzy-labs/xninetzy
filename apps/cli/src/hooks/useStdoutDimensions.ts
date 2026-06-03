import { useEffect, useState } from "react";
import { useStdout } from "ink";

export function useStdoutDimensions(): [number, number] {
  const { stdout } = useStdout();
  const [dimensions, setDimensions] = useState<[number, number]>([
    stdout.columns || 100,
    stdout.rows || 30,
  ]);

  useEffect(() => {
    const handler = () => {
      setDimensions([stdout.columns || 100, stdout.rows || 30]);
    };

    stdout.on("resize", handler);
    return () => {
      stdout.off("resize", handler);
    };
  }, [stdout]);

  return dimensions;
}
