/**
 * The open document as the chat sends it: the .docx itself, read through Office.js,
 * images and all.
 *
 * Sent only when it changed since it was last sent in this conversation, so a quick
 * follow-up does not upload the document again. The backend keeps the copy it has
 * otherwise (`lib/agents/word_chat_agent.py`).
 */

/** The most Office hands over per slice. */
const SLICE = 4 * 1024 * 1024;

function openFile(): Promise<Office.File> {
  return new Promise((resolve, reject) =>
    Office.context.document.getFileAsync(Office.FileType.Compressed, { sliceSize: SLICE }, (result) =>
      result.status === Office.AsyncResultStatus.Succeeded ? resolve(result.value) : reject(result.error),
    ),
  );
}

function readSlice(file: Office.File, index: number): Promise<number[]> {
  return new Promise((resolve, reject) =>
    file.getSliceAsync(index, (result) =>
      result.status === Office.AsyncResultStatus.Succeeded ? resolve(result.value.data) : reject(result.error),
    ),
  );
}

/**
 * The open document as a .docx, as it is on screen: Word saves any pending edit first,
 * which is why this can take a couple of seconds after typing. Office allows one open
 * file at a time, so it is always closed again.
 */
export async function documentFile(): Promise<Blob> {
  const file = await openFile();
  try {
    const slices: Uint8Array<ArrayBuffer>[] = [];
    for (let i = 0; i < file.sliceCount; i++) slices.push(new Uint8Array(await readSlice(file, i)));
    return new Blob(slices, { type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' });
  } finally {
    file.closeAsync();
  }
}

/** The text selected in Word, or an empty string. */
export async function selectedText(): Promise<string> {
  return Word.run(async (context) => {
    const selection = context.document.getSelection();
    selection.load('text');
    await context.sync();
    return String(selection.text ?? '').trim();
  });
}

/** A short fingerprint of the file, to tell whether it changed since it was sent. */
export async function fingerprint(file: Blob): Promise<string> {
  const digest = await crypto.subtle.digest('SHA-256', await file.arrayBuffer());
  return [...new Uint8Array(digest)].map((byte) => byte.toString(16).padStart(2, '0')).join('');
}

const PANE_KEY = 'draft-detective:unsaved-document';
let paneKeyFallback: string | null = null;

/**
 * What the chat knows this document by: the URL Word reports, or, for a document never
 * saved, a key of this pane's own. Word gives an unsaved document no URL, so without one
 * every unsaved document of an account would share one conversation and one copy of the
 * document. Kept in sessionStorage so reloading the pane keeps the conversation; where
 * that is unavailable, for as long as the pane is open.
 */
export function chatDocumentKey(url: string): string {
  if (url.trim()) return url;
  try {
    let key = sessionStorage.getItem(PANE_KEY);
    if (!key) {
      key = crypto.randomUUID();
      sessionStorage.setItem(PANE_KEY, key);
    }
    return `unsaved:${key}`;
  } catch {
    paneKeyFallback ??= crypto.randomUUID();
    return `unsaved:${paneKeyFallback}`;
  }
}
