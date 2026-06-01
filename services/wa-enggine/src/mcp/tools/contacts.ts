import type { McpTool } from "../types";
import { requireString } from "../validation";

const jidParam = { type: "string", description: "WhatsApp JID" };

export const contactTools: McpTool[] = [
  {
    definition: {
      name: "get_contact_info",
      description: "Ambil info kontak dari store/signal WhatsApp jika tersedia.",
      inputSchema: { type: "object", properties: { jid: jidParam }, required: ["jid"] },
    },
    async handler(input, { sock }) {
      const jid = requireString(input, "jid");
      const [status, profilePictureUrl] = await Promise.allSettled([
        (sock as any).fetchStatus?.(jid),
        sock.profilePictureUrl(jid, "image"),
      ]);

      return {
        jid,
        status: status.status === "fulfilled" ? status.value : null,
        profile_picture_url: profilePictureUrl.status === "fulfilled" ? profilePictureUrl.value : null,
      };
    },
  },
  {
    definition: {
      name: "block_contact",
      description: "Blokir kontak.",
      inputSchema: { type: "object", properties: { jid: jidParam }, required: ["jid"] },
    },
    async handler(input, { sock }) {
      await sock.updateBlockStatus(requireString(input, "jid"), "block");
      return { blocked: true };
    },
  },
  {
    definition: {
      name: "unblock_contact",
      description: "Buka blokir kontak.",
      inputSchema: { type: "object", properties: { jid: jidParam }, required: ["jid"] },
    },
    async handler(input, { sock }) {
      await sock.updateBlockStatus(requireString(input, "jid"), "unblock");
      return { blocked: false };
    },
  },
  {
    definition: {
      name: "get_blocklist",
      description: "Ambil daftar kontak yang diblokir.",
      inputSchema: { type: "object", properties: {} },
    },
    async handler(_input, { sock }) {
      return { blocklist: await sock.fetchBlocklist() };
    },
  },
  {
    definition: {
      name: "update_status",
      description: "Update status/bio profil bot.",
      inputSchema: { type: "object", properties: { status_text: { type: "string" } }, required: ["status_text"] },
    },
    async handler(input, { sock }) {
      await sock.updateProfileStatus(requireString(input, "status_text"));
      return { updated: true };
    },
  },
  {
    definition: {
      name: "update_profile_name",
      description: "Update nama profil bot.",
      inputSchema: { type: "object", properties: { name: { type: "string" } }, required: ["name"] },
    },
    async handler(input, { sock }) {
      await sock.updateProfileName(requireString(input, "name"));
      return { updated: true };
    },
  },
];
