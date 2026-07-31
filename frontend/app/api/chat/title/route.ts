import { openai } from '@ai-sdk/openai';
import { generateText, type ModelMessage } from 'ai';

export const maxDuration = 15;

interface TitleRequest {
  messages: ModelMessage[];
}

/** Generate a short thread title from the opening messages. */
export async function POST(req: Request): Promise<Response> {
  const { messages }: TitleRequest = await req.json();

  if (!process.env.OPENAI_API_KEY) {
    return Response.json({ title: 'New chat' });
  }

  try {
    const { text } = await generateText({
      model: openai('gpt-4.1'),
      system:
        'Generate a short, specific title (3 to 6 words) for this conversation. ' +
        'Respond with only the title text: no quotes, no trailing punctuation.',
      messages,
    });
    const title =
      text
        .trim()
        .replace(/^["']|["']$/g, '')
        .slice(0, 80) || 'New chat';
    return Response.json({ title });
  } catch {
    return Response.json({ title: 'New chat' });
  }
}
