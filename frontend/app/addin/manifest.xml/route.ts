import { addinManifest } from '@/lib/addin/manifest';
import packageJson from '@/package.json';
import { NextRequest } from 'next/server';

/**
 * The Word add-in's manifest for this deployment: the URL an admin gives Microsoft 365
 * to publish the add-in (`microsoft/word-addin/README.md`).
 *
 * Refused until the deployment signs in with Microsoft, since the add-in cannot sign
 * anyone in without that app.
 */
export function GET(request: NextRequest) {
  const clientId = process.env.AUTH_MICROSOFT_ENTRA_ID_ID?.trim();
  if (!clientId) {
    return new Response('Set AUTH_MICROSOFT_ENTRA_ID_ID first: the add-in signs in with that Entra app.\n', {
      status: 503,
      headers: { 'Content-Type': 'text/plain; charset=utf-8' },
    });
  }
  const manifest = addinManifest({ frontendUrl: publicOrigin(request), clientId, version: packageJson.version });
  return new Response(manifest, {
    headers: { 'Content-Type': 'application/xml; charset=utf-8', 'Cache-Control': 'no-store' },
  });
}

/**
 * The address people reach this frontend at. `AUTH_URL` when set, as Auth.js reads it;
 * otherwise what the proxy in front reports, since the request itself may arrive over
 * plain HTTP on an internal host.
 */
function publicOrigin(request: NextRequest): string {
  const configured = process.env.AUTH_URL?.trim();
  if (configured) return configured;
  const forwarded = (name: string) => request.headers.get(name)?.split(',')[0].trim();
  const host = forwarded('x-forwarded-host') ?? request.headers.get('host') ?? request.nextUrl.host;
  const protocol = forwarded('x-forwarded-proto') ?? request.nextUrl.protocol.replace(':', '');
  return `${protocol}://${host}`;
}
