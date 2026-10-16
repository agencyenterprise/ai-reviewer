import { NextResponse } from 'next/server';
import { auth } from '@/auth';
import { REQUEST_PATH_HEADER, requestPath } from '@/lib/sign-in-redirect';

/**
 * Keeps the session cookie fresh, and tells the server layouts which page was asked
 * for, so a signed-out visitor returns there after signing in. The layouts decide who
 * may see a page; this never redirects.
 */
export const proxy = auth((request) => {
  const headers = new Headers(request.headers);
  headers.set(REQUEST_PATH_HEADER, requestPath(request.nextUrl));
  return NextResponse.next({ request: { headers } });
});

export const config = {
  // Everything but build output, files with an extension (public/ and the app icons),
  // and the API routes that never need a session: NextAuth's own and the health check.
  matcher: ['/((?!_next/static/|_next/image|api/auth/|api/health$|.*\\.[a-zA-Z0-9]+$).*)'],
};
