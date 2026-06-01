export function requireString(input: Record<string, unknown>, key: string): string {
  const value = input[key];
  if (typeof value !== "string" || value.trim().length === 0) {
    throw new Error(`Missing or invalid string parameter: ${key}`);
  }
  return value.trim();
}

export function optionalString(input: Record<string, unknown>, key: string): string | undefined {
  const value = input[key];
  if (value === undefined || value === null) return undefined;
  if (typeof value !== "string") {
    throw new Error(`Invalid string parameter: ${key}`);
  }
  const trimmed = value.trim();
  return trimmed.length > 0 ? trimmed : undefined;
}

export function requireBoolean(input: Record<string, unknown>, key: string): boolean {
  const value = input[key];
  if (typeof value !== "boolean") {
    throw new Error(`Missing or invalid boolean parameter: ${key}`);
  }
  return value;
}

export function optionalBoolean(input: Record<string, unknown>, key: string, fallback = false): boolean {
  const value = input[key];
  if (value === undefined || value === null) return fallback;
  if (typeof value !== "boolean") {
    throw new Error(`Invalid boolean parameter: ${key}`);
  }
  return value;
}

export function requireNumber(input: Record<string, unknown>, key: string): number {
  const value = input[key];
  if (typeof value !== "number" || !Number.isFinite(value)) {
    throw new Error(`Missing or invalid number parameter: ${key}`);
  }
  return value;
}

export function optionalNumber(input: Record<string, unknown>, key: string): number | undefined {
  const value = input[key];
  if (value === undefined || value === null) return undefined;
  if (typeof value !== "number" || !Number.isFinite(value)) {
    throw new Error(`Invalid number parameter: ${key}`);
  }
  return value;
}

export function requireStringArray(input: Record<string, unknown>, key: string): string[] {
  const value = input[key];
  if (!Array.isArray(value) || value.some((item) => typeof item !== "string" || item.trim().length === 0)) {
    throw new Error(`Missing or invalid string array parameter: ${key}`);
  }
  return value.map((item) => item.trim());
}
