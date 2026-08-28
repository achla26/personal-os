import { config } from "./config";

let accessToken: string | null = null;
let refreshPromise: Promise<string | null> | null = null;

export function setAccessToken(token: string | null) {
  accessToken = token;
}

export function getAccessToken(): string | null {
  return accessToken;
}

/**
 * Handle silent refresh with a lock (promise-sharing)
 * to prevent duplicate refresh calls if multiple API calls trigger 401 simultaneously.
 */
async function refreshAccessToken(): Promise<string | null> {
  if (refreshPromise) {
    return refreshPromise;
  }

  refreshPromise = (async () => {
    try {
      const res = await fetch(`${config.API_URL}/auth/refresh`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        credentials: "include", // Crucial: sends and receives HttpOnly cookies
      });

      if (!res.ok) {
        throw new Error("Refresh token expired or invalid");
      }

      const data = await res.json();
      const token = data.access_token;
      setAccessToken(token);
      return token;
    } catch (error) {
      setAccessToken(null);
      return null;
    } finally {
      refreshPromise = null; // Release lock
    }
  })();

  return refreshPromise;
}

/**
 * Global API client wrapper around standard fetch
 */
export async function apiFetch<T = any>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const headers = new Headers(options.headers);

  // 1. Set default Content-Type to application/json unless it's FormData
  if (!headers.has("Content-Type") && !(options.body instanceof FormData)) {
    headers.set("Content-Type", "application/json");
  }

  // 2. Attach access token from memory if present
  if (accessToken) {
    headers.set("Authorization", `Bearer ${accessToken}`);
  }

  // 3. Build fetch options and handle automatic JSON stringification
  const fetchOptions: RequestInit = {
    ...options,
    headers,
    credentials: "include", // Required for HttpOnly cookies
  };

  // If body is an object/array, stringify it automatically before sending
  if (options.body && typeof options.body === "object" && !(options.body instanceof FormData)) {
    fetchOptions.body = JSON.stringify(options.body);
  }

  // 4. Fire the actual request
  let response = await fetch(`${config.API_URL}${endpoint}`, fetchOptions);

  // 5. Handle token expiration and silent retry
  if (
    response.status === 401 &&
    endpoint !== "/auth/login" &&
    endpoint !== "/auth/refresh"
  ) {
    const token = await refreshAccessToken();

    if (token) {
      headers.set("Authorization", `Bearer ${token}`);
      
      const retryOptions: RequestInit = {
        ...fetchOptions,
        headers,
      };
      
      response = await fetch(`${config.API_URL}${endpoint}`, retryOptions);
    } else {
      // Let the caller handle navigation in the appropriate Next.js context.
      throw new Error("Session expired. Please log in again.");
    }
  }

  // 6. Handle errors cleanly
  if (!response.ok) {
    let errorMessage = `API request failed: ${response.status}`;
    try {
      const errorData = await response.json();
      errorMessage = errorData.detail || errorData.message || errorMessage;
    } catch {
      // Fallback if response is not JSON
    }
    throw new Error(errorMessage);
  }

  // 7. Handle empty responses
  if (response.status === 204) {
    return undefined as T;
  }

  return response.json() as Promise<T>;
}