export function getMockReply(input: string): string {
  const normalized = input.toLowerCase().trim();

  if (
    normalized.includes("halo") ||
    normalized.includes("hai") ||
    normalized.includes("hello")
  ) {
    return "hei yoi this is xninetzy";
  }

  return "xninetzy mock mode aktif — AI belum disambungkan.";
}
