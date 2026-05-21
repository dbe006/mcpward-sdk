/**
 * mcpward SDK — TypeScript client for the mcpward MCP gateway.
 *
 * Usage:
 *   const client = new MCPWardClient("https://mcpward.redfleet.fr", "mw_sk_your_key");
 *   const tools = await client.listTools();
 *   const result = await client.callTool("read_file", { path: "/tmp" });
 */

export interface MCPWardOptions {
  baseUrl: string;
  apiKey: string;
  timeout?: number;
}

export interface Tool {
  name: string;
  description?: string;
  inputSchema?: Record<string, unknown>;
  [key: string]: unknown;
}

export interface ToolResult {
  content: Array<{ type: string; text?: string; [key: string]: unknown }>;
  raw: Record<string, unknown>;
}

export interface UsageStats {
  key_id: string;
  date: string;
  calls_today: number;
  quota_limit: number;
  quota_remaining: number;
  rate_limit_per_minute: number;
  rate_current_minute: number;
  rate_remaining: number;
}

export interface WebhookConfig {
  id: string;
  url: string;
  events: string[];
  secret?: string;
  created_at?: string;
}

export class MCPWardError extends Error {
  code: number;
  data?: Record<string, unknown>;

  constructor(code: number, message: string, data?: Record<string, unknown>) {
    super(message);
    this.name = "MCPWardError";
    this.code = code;
    this.data = data;
  }
}

export class MCPWardClient {
  private baseUrl: string;
  private apiKey: string;
  private timeout: number;

  constructor(baseUrl: string, apiKey: string, timeout = 30000) {
    this.baseUrl = baseUrl.replace(/\/$/, "");
    this.apiKey = apiKey;
    this.timeout = timeout;
  }

  private get headers(): Record<string, string> {
    return {
      Authorization: `Bearer ${this.apiKey}`,
      "Content-Type": "application/json",
      Accept: "application/json, text/event-stream",
    };
  }

  private parseResponse(text: string, contentType: string): Record<string, unknown> {
    if (contentType.includes("text/event-stream")) {
      const lines = text.trim().split("\n").reverse();
      for (const line of lines) {
        if (line.startsWith("data: ")) return JSON.parse(line.slice(6));
        if (line.startsWith("data:")) return JSON.parse(line.slice(5));
      }
      throw new MCPWardError(-1, "No data in SSE response");
    }
    return JSON.parse(text);
  }

  private async jsonrpc(
    method: string,
    params: Record<string, unknown> = {},
    server?: string
  ): Promise<Record<string, unknown>> {
    const url = server
      ? `${this.baseUrl}/mcp/${server}`
      : `${this.baseUrl}/mcp`;

    const resp = await fetch(url, {
      method: "POST",
      headers: this.headers,
      body: JSON.stringify({ jsonrpc: "2.0", id: 1, method, params }),
      signal: AbortSignal.timeout(this.timeout),
    });

    const ct = resp.headers.get("content-type") || "";
    const text = await resp.text();
    const data = this.parseResponse(text, ct);

    if (data.error) {
      const err = data.error as { code?: number; message?: string; data?: Record<string, unknown> };
      throw new MCPWardError(err.code ?? -1, err.message ?? "Unknown error", err.data);
    }
    return data;
  }

  private async get(path: string): Promise<Record<string, unknown>> {
    const resp = await fetch(`${this.baseUrl}${path}`, {
      headers: this.headers,
      signal: AbortSignal.timeout(this.timeout),
    });
    const data = await resp.json();
    if (resp.status >= 400) {
      throw new MCPWardError(resp.status, (data as { error?: string }).error ?? "Error");
    }
    return data as Record<string, unknown>;
  }

  private async post(path: string, body: Record<string, unknown>): Promise<Record<string, unknown>> {
    const resp = await fetch(`${this.baseUrl}${path}`, {
      method: "POST",
      headers: this.headers,
      body: JSON.stringify(body),
      signal: AbortSignal.timeout(this.timeout),
    });
    const data = await resp.json();
    if (resp.status >= 400) {
      throw new MCPWardError(resp.status, (data as { error?: string }).error ?? "Error");
    }
    return data as Record<string, unknown>;
  }

  private async delete(path: string): Promise<Record<string, unknown>> {
    const resp = await fetch(`${this.baseUrl}${path}`, {
      method: "DELETE",
      headers: this.headers,
      signal: AbortSignal.timeout(this.timeout),
    });
    const data = await resp.json();
    if (resp.status >= 400) {
      throw new MCPWardError(resp.status, (data as { error?: string }).error ?? "Error");
    }
    return data as Record<string, unknown>;
  }

  // --- MCP operations ---

  async listTools(server?: string): Promise<Tool[]> {
    const data = await this.jsonrpc("tools/list", {}, server);
    const result = data.result as { tools?: Tool[] };
    return result?.tools ?? [];
  }

  async callTool(
    toolName: string,
    args: Record<string, unknown> = {},
    server?: string
  ): Promise<ToolResult> {
    const data = await this.jsonrpc("tools/call", { name: toolName, arguments: args }, server);
    const result = data.result as { content?: ToolResult["content"] } ?? {};
    return {
      content: result.content ?? [],
      raw: result as Record<string, unknown>,
    };
  }

  // --- Usage ---

  async getUsage(keyId: string): Promise<UsageStats> {
    return (await this.get(`/v1/usage/key/${keyId}`)) as unknown as UsageStats;
  }

  // --- Webhooks ---

  async createWebhook(url: string, events?: string[]): Promise<WebhookConfig> {
    const body: Record<string, unknown> = { url };
    if (events) body.events = events;
    return (await this.post("/v1/webhooks", body)) as unknown as WebhookConfig;
  }

  async listWebhooks(): Promise<WebhookConfig[]> {
    const data = await this.get("/v1/webhooks");
    return (data.webhooks ?? []) as WebhookConfig[];
  }

  async deleteWebhook(webhookId: string): Promise<void> {
    await this.delete(`/v1/webhooks/${webhookId}`);
  }

  // --- Billing ---

  async createCheckout(tier: "pro" | "team"): Promise<string> {
    const data = await this.post("/v1/billing/checkout", { tier });
    return data.checkout_url as string;
  }

  // --- Health ---

  async health(): Promise<{ status: string }> {
    return (await this.get("/healthz")) as { status: string };
  }

  async serverHealth(server: string): Promise<{ server: string; healthy: boolean }> {
    return (await this.get(`/mcp/${server}/health`)) as { server: string; healthy: boolean };
  }
}
