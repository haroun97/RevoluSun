/**
 * Base API client for the RevoluSUN backend.
 *
 * API_BASE comes from VITE_API_URL in the environment (e.g. in .env.local or Vercel).
 * If not set, we fall back to http://localhost:8000 for local development.
 */

const API_BASE =
  typeof import.meta !== "undefined" && import.meta.env?.VITE_API_URL
    ? import.meta.env.VITE_API_URL
    : "http://localhost:8000";

/** GET request to the API; throws if the response is not ok. */
export async function apiGet<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    method: "GET",
    headers: { Accept: "application/json" },
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`API ${path}: ${res.status} ${text || res.statusText}`);
  }
  return res.json() as Promise<T>;
}

/** POST request with a JSON body; throws if the response is not ok. */
export async function apiPost<T, B = object>(path: string, body: B): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Accept: "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`API ${path}: ${res.status} ${text || res.statusText}`);
  }
  return res.json() as Promise<T>;
}

export { API_BASE };
