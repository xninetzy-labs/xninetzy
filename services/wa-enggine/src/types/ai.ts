export type AIChatType = "private" | "group";

export type AIChatPayload = {
  chat_id: string;
  sender_id: string;
  sender_name?: string | null;
  message: string;
  chat_type: AIChatType;
  group_name?: string | null;
  metadata?: Record<string, unknown>;
};

export type AIChatResponse = {
  reply: string;
};
