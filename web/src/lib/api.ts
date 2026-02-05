export type ApiError = { detail?: string };

const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000";

async function handleError(res: Response): Promise<never> {
  let payload: ApiError | undefined;
  try {
    payload = (await res.json()) as ApiError;
  } catch {
    payload = undefined;
  }
  const msg = payload?.detail || `${res.status} ${res.statusText}`;
  throw new Error(msg);
}

export async function postJSON<T>(
  path: string,
  body: unknown
): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) return handleError(res);
  return (await res.json()) as T;
}

export async function postBlob(
  path: string,
  body: unknown
): Promise<Blob> {
  const res = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) return handleError(res);
  return await res.blob();
}

