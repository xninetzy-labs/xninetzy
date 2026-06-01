import type { McpTool } from "../types";
import { requireString } from "../validation";

function unavailable(name: string): McpTool {
  return {
    definition: {
      name,
      description: "Placeholder media retrieval tool. Butuh message store/media pipeline untuk mengambil media pesan lama.",
      inputSchema: { type: "object", properties: { message_id: { type: "string" } }, required: ["message_id"] },
    },
    async handler(input) {
      requireString(input, "message_id");
      throw new Error(`${name} needs persisted message/media store before it can be used safely.`);
    },
  };
}

export const mediaTools: McpTool[] = [unavailable("download_media"), unavailable("get_media_url")];
