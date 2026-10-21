import { afterEach, describe, expect, it, vi } from 'vitest';

// serverApiUrl is read from the env when the module loads, so each case stubs the env
// and loads a fresh copy.
async function serverApiUrlWith(internalUrl: string | undefined, publicUrl: string | undefined) {
  vi.stubEnv('API_INTERNAL_URL', internalUrl);
  vi.stubEnv('NEXT_PUBLIC_API_URL', publicUrl);
  vi.resetModules();
  return (await import('./server-api-url')).serverApiUrl;
}

describe('serverApiUrl', () => {
  afterEach(() => {
    vi.unstubAllEnvs();
  });

  it.each([
    ['http://api:8000', 'https://api.example.com', 'http://api:8000'],
    ['http://api:8000/', 'https://api.example.com', 'http://api:8000'],
    [undefined, 'https://api.example.com/', 'https://api.example.com'],
    ['', 'https://api.example.com', 'https://api.example.com'],
    [undefined, undefined, 'http://localhost:8000'],
  ])('with API_INTERNAL_URL %s and NEXT_PUBLIC_API_URL %s calls %s', async (internalUrl, publicUrl, expected) => {
    expect(await serverApiUrlWith(internalUrl, publicUrl)).toBe(expected);
  });
});
