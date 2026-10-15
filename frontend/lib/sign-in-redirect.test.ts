import { describe, expect, it } from 'vitest';
import { requestPath, signInUrl } from './sign-in-redirect';

describe('requestPath', () => {
  it('keeps the query', () => {
    expect(requestPath(new URL('http://localhost:3000/projects/abc/references?tab=x&y=1'))).toBe(
      '/projects/abc/references?tab=x&y=1',
    );
  });
});

describe('signInUrl', () => {
  it('returns to the requested path and query', () => {
    const url = new URL(signInUrl('/projects/abc/references?tab=x&y=1'), 'http://localhost');
    expect(url.pathname).toBe('/api/auth/signin');
    expect(url.searchParams.get('callbackUrl')).toBe('/projects/abc/references?tab=x&y=1');
  });

  it.each([null, undefined, '', 'https://evil.example/x', '//evil.example/x', '/\\evil.example/x'])(
    'returns home for %j',
    (path) => {
      expect(new URL(signInUrl(path), 'http://localhost').searchParams.get('callbackUrl')).toBe('/');
    },
  );
});
