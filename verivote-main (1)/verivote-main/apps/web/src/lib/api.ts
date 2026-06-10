const DEFAULT_API_BASE_URL = "http://127.0.0.1:8000";
const API_PREFIX = "/api/v2";

type ApiMethod = "GET" | "POST";

interface ApiOptions {
  method?: ApiMethod;
  body?: unknown;
}

const configuredApiBaseUrl = (import.meta.env.VITE_API_BASE_URL as string | undefined)
  ?.trim()
  .replace(/\/+$/, "");

export const apiBaseUrl =
  configuredApiBaseUrl && configuredApiBaseUrl.length > 0
    ? configuredApiBaseUrl
    : DEFAULT_API_BASE_URL;

function normalizeApiPath(path: string): string {
  if (/^https?:\/\//i.test(path)) {
    return path;
  }

  const normalizedPath = path.startsWith("/") ? path : `/${path}`;
  if (normalizedPath.startsWith("/api/")) {
    return normalizedPath;
  }
  return `${API_PREFIX}${normalizedPath}`;
}

export function buildApiUrl(path: string): string {
  const normalizedPath = normalizeApiPath(path);
  if (/^https?:\/\//i.test(normalizedPath)) {
    return normalizedPath;
  }
  return `${apiBaseUrl}${normalizedPath}`;
}

function snakeToCamel(key: string): string {
  return key.replace(/_([a-z])/g, (_match, letter: string) => letter.toUpperCase());
}

function normalizeApiData(value: unknown): unknown {
  if (Array.isArray(value)) {
    return value.map((item) => normalizeApiData(item));
  }

  if (value && typeof value === "object") {
    return Object.fromEntries(
      Object.entries(value).map(([key, child]) => [
        snakeToCamel(key),
        normalizeApiData(child)
      ])
    );
  }

  return value;
}

function extractBackendMessage(value: unknown): string | null {
  if (!value || typeof value !== "object") {
    return null;
  }

  const payload = value as Record<string, unknown>;
  const direct = payload.error ?? payload.message;
  if (typeof direct === "string") {
    return direct;
  }

  const detail = payload.detail;
  if (typeof detail === "string") {
    return detail;
  }

  if (Array.isArray(detail)) {
    const messages = detail
      .map((item) => {
        if (item && typeof item === "object" && typeof (item as { msg?: unknown }).msg === "string") {
          return (item as { msg: string }).msg;
        }
        return null;
      })
      .filter((item): item is string => item !== null);
    if (messages.length > 0) {
      return messages.join("; ");
    }
  }

  return null;
}

export class ApiRequestError extends Error {
  readonly requestUrl: string;
  readonly status?: number;
  readonly backendMessage?: string;

  constructor(message: string, requestUrl: string, status?: number, backendMessage?: string) {
    super(message);
    this.name = "ApiRequestError";
    this.requestUrl = requestUrl;
    this.status = status;
    this.backendMessage = backendMessage;
  }
}

export async function apiRequest<T>(path: string, options: ApiOptions = {}): Promise<T> {
  const requestUrl = buildApiUrl(path);

  let response: Response;
  try {
    response = await fetch(requestUrl, {
      method: options.method ?? "GET",
      headers:
        options.body === undefined
          ? { Accept: "application/json" }
          : {
              Accept: "application/json",
              "Content-Type": "application/json"
            },
      body: options.body === undefined ? undefined : JSON.stringify(options.body)
    });
  } catch (error) {
    const message =
      error instanceof Error && error.message !== "Failed to fetch"
        ? error.message
        : `Cannot connect to the Python API. Check ${apiBaseUrl}${API_PREFIX}/health.`;
    throw new ApiRequestError(message, requestUrl);
  }

  const rawData = (await response.json().catch(() => null)) as unknown;
  if (!response.ok) {
    const backendMessage = extractBackendMessage(rawData);
    const message = backendMessage ?? `HTTP ${response.status}`;
    throw new ApiRequestError(message, requestUrl, response.status, backendMessage ?? undefined);
  }

  return normalizeApiData(rawData) as T;
}

export function getErrorMessage(error: unknown): string {
  if (error instanceof ApiRequestError) {
    const status = error.status === undefined ? "network" : `HTTP ${error.status}`;
    return `${error.message} [${status}] ${error.requestUrl}`;
  }
  return error instanceof Error ? error.message : "Request failed";
}
