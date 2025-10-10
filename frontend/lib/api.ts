import { Configuration, DefaultApi } from './generated-api';

export const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export const api = new DefaultApi(
  new Configuration({
    basePath: apiUrl,
  }),
);
