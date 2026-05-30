import axios from "axios";

import { env } from "../config/env";
import type { AIChatResponse, ChatPayload } from "../types/message";
import { logger } from "../utils/logger";

const fallbackReply = "Maaf, Xninetzy AI lagi error sebentar. Coba ulangi lagi ya.";

const client = axios.create({
  baseURL: env.AI_BASE_URL,
  timeout: env.AI_TIMEOUT_MS,
});

type FlexibleAIChatResponse = AIChatResponse & {
  response?: string;
  message?: string;
  text?: string;
  data?: {
    reply?: string;
    response?: string;
    message?: string;
    text?: string;
  };
};

export async function sendChatToAI(
  payload: ChatPayload,
  context?: { traceId?: string; messageId?: string | null }
): Promise<AIChatResponse> {
  const startedAt = Date.now();

  logger.info(
    {
      step: "ai_request_start",
      traceId: context?.traceId,
      messageId: context?.messageId,
      url: `${env.AI_BASE_URL}${env.AI_CHAT_ENDPOINT}`,
      chatType: payload.chat_type,
      textLength: payload.message.length,
    },
    "Sending WhatsApp message to AI service"
  );

  try {
    const response = await client.post<FlexibleAIChatResponse>(env.AI_CHAT_ENDPOINT, payload);

    logger.info(
      {
        step: "ai_response_received",
        traceId: context?.traceId,
        messageId: context?.messageId,
        status: response.status,
        durationMs: Date.now() - startedAt,
        bodyKeys: Object.keys(response.data || {}),
      },
      "AI service response received"
    );

    const reply = extractAiReply(response.data);
    if (!reply) {
      logger.error(
        {
          step: "ai_reply_missing",
          traceId: context?.traceId,
          messageId: context?.messageId,
          responseKeys: Object.keys(response.data || {}),
        },
        "AI response does not contain reply text"
      );

      return { reply: fallbackReply };
    }

    return { reply };
  } catch (error) {
    logger.error(
      {
        step: "ai_request_failed",
        traceId: context?.traceId,
        messageId: context?.messageId,
        durationMs: Date.now() - startedAt,
        err: error,
      },
      "AI service request failed"
    );
    return { reply: fallbackReply };
  }
}

function extractAiReply(data: FlexibleAIChatResponse): string | null {
  const reply =
    data.reply ||
    data.response ||
    data.message ||
    data.text ||
    data.data?.reply ||
    data.data?.response ||
    data.data?.message ||
    data.data?.text ||
    null;

  return typeof reply === "string" && reply.trim().length > 0 ? reply.trim() : null;
}
