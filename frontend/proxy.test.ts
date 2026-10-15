// Named `unstable_doesProxyMatch` in the bundled docs, but Next 16.4.1 still exports the old name.
import { unstable_doesMiddlewareMatch } from 'next/experimental/testing/server';
import { describe, expect, it, vi } from 'vitest';
import nextConfig from './next.config';

// The matcher is all that is under test; loading NextAuth's config is not needed for it.
vi.mock('@/auth', () => ({ auth: () => () => undefined }));
const { config } = await import('./proxy');

const matches = (url: string) => unstable_doesMiddlewareMatch({ config, nextConfig, url });

describe('proxy matcher', () => {
  it.each([
    '/',
    '/projects',
    '/projects/0b7c/references?tab=all',
    '/chat',
    '/dashboard',
    '/share/abc123',
    '/addin/sign-in',
    '/api/files/download/0b7c',
  ])('runs on %s', (url) => {
    expect(matches(url)).toBe(true);
  });

  it.each([
    '/_next/static/chunks/main.js',
    '/_next/image?url=%2Flogo.svg&w=64&q=75',
    '/favicon.ico',
    '/icon.svg',
    '/apple-icon.png',
    '/logo_32x32.png',
    '/api/auth/session',
    '/api/auth/callback/google?code=x',
    '/api/health',
  ])('skips %s', (url) => {
    expect(matches(url)).toBe(false);
  });
});
