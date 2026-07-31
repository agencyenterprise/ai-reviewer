import mammoth from 'mammoth';
import { extractText, getDocumentProxy } from 'unpdf';
import { auth } from '@/auth';

// mammoth/unpdf are Node-only; keep this route on the Node.js runtime.
export const runtime = 'nodejs';
export const maxDuration = 30;

const PDF_TYPE = 'application/pdf';
const DOCX_TYPE = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document';

/** Extract plain text from an uploaded PDF or DOCX file. */
export async function POST(req: Request): Promise<Response> {
  const session = await auth();
  if (!session?.user) {
    return new Response('Unauthorized', { status: 401 });
  }

  const form = await req.formData();
  const file = form.get('file');

  if (!(file instanceof File)) {
    return Response.json({ error: 'No file provided.' }, { status: 400 });
  }

  const name = file.name.toLowerCase();
  const isPdf = file.type === PDF_TYPE || name.endsWith('.pdf');
  const isDocx = file.type === DOCX_TYPE || name.endsWith('.docx');

  if (!isPdf && !isDocx) {
    return Response.json({ error: 'Only PDF and DOCX files are supported.' }, { status: 415 });
  }

  const buffer = Buffer.from(await file.arrayBuffer());

  try {
    let text: string;
    if (isPdf) {
      const pdf = await getDocumentProxy(new Uint8Array(buffer));
      const result = await extractText(pdf, { mergePages: true });
      text = Array.isArray(result.text) ? result.text.join('\n\n') : result.text;
    } else {
      const result = await mammoth.extractRawText({ buffer });
      text = result.value;
    }

    text = text.trim();
    if (!text) {
      return Response.json({ error: 'No text could be extracted from the document.' }, { status: 422 });
    }

    return Response.json({ text });
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Unknown error';
    return Response.json({ error: `Failed to extract text: ${message}` }, { status: 500 });
  }
}
