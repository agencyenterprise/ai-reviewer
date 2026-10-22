import { PREVIEW_DOCUMENT_URL } from './fake-api';

/**
 * Just enough of Word for the pane preview, once office.js has loaded outside Office:
 * single sign-on hands over a token, and the document has a URL and a .docx to read.
 * Nothing can be written: Word's own API (`Word.run`) is not there, so Apply fails.
 */

const ACCOUNT = 'ana@contoso.com';

function base64Url(value: object): string {
  return btoa(JSON.stringify(value)).replace(/=+$/, '').replace(/\+/g, '-').replace(/\//g, '_');
}

/** An unsigned token with the claims the pane reads; the preview's API never checks it. */
function token(): string {
  const claims = {
    preferred_username: ACCOUNT,
    oid: 'preview-oid',
    tid: 'preview-tid',
    exp: Math.floor(Date.now() / 1000) + 3600,
  };
  return `${base64Url({ alg: 'none' })}.${base64Url(claims)}.preview`;
}

type Callback<T> = (result: { status: string; value: T }) => void;

/** The document as one slice of a few bytes: the preview's API does not open it. */
const file = {
  size: 4,
  sliceCount: 1,
  getSliceAsync: (_index: number, done: Callback<{ data: number[] }>) =>
    done({ status: 'succeeded', value: { data: [80, 75, 3, 4] } }),
  closeAsync: (done: () => void) => done(),
};

export function installFakeOffice(): void {
  const office = Office as unknown as { auth: object; context?: Record<string, unknown>; FileType?: object };
  office.auth = { getAccessToken: async () => token() };
  // Outside Office, office.js leaves out the enums only Word fills in.
  office.FileType ??= { Compressed: 'compressed' };
  // Word's own API, which reads the selection and writes changes, is Word's alone.
  (window as unknown as { Word?: object }).Word ??= {
    run: async () => {
      throw new Error('The preview cannot write to a document: Apply needs Word.');
    },
  };
  office.context ??= {};
  office.context.document = {
    url: PREVIEW_DOCUMENT_URL,
    getFileAsync: (_type: unknown, _options: unknown, done: Callback<typeof file>) =>
      done({ status: 'succeeded', value: file }),
  };
}
