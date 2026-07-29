export function mcpCallLogFields(body: unknown): {
  tool: string;
  inputKeys: string[];
} {
  if (!body || typeof body !== "object" || Array.isArray(body)) {
    return { tool: "unknown", inputKeys: [] };
  }

  const value = body as Record<string, unknown>;
  const input = value.input;
  const inputKeys =
    input && typeof input === "object" && !Array.isArray(input)
      ? Object.keys(input).sort()
      : [];

  return {
    tool: typeof value.tool === "string" ? value.tool : "unknown",
    inputKeys,
  };
}
