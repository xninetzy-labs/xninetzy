import axios, { AxiosError } from "axios";
import { env } from "../config/env";
import { logger } from "../utils/logger";
import type { AIChatPayload, AIChatResponse } from "../types/ai";

const client = axios.create({
  baseURL: env.AI_API_URL,
  timeout: env.AI_TIMEOUT_MS || 60_000,
});

export async function sendChatToAI(
  payload: AIChatPayload,
): Promise<AIChatResponse> {
  const startedAt = Date.now();

  logger.info(
    {
      step: "ai_request_start",
      url: `${env.AI_API_URL}/api/chat`,
      chatType: payload.chat_type,
      textLength: payload.message.length,
      hasSenderId: Boolean(payload.sender_id),
    },
    "Sending WhatsApp message to AI service",
  );

  try {
    const response = await client.post<AIChatResponse>("/api/chat", payload);

    logger.info(
      {
        step: "ai_response_received",
        status: response.status,
        durationMs: Date.now() - startedAt,
      },
      "AI service response received",
    );

    return response.data;
  } catch (error) {
    const err = error as AxiosError;

    logger.error(
      {
        step: "ai_request_failed",
        durationMs: Date.now() - startedAt,
        status: err.response?.status,
        code: err.code,
        responseData: err.response?.data,
      },
      "AI service request failed",
    );

    return {
      reply: "Maaf, Xninetzy AI lagi error sebentar. Coba ulangi lagi ya.",
    };
  }
}
