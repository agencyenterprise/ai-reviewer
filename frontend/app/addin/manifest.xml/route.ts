import { addinManifest, DEFAULT_ADDIN_NAME } from '@/lib/addin/manifest';
import packageJson from '@/package.json';
import { NextRequest } from 'next/server';

// Sign in with Microsoft: the add-in signs in with this app, and the API turns its
// tokens down unless all three are set (`lib/api/addin_auth.py`).
const SIGN_IN_SETTINGS = [
  'AUTH_MICROSOFT_ENTRA_ID_ID',
  'AUTH_MICROSOFT_ENTRA_ID_SECRET',
  'AUTH_MICROSOFT_ENTRA_ID_ISSUER',
] as const;

/**
 * The Word add-in's manifest for this deployment: the URL an admin gives Microsoft 365
 * to publish the add-in (`docs/microsoft-integrations.md`).
 *
 * Refused until the deployment signs in with Microsoft, so an add-in that could sign
 * nobody in is never published.
 */
export function GET(request: NextRequest) {
  const missing = SIGN_IN_SETTINGS.filter((name) => !process.env[name]?.trim());
  if (missing.length > 0) {
    return new Response(`Set ${missing.join(', ')} first: the add-in signs in with Microsoft.\n`, {
      status: 503,
      headers: { 'Content-Type': 'text/plain; charset=utf-8' },
    });
  }
  const clientId = process.env.AUTH_MICROSOFT_ENTRA_ID_ID!.trim();
  const manifest = addinManifest({
    frontendUrl: publicOrigin(request),
    clientId,
    version: packageJson.version,
    name: process.env.ADDIN_NAME?.trim() || DEFAULT_ADDIN_NAME,
  });
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
