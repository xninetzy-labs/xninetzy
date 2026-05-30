export type ChatType = "private" | "group";

export interface ChatPayload {
  chat_id: string;
  sender_id: string;
  sender_name: string | null;
  message: string;
  chat_type: ChatType;
  group_name: string | null;
}

export interface AIChatResponse {
  reply: string;
}
