import http from "node:http";
import { env } from "../config/env";
import { getCurrentSocket } from "../whatsapp/socket-state";
import { logger } from "../utils/logger";
import { getTool, listToolDefinitions } from "./tool-registry";
import type { McpCallRequest, McpCallResponse } from "./types";

const MAX_BODY_BYTES = 2 * 1024 * 1024;

let server: http.Server | null = null;

export function startMcpServer(): void {
  if (!env.MCP_SERVER_ENABLED) {
    logger.info({ step: "mcp_server_disabled" }, "MCP server disabled");
    return;
  }

  if (server) return;

  server = http.createServer((req, res) => {
    void routeRequest(req, res).catch((error) => {
      logger.error({ step: "mcp_request_failed", err: error }, "MCP request failed");
      sendJson(res, 500, { error: "internal_error", message: "Internal MCP server error" });
    });
  });

  server.listen(env.MCP_PORT, env.MCP_HOST, () => {
    logger.info(
      { step: "mcp_server_started", host: env.MCP_HOST, port: env.MCP_PORT },
      "MCP HTTP server started",
    );
  });
}

async function routeRequest(req: http.IncomingMessage, res: http.ServerResponse): Promise<void> {
  const url = new URL(req.url ?? "/", `http://${req.headers.host ?? "localhost"}`);

  if (url.pathname === "/health") {
    sendJson(res, 200, { status: "ok", socket_ready: Boolean(getCurrentSocket()) });
    return;
  }

  if (!isAuthorized(req)) {
    sendJson(res, 401, { error: "unauthorized", message: "Invalid MCP API key" });
    return;
  }

  if (req.method === "GET" && url.pathname === "/mcp/tools") {
    sendJson(res, 200, { tools: listToolDefinitions() });
    return;
  }

  if (req.method === "POST" && url.pathname === "/mcp/call") {
    const body = await readJsonBody(req);
    logger.info({ step: "mcp_call_received", body }, "MCP tool call received");
    const response = await callTool(body);
    logger.info({ step: "mcp_call_completed", tool: response.tool, success: response.success }, "MCP tool call completed");
    sendJson(res, response.success ? 200 : 400, response);
    return;
  }

  sendJson(res, 404, { error: "not_found", message: "Route not found" });
}

async function callTool(body: unknown): Promise<McpCallResponse> {
  if (!isCallRequest(body)) {
    return {
      success: false,
      tool: "unknown",
      error: { code: "invalid_request", message: "Expected body: { tool: string, input?: object }" },
    };
  }

  const tool = getTool(body.tool);
  if (!tool) {
    return {
      success: false,
      tool: body.tool,
      error: { code: "tool_not_found", message: `Unknown MCP tool: ${body.tool}` },
    };
  }

  const sock = getCurrentSocket();
  if (!sock) {
    return {
      success: false,
      tool: body.tool,
      error: { code: "socket_not_ready", message: "WhatsApp socket is not connected yet" },
    };
  }

  try {
    const result = await tool.handler(body.input ?? {}, { sock });
    return { success: true, tool: body.tool, result };
  } catch (error) {
    const message = error instanceof Error ? error.message : "Tool execution failed";
    return {
      success: false,
      tool: body.tool,
      error: { code: "tool_error", message },
    };
  }
}

function isAuthorized(req: http.IncomingMessage): boolean {
  if (!env.MCP_API_KEY) return true;
  const header = req.headers.authorization;
  return header === `Bearer ${env.MCP_API_KEY}` || req.headers["x-api-key"] === env.MCP_API_KEY;
}

function isCallRequest(value: unknown): value is McpCallRequest {
  if (!value || typeof value !== "object") return false;
  const candidate = value as Record<string, unknown>;
  const input = candidate.input;
  return (
    typeof candidate.tool === "string" &&
    (input === undefined || (typeof input === "object" && input !== null && !Array.isArray(input)))
  );
}

async function readJsonBody(req: http.IncomingMessage): Promise<unknown> {
  const chunks: Buffer[] = [];
  let size = 0;

  for await (const chunk of req) {
    const buffer = Buffer.isBuffer(chunk) ? chunk : Buffer.from(chunk);
    size += buffer.byteLength;
    if (size > MAX_BODY_BYTES) {
      throw new Error("MCP request body too large");
    }
    chunks.push(buffer);
  }

  const raw = Buffer.concat(chunks).toString("utf8").trim();
  return raw ? JSON.parse(raw) : {};
}

function sendJson(res: http.ServerResponse, statusCode: number, payload: unknown): void {
  res.writeHead(statusCode, { "content-type": "application/json; charset=utf-8" });
  res.end(JSON.stringify(payload));
}
