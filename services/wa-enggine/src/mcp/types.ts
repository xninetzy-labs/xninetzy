import type { WASocket } from "@whiskeysockets/baileys";

export interface McpToolSchema {
  type: "object";
  properties: Record<string, unknown>;
  required?: string[];
}

export interface McpToolDefinition {
  name: string;
  description: string;
  inputSchema: McpToolSchema;
}

export interface McpToolContext {
  sock: WASocket;
}

export type McpToolHandler = (
  input: Record<string, unknown>,
  context: McpToolContext,
) => Promise<unknown>;

export interface McpTool {
  definition: McpToolDefinition;
  handler: McpToolHandler;
}

export interface McpCallRequest {
  tool: string;
  input?: Record<string, unknown>;
}

export interface McpCallResponse {
  success: boolean;
  tool: string;
  result?: unknown;
  error?: {
    code: string;
    message: string;
  };
}
