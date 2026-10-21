import { baseUrl } from '@/lib/api';

// Server code (route handlers, server components) calls the API at API_INTERNAL_URL when
// it's set. Unlike NEXT_PUBLIC_API_URL, which the build inlines, it's read when the server
// starts, so a cluster can point it at the API's internal address (`http://api:8000`).
// Without it, server code uses the browser's URL.
export const serverApiUrl = process.env.API_INTERNAL_URL?.replace(/\/+$/, '') || baseUrl;
