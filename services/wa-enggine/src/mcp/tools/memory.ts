import type { McpTool } from "../types";

function unavailable(name: string): McpTool {
  return {
    definition: {
      name,
      description: "Placeholder memory tool. Implementasi FAISS/SQLite ada di AI service.",
      inputSchema: { type: "object", properties: {} },
    },
    async handler() {
      throw new Error(`${name} is not implemented in WA engine. Call the AI memory service instead.`);
    },
  };
}

export const memoryTools: McpTool[] = [
  unavailable("memory_faiss_search"),
  unavailable("memory_sqlite_get"),
  unavailable("memory_save_summary"),
  unavailable("memory_save_full"),
];
