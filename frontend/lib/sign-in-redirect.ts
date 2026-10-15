/**
 * Sending a signed-out visitor to sign in, and back to the page they asked for.
 *
 * Server layouts cannot see the request URL, so `proxy.ts` copies the path and query
 * into a request header that the layouts read.
 */

/** The request header `proxy.ts` sets to the path and query of the page requested. */
export const REQUEST_PATH_HEADER = 'x-pathname';

/** The value `proxy.ts` puts in `REQUEST_PATH_HEADER` for a request URL. */
export function requestPath(url: URL): string {
  return `${url.pathname}${url.search}`;
}

/** A path on this origin: `//host` and `/\host` are other origins to a browser. */
function isLocalPath(path: string | null | undefined): path is string {
  return !!path && path.startsWith('/') && !path.startsWith('//') && !path.startsWith('/\\');
}

/** The sign-in URL that returns to `path` afterwards, or home when `path` is not local. */
export function signInUrl(path: string | null | undefined): string {
  return `/api/auth/signin?callbackUrl=${encodeURIComponent(isLocalPath(path) ? path : '/')}`;
}
