import type { McpTool } from "../types";
import { logger } from "../../utils/logger";
import { sourceToMessageMedia, publicMessageResult } from "../media";
import {
  optionalBoolean,
  optionalNumber,
  optionalString,
  requireNumber,
  requireString,
  requireStringArray,
} from "../validation";

const jidParam = { type: "string", description: "Target WhatsApp JID" };

export const messageTools: McpTool[] = [
  {
    definition: {
      name: "send_text_message",
      description: "Kirim pesan teks WhatsApp.",
      inputSchema: {
        type: "object",
        properties: { jid: jidParam, text: { type: "string" } },
        required: ["jid", "text"],
      },
    },
    async handler(input, { sock }) {
      const message = await sock.sendMessage(requireString(input, "jid"), {
        text: requireString(input, "text"),
      });
      return publicMessageResult(message);
    },
  },
  {
    definition: {
      name: "send_image",
      description: "Kirim gambar dari URL, file URL, atau base64.",
      inputSchema: {
        type: "object",
        properties: { jid: jidParam, source: { type: "string" }, caption: { type: "string" } },
        required: ["jid", "source"],
      },
    },
    async handler(input, { sock }) {
      const message = await sock.sendMessage(requireString(input, "jid"), {
        image: sourceToMessageMedia(requireString(input, "source")),
        caption: optionalString(input, "caption"),
      } as any);
      return publicMessageResult(message);
    },
  },
  {
    definition: {
      name: "send_video",
      description: "Kirim video dari URL, file URL, atau base64.",
      inputSchema: {
        type: "object",
        properties: { jid: jidParam, source: { type: "string" }, caption: { type: "string" } },
        required: ["jid", "source"],
      },
    },
    async handler(input, { sock }) {
      const message = await sock.sendMessage(requireString(input, "jid"), {
        video: sourceToMessageMedia(requireString(input, "source")),
        caption: optionalString(input, "caption"),
      } as any);
      return publicMessageResult(message);
    },
  },
  {
    definition: {
      name: "send_audio",
      description: "Kirim audio biasa dari URL, file URL, atau base64.",
      inputSchema: {
        type: "object",
        properties: { jid: jidParam, source: { type: "string" } },
        required: ["jid", "source"],
      },
    },
    async handler(input, { sock }) {
      const message = await sock.sendMessage(requireString(input, "jid"), {
        audio: sourceToMessageMedia(requireString(input, "source")),
      } as any);
      return publicMessageResult(message);
    },
  },
  {
    definition: {
      name: "send_ptt",
      description: "Kirim voice note/push-to-talk dari URL, file URL, atau base64.",
      inputSchema: {
        type: "object",
        properties: { jid: jidParam, source: { type: "string" } },
        required: ["jid", "source"],
      },
    },
    async handler(input, { sock }) {
      const message = await sock.sendMessage(requireString(input, "jid"), {
        audio: sourceToMessageMedia(requireString(input, "source")),
        ptt: true,
      } as any);
      return publicMessageResult(message);
    },
  },
  {
    definition: {
      name: "send_document",
      description: "Kirim dokumen dari URL, file URL, atau base64.",
      inputSchema: {
        type: "object",
        properties: {
          jid: jidParam,
          source: { type: "string" },
          filename: { type: "string" },
          mimetype: { type: "string" },
        },
        required: ["jid", "source", "filename", "mimetype"],
      },
    },
    async handler(input, { sock }) {
      const message = await sock.sendMessage(requireString(input, "jid"), {
        document: sourceToMessageMedia(requireString(input, "source")),
        fileName: requireString(input, "filename"),
        mimetype: requireString(input, "mimetype"),
      } as any);
      return publicMessageResult(message);
    },
  },
  {
    definition: {
      name: "send_sticker",
      description: "Kirim stiker WebP dari URL, file URL, atau base64.",
      inputSchema: {
        type: "object",
        properties: { jid: jidParam, source: { type: "string" } },
        required: ["jid", "source"],
      },
    },
    async handler(input, { sock }) {
      const message = await sock.sendMessage(requireString(input, "jid"), {
        sticker: sourceToMessageMedia(requireString(input, "source")),
      } as any);
      return publicMessageResult(message);
    },
  },
  {
    definition: {
      name: "send_reaction",
      description: "Kirim reaksi emoji ke pesan.",
      inputSchema: {
        type: "object",
        properties: { jid: jidParam, message_id: { type: "string" }, emoji: { type: "string" } },
        required: ["jid", "message_id", "emoji"],
      },
    },
    async handler(input, { sock }) {
      const jid = requireString(input, "jid");
      const message = await sock.sendMessage(jid, {
        react: { text: requireString(input, "emoji"), key: { remoteJid: jid, id: requireString(input, "message_id") } },
      } as any);
      return publicMessageResult(message);
    },
  },
  {
    definition: {
      name: "send_poll",
      description: "Buat polling WhatsApp.",
      inputSchema: {
        type: "object",
        properties: {
          jid: jidParam,
          question: { type: "string" },
          options: { type: "array", items: { type: "string" } },
          allow_multiple: { type: "boolean" },
        },
        required: ["jid", "question", "options"],
      },
    },
    async handler(input, { sock }) {
      const message = await sock.sendMessage(requireString(input, "jid"), {
        poll: {
          name: requireString(input, "question"),
          values: requireStringArray(input, "options"),
          selectableCount: optionalBoolean(input, "allow_multiple") ? 0 : 1,
        },
      } as any);
      return publicMessageResult(message);
    },
  },
  {
    definition: {
      name: "send_location",
      description: "Kirim lokasi.",
      inputSchema: {
        type: "object",
        properties: {
          jid: jidParam,
          lat: { type: "number" },
          lng: { type: "number" },
          name: { type: "string" },
          address: { type: "string" },
        },
        required: ["jid", "lat", "lng"],
      },
    },
    async handler(input, { sock }) {
      const message = await sock.sendMessage(requireString(input, "jid"), {
        location: {
          degreesLatitude: requireNumber(input, "lat"),
          degreesLongitude: requireNumber(input, "lng"),
          name: optionalString(input, "name"),
          address: optionalString(input, "address"),
        },
      } as any);
      return publicMessageResult(message);
    },
  },
  {
    definition: {
      name: "send_contact",
      description: "Kirim kartu kontak.",
      inputSchema: {
        type: "object",
        properties: { jid: jidParam, contact_name: { type: "string" }, contact_phone: { type: "string" } },
        required: ["jid", "contact_name", "contact_phone"],
      },
    },
    async handler(input, { sock }) {
      const name = requireString(input, "contact_name");
      const phone = requireString(input, "contact_phone");
      const vcard = [
        "BEGIN:VCARD",
        "VERSION:3.0",
        `FN:${name}`,
        `TEL;type=CELL;type=VOICE;waid=${phone.replace(/\D/g, "")}:${phone}`,
        "END:VCARD",
      ].join("\n");
      const message = await sock.sendMessage(requireString(input, "jid"), {
        contacts: { displayName: name, contacts: [{ vcard }] },
      } as any);
      return publicMessageResult(message);
    },
  },
  {
    definition: {
      name: "edit_message",
      description: "Edit pesan yang pernah dikirim bot.",
      inputSchema: {
        type: "object",
        properties: { jid: jidParam, message_id: { type: "string" }, new_text: { type: "string" } },
        required: ["jid", "message_id", "new_text"],
      },
    },
    async handler(input, { sock }) {
      const jid = requireString(input, "jid");
      const message = await sock.sendMessage(jid, {
        text: requireString(input, "new_text"),
        edit: { remoteJid: jid, id: requireString(input, "message_id"), fromMe: true },
      } as any);
      return publicMessageResult(message);
    },
  },
  {
    definition: {
      name: "delete_message",
      description: "Hapus/revoke pesan bot.",
      inputSchema: {
        type: "object",
        properties: { jid: jidParam, message_id: { type: "string" } },
        required: ["jid", "message_id"],
      },
    },
    async handler(input, { sock }) {
      const jid = requireString(input, "jid");
      const message = await sock.sendMessage(jid, {
        delete: { remoteJid: jid, id: requireString(input, "message_id"), fromMe: true },
      } as any);
      return publicMessageResult(message);
    },
  },
  {
    definition: {
      name: "pin_message",
      description: "Pin pesan di chat/grup.",
      inputSchema: {
        type: "object",
        properties: {
          jid: jidParam,
          message_id: { type: "string" },
          duration: { type: "number" },
          from_me: { type: "boolean" },
          participant: { type: "string" },
        },
        required: ["jid", "message_id"],
      },
    },
    async handler(input, { sock }) {
      const jid = requireString(input, "jid");
      const messageId = requireString(input, "message_id");
      const duration = optionalNumber(input, "duration") ?? 86_400;
      const fromMe = optionalBoolean(input, "from_me") ?? false;
      const participant = optionalString(input, "participant");

      if (jid.endsWith("@g.us")) {
        try {
          const metadata = await sock.groupMetadata(jid);
          const botId = sock.user?.id?.split(":")[0];
          const me = metadata.participants.find((p) => p.id.split(":")[0] === botId);
          logger.info(
            { step: "tool_pin_admin_check", jid, isAdmin: Boolean(me?.admin), botId },
            "Checking bot admin status for pin",
          );
        } catch (err) {
          logger.warn({ step: "tool_pin_admin_check_failed", err, jid }, "Failed to check bot admin status");
        }
      }

      logger.info(
        { step: "tool_pin_message_start", jid, messageId, duration, fromMe, participant },
        "Attempting to pin message",
      );

      const message = await sock.sendMessage(jid, {
        pin: {
          type: 1,
          time: duration,
          key: {
            remoteJid: jid,
            id: messageId,
            fromMe: fromMe,
            ...(fromMe ? {} : { participant: participant || undefined }),
          },
        },
      } as any);

      return publicMessageResult(message);
    },
  },
];
