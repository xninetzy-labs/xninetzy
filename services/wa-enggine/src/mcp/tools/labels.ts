import type { McpTool } from "../types";
import { requireString } from "../validation";

const labelsByJid = new Map<string, Set<string>>();

export const labelTools: McpTool[] = [
  {
    definition: {
      name: "add_label",
      description: "Tambah label internal ke chat. Label disimpan in-memory pada WA engine MVP.",
      inputSchema: {
        type: "object",
        properties: { jid: { type: "string" }, label_name: { type: "string" } },
        required: ["jid", "label_name"],
      },
    },
    async handler(input) {
      const jid = requireString(input, "jid");
      const label = requireString(input, "label_name");
      const labels = labelsByJid.get(jid) ?? new Set<string>();
      labels.add(label);
      labelsByJid.set(jid, labels);
      return { jid, labels: [...labels] };
    },
  },
  {
    definition: {
      name: "remove_label",
      description: "Hapus label internal dari chat.",
      inputSchema: {
        type: "object",
        properties: { jid: { type: "string" }, label_name: { type: "string" } },
        required: ["jid", "label_name"],
      },
    },
    async handler(input) {
      const jid = requireString(input, "jid");
      const label = requireString(input, "label_name");
      const labels = labelsByJid.get(jid) ?? new Set<string>();
      labels.delete(label);
      labelsByJid.set(jid, labels);
      return { jid, labels: [...labels] };
    },
  },
  {
    definition: {
      name: "get_chat_labels",
      description: "Ambil label internal pada chat.",
      inputSchema: { type: "object", properties: { jid: { type: "string" } }, required: ["jid"] },
    },
    async handler(input) {
      const jid = requireString(input, "jid");
      return { jid, labels: [...(labelsByJid.get(jid) ?? new Set<string>())] };
    },
  },
];
