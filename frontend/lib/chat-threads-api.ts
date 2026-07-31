import { baseUrl } from '@/lib/api';

/**
 * Thin client for the backend chat-thread persistence endpoints
 * (`lib/api/routers/chat.py`). Hand-written (rather than using the generated
 * SDK) so it works before `pnpm run openapi-generate` is re-run against the
 * updated backend. Calls are authenticated with the user's access token.
 */

export interface DbThread {
  id: string;
  title: string | null;
  is_archived: boolean;
  created_at: string;
  last_updated_at: string;
}

export interface DbMessage {
  message_id: string;
  parent_id: string | null;
  content: unknown;
}

async function request(path: string, token: string | undefined, init?: RequestInit): Promise<Response> {
  const response = await fetch(`${baseUrl}${path}`, {
    ...init,
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...init?.headers,
    },
  });
  if (!response.ok) {
    throw new Error(`${init?.method ?? 'GET'} ${path} failed: ${response.status}`);
  }
  return response;
}

export const chatThreadsApi = {
  list: (token: string | undefined) => request('/chat/threads', token).then((r) => r.json() as Promise<DbThread[]>),

  create: (token: string | undefined, title?: string | null) =>
    request('/chat/threads', token, {
      method: 'POST',
      body: JSON.stringify({ title: title ?? null }),
    }).then((r) => r.json() as Promise<DbThread>),

  update: (token: string | undefined, id: string, patch: { title?: string; is_archived?: boolean }) =>
    request(`/chat/threads/${id}`, token, {
      method: 'PATCH',
      body: JSON.stringify(patch),
    }).then((r) => r.json() as Promise<DbThread>),

  remove: (token: string | undefined, id: string) => request(`/chat/threads/${id}`, token, { method: 'DELETE' }),

  listMessages: (token: string | undefined, id: string) =>
    request(`/chat/threads/${id}/messages`, token).then((r) => r.json() as Promise<DbMessage[]>),

  appendMessage: (
    token: string | undefined,
    id: string,
    body: { message_id: string; parent_id: string | null; content: unknown },
  ) => request(`/chat/threads/${id}/messages`, token, { method: 'POST', body: JSON.stringify(body) }),
};
