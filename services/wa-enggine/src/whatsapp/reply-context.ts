import type { WASocket, WAMessage } from "@whiskeysockets/baileys";
import { logger } from "../utils/logger";
import { maskJid } from "../utils/observability";
import { sendTextMessage } from "./message-sender";

export async function sendWhatsAppReply(params: {
  sock: WASocket;
  remoteJid: string;
  reply: string;
  quoted: WAMessage;
  traceId: string;
  messageId: string | null | undefined;
  chatType: "private" | "group";
  rememberBotMessageId: (id: string | null | undefined) => void;
}): Promise<void> {
  const { sock, remoteJid, reply, quoted, traceId, messageId, chatType, rememberBotMessageId } = params;

  logger.info(
    {
      step: "reply_sending",
      traceId,
      messageId,
      remoteJid: maskJid(remoteJid),
      replyLength: reply.length,
    },
    "Sending AI reply to WhatsApp"
  );

  try {
    const sentMessage = await sendTextMessage(sock, remoteJid, reply, { quoted });
    rememberBotMessageId(sentMessage?.key.id);
  } catch (error) {
    logger.warn(
      {
        step: "reply_quoted_failed",
        traceId,
        messageId,
        remoteJid: maskJid(remoteJid),
        err: error,
      },
      "Failed to send quoted reply, retrying without quoted message"
    );

    try {
      const sentMessage = await sendTextMessage(sock, remoteJid, reply);
      rememberBotMessageId(sentMessage?.key.id);
    } catch (sendError) {
      logger.error(
        {
          step: "reply_failed",
          traceId,
          messageId,
          remoteJid: maskJid(remoteJid),
          err: sendError,
        },
        "Failed to send WhatsApp reply"
      );
      throw sendError;
    }
  }

  logger.info(
    {
      step: "reply_sent",
      traceId,
      messageId,
      remoteJid: maskJid(remoteJid),
    },
    "AI reply sent to WhatsApp"
  );
}
