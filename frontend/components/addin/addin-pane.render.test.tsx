import { afterEach, describe, expect, it, vi } from 'vitest';
import { act } from 'react';
import { featuresApiMicrosoftWordFeaturesGet, type HandoffView } from '@/lib/generated-api';
import { flush, renderInto, Rendered, testQueryClient, withQueryClient } from '@/lib/test-render';
import { AddinPane } from './addin-pane';
import type { AddinSession } from './addin-sign-in';
import { usePendingHandoffs } from './handoff-panel';

vi.mock('@/lib/generated-api', async (original) => ({
  ...(await original<typeof import('@/lib/generated-api')>()),
  featuresApiMicrosoftWordFeaturesGet: vi.fn(),
}));
// The chat and the Teams list have their own tests; here they only need to be there.
vi.mock('@/components/addin/chat/word-chat', () => ({ WordChat: () => <div>the chat</div> }));
vi.mock('@/components/addin/handoff-panel', () => ({
  HandoffList: () => <div>the teams list</div>,
  usePendingHandoffs: vi.fn(),
}));

const features = vi.mocked(featuresApiMicrosoftWordFeaturesGet);
const pending = vi.mocked(usePendingHandoffs);
const SESSION: AddinSession = { email: 'ana@contoso.com', authorize: async () => 'Bearer t', expire: vi.fn() };
const HERE = { document_url: 'a', document_name: 'Draft.docx' } as HandoffView;

let rendered: Rendered | null = null;

async function render(teams: boolean, here: HandoffView[]): Promise<HTMLElement> {
  features.mockResolvedValue({ teams } as Awaited<ReturnType<typeof featuresApiMicrosoftWordFeaturesGet>>);
  pending.mockReturnValue({ data: { here, elsewhere: [] } } as unknown as ReturnType<typeof usePendingHandoffs>);
  rendered = await renderInto(withQueryClient(testQueryClient(), <AddinPane session={SESSION} />));
  await flush();
  return rendered.container;
}

function click(container: HTMLElement, label: string) {
  const button = [...container.querySelectorAll('button')].find((b) => b.textContent?.includes(label));
  if (!button) throw new Error(`no ${label} button`);
  return act(async () => button.click());
}

const visible = (container: HTMLElement, text: string) =>
  [...container.querySelectorAll('div')].some((node) => node.textContent === text && !node.closest('.hidden'));

afterEach(async () => {
  await rendered?.unmount();
  rendered = null;
  vi.resetAllMocks();
});

describe('AddinPane', () => {
  it('says what waits from Teams, and opens it in place of the chat until asked back', async () => {
    const container = await render(true, [HERE, HERE]);
    expect(container.textContent).toContain('2 suggestions from Teams for this document');

    await click(container, 'Review');
    expect(visible(container, 'the teams list')).toBe(true);
    expect(visible(container, 'the chat')).toBe(false);

    await click(container, 'Chat');
    expect(visible(container, 'the chat')).toBe(true);
    expect(container.textContent).not.toContain('the teams list');
  });

  it('takes no room when nothing waits', async () => {
    const container = await render(true, []);

    expect(container.querySelectorAll('button')).toHaveLength(0);
    expect(visible(container, 'the chat')).toBe(true);
  });

  it('still looks for what waits from Teams when it cannot tell whether the bot runs', async () => {
    features.mockRejectedValue(new Error('502'));
    pending.mockReturnValue({ data: { here: [HERE], elsewhere: [] } } as unknown as ReturnType<
      typeof usePendingHandoffs
    >);
    rendered = await renderInto(withQueryClient(testQueryClient(), <AddinPane session={SESSION} />));
    await flush();

    expect(rendered.container.textContent).toContain('1 suggestion from Teams for this document');
  });

  it('never mentions Teams where the deployment does not run the bot', async () => {
    const container = await render(false, [HERE]);

    expect(container.textContent).not.toContain('from Teams');
    expect(visible(container, 'the chat')).toBe(true);
  });
});
