import type { McpTool, McpToolDefinition } from "./types";
import { messageTools } from "./tools/messages";
import { groupTools } from "./tools/groups";
import { contactTools } from "./tools/contacts";
import { labelTools } from "./tools/labels";
import { mediaTools } from "./tools/media";
import { memoryTools } from "./tools/memory";

const tools: McpTool[] = [
  ...messageTools,
  ...groupTools,
  ...contactTools,
  ...labelTools,
  ...mediaTools,
  ...memoryTools,
];

const toolByName = new Map<string, McpTool>();

for (const tool of tools) {
  if (toolByName.has(tool.definition.name)) {
    throw new Error(`Duplicate MCP tool registered: ${tool.definition.name}`);
  }
  toolByName.set(tool.definition.name, tool);
}

export function listToolDefinitions(): McpToolDefinition[] {
  return tools.map((tool) => tool.definition);
}

export function getTool(name: string): McpTool | undefined {
  return toolByName.get(name);
}
