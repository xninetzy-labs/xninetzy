import type { WASocket, WAMessage } from "@whiskeysockets/baileys";

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
  recentMessages?: Map<string, WAMessage>;
}

export type McpToolHandler = (
  input: Record<string, unknown>,
  context: McpToolContext,
) => Promise<unknown>;

export type McpOfflineToolHandler = (
  input: Record<string, unknown>,
  context: Pick<McpToolContext, "recentMessages">,
) => Promise<unknown>;

export interface McpTool {
  definition: McpToolDefinition;
  handler: McpToolHandler;
  /** Optional read-only path that is safe when the WhatsApp socket is closed. */
  offlineHandler?: McpOfflineToolHandler;
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
