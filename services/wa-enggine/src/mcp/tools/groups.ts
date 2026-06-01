import type { McpTool } from "../types";
import { optionalNumber, requireBoolean, requireString, requireStringArray } from "../validation";

const groupParam = { type: "string", description: "WhatsApp group JID (...@g.us)" };
const memberParam = { type: "string", description: "WhatsApp member JID" };

function participantResult(result: unknown): Record<string, unknown> {
  return { participants: result };
}

export const groupTools: McpTool[] = [
  {
    definition: {
      name: "get_group_metadata",
      description: "Ambil metadata lengkap grup.",
      inputSchema: { type: "object", properties: { group_jid: groupParam }, required: ["group_jid"] },
    },
    async handler(input, { sock }) {
      return sock.groupMetadata(requireString(input, "group_jid"));
    },
  },
  {
    definition: {
      name: "get_group_members",
      description: "Ambil daftar anggota dan admin grup.",
      inputSchema: { type: "object", properties: { group_jid: groupParam }, required: ["group_jid"] },
    },
    async handler(input, { sock }) {
      const metadata = await sock.groupMetadata(requireString(input, "group_jid"));
      return {
        id: metadata.id,
        subject: metadata.subject,
        size: metadata.participants.length,
        participants: metadata.participants,
      };
    },
  },
  {
    definition: {
      name: "add_member",
      description: "Tambah anggota ke grup. Bot harus admin.",
      inputSchema: {
        type: "object",
        properties: { group_jid: groupParam, member_jid: memberParam },
        required: ["group_jid", "member_jid"],
      },
    },
    async handler(input, { sock }) {
      return participantResult(
        await sock.groupParticipantsUpdate(requireString(input, "group_jid"), [requireString(input, "member_jid")], "add"),
      );
    },
  },
  {
    definition: {
      name: "remove_member",
      description: "Keluarkan anggota dari grup. Bot harus admin.",
      inputSchema: {
        type: "object",
        properties: { group_jid: groupParam, member_jid: memberParam },
        required: ["group_jid", "member_jid"],
      },
    },
    async handler(input, { sock }) {
      return participantResult(
        await sock.groupParticipantsUpdate(requireString(input, "group_jid"), [requireString(input, "member_jid")], "remove"),
      );
    },
  },
  {
    definition: {
      name: "promote_admin",
      description: "Jadikan anggota sebagai admin grup.",
      inputSchema: {
        type: "object",
        properties: { group_jid: groupParam, member_jid: memberParam },
        required: ["group_jid", "member_jid"],
      },
    },
    async handler(input, { sock }) {
      return participantResult(
        await sock.groupParticipantsUpdate(requireString(input, "group_jid"), [requireString(input, "member_jid")], "promote"),
      );
    },
  },
  {
    definition: {
      name: "demote_admin",
      description: "Cabut admin grup.",
      inputSchema: {
        type: "object",
        properties: { group_jid: groupParam, member_jid: memberParam },
        required: ["group_jid", "member_jid"],
      },
    },
    async handler(input, { sock }) {
      return participantResult(
        await sock.groupParticipantsUpdate(requireString(input, "group_jid"), [requireString(input, "member_jid")], "demote"),
      );
    },
  },
  {
    definition: {
      name: "update_group_subject",
      description: "Ganti nama grup.",
      inputSchema: {
        type: "object",
        properties: { group_jid: groupParam, new_subject: { type: "string" } },
        required: ["group_jid", "new_subject"],
      },
    },
    async handler(input, { sock }) {
      await sock.groupUpdateSubject(requireString(input, "group_jid"), requireString(input, "new_subject"));
      return { updated: true };
    },
  },
  {
    definition: {
      name: "update_group_description",
      description: "Ganti deskripsi grup.",
      inputSchema: {
        type: "object",
        properties: { group_jid: groupParam, new_desc: { type: "string" } },
        required: ["group_jid", "new_desc"],
      },
    },
    async handler(input, { sock }) {
      await sock.groupUpdateDescription(requireString(input, "group_jid"), requireString(input, "new_desc"));
      return { updated: true };
    },
  },
  {
    definition: {
      name: "get_invite_code",
      description: "Ambil kode invite grup.",
      inputSchema: { type: "object", properties: { group_jid: groupParam }, required: ["group_jid"] },
    },
    async handler(input, { sock }) {
      const code = await sock.groupInviteCode(requireString(input, "group_jid"));
      return { code, invite_url: `https://chat.whatsapp.com/${code}` };
    },
  },
  {
    definition: {
      name: "revoke_invite_code",
      description: "Reset kode invite grup lama.",
      inputSchema: { type: "object", properties: { group_jid: groupParam }, required: ["group_jid"] },
    },
    async handler(input, { sock }) {
      const code = await sock.groupRevokeInvite(requireString(input, "group_jid"));
      return { code, invite_url: `https://chat.whatsapp.com/${code}` };
    },
  },
  {
    definition: {
      name: "set_group_announce",
      description: "Set announcement mode. true = hanya admin bisa chat.",
      inputSchema: {
        type: "object",
        properties: { group_jid: groupParam, announce: { type: "boolean" } },
        required: ["group_jid", "announce"],
      },
    },
    async handler(input, { sock }) {
      await sock.groupSettingUpdate(requireString(input, "group_jid"), requireBoolean(input, "announce") ? "announcement" : "not_announcement");
      return { updated: true };
    },
  },
  {
    definition: {
      name: "set_group_lock",
      description: "Set group info locked. true = hanya admin bisa ubah info grup.",
      inputSchema: {
        type: "object",
        properties: { group_jid: groupParam, locked: { type: "boolean" } },
        required: ["group_jid", "locked"],
      },
    },
    async handler(input, { sock }) {
      await sock.groupSettingUpdate(requireString(input, "group_jid"), requireBoolean(input, "locked") ? "locked" : "unlocked");
      return { updated: true };
    },
  },
  {
    definition: {
      name: "set_group_ephemeral",
      description: "Set disappearing messages grup dalam detik. 0 untuk off.",
      inputSchema: {
        type: "object",
        properties: { group_jid: groupParam, seconds: { type: "number" } },
        required: ["group_jid", "seconds"],
      },
    },
    async handler(input, { sock }) {
      await (sock as any).groupToggleEphemeral(requireString(input, "group_jid"), optionalNumber(input, "seconds") ?? 0);
      return { updated: true };
    },
  },
  {
    definition: {
      name: "set_member_add_mode",
      description: "Atur siapa yang bisa tambah anggota.",
      inputSchema: {
        type: "object",
        properties: { group_jid: groupParam, admin_only: { type: "boolean" } },
        required: ["group_jid", "admin_only"],
      },
    },
    async handler(input, { sock }) {
      await (sock as any).groupMemberAddMode(requireString(input, "group_jid"), requireBoolean(input, "admin_only") ? "admin_add" : "all_member_add");
      return { updated: true };
    },
  },
  {
    definition: {
      name: "create_group",
      description: "Buat grup baru.",
      inputSchema: {
        type: "object",
        properties: { subject: { type: "string" }, participants: { type: "array", items: { type: "string" } } },
        required: ["subject", "participants"],
      },
    },
    async handler(input, { sock }) {
      return sock.groupCreate(requireString(input, "subject"), requireStringArray(input, "participants"));
    },
  },
  {
    definition: {
      name: "leave_group",
      description: "Bot keluar dari grup.",
      inputSchema: { type: "object", properties: { group_jid: groupParam }, required: ["group_jid"] },
    },
    async handler(input, { sock }) {
      await sock.groupLeave(requireString(input, "group_jid"));
      return { left: true };
    },
  },
  {
    definition: {
      name: "accept_invite",
      description: "Bot join grup via invite code.",
      inputSchema: { type: "object", properties: { invite_code: { type: "string" } }, required: ["invite_code"] },
    },
    async handler(input, { sock }) {
      const groupJid = await sock.groupAcceptInvite(requireString(input, "invite_code"));
      return { group_jid: groupJid };
    },
  },
];
