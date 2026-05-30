export type ChatType = "private" | "group" | "broadcast" | "status" | "unknown";

export function isProcessableChatType(chatType: ChatType): chatType is "private" | "group" {
  return chatType === "private" || chatType === "group";
}
