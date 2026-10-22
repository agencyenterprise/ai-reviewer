import { afterEach, describe, expect, it, vi } from 'vitest';
import { featuresApiMicrosoftWordFeaturesGet } from '@/lib/generated-api';
import { flush, renderInto, Rendered, testQueryClient, withQueryClient } from '@/lib/test-render';
import { AddinPane } from './addin-pane';
import type { AddinSession } from './addin-sign-in';

vi.mock('@/lib/generated-api', async (original) => ({
  ...(await original<typeof import('@/lib/generated-api')>()),
  featuresApiMicrosoftWordFeaturesGet: vi.fn(),
}));
// The chat and the Teams list have their own tests; here they only need to be there.
vi.mock('@/components/addin/chat/word-chat', () => ({ WordChat: () => <div>the chat</div> }));
vi.mock('@/components/addin/handoff-panel', () => ({ HandoffList: () => <div>from teams</div> }));

const features = vi.mocked(featuresApiMicrosoftWordFeaturesGet);
const SESSION: AddinSession = { email: 'ana@contoso.com', authorize: async () => 'Bearer t', expire: vi.fn() };

let rendered: Rendered | null = null;

async function render(teams: boolean): Promise<HTMLElement> {
  features.mockResolvedValue({ teams } as Awaited<ReturnType<typeof featuresApiMicrosoftWordFeaturesGet>>);
  rendered = await renderInto(withQueryClient(testQueryClient(), <AddinPane session={SESSION} />));
  await flush();
  return rendered.container;
}

afterEach(async () => {
  await rendered?.unmount();
  rendered = null;
  vi.resetAllMocks();
});

describe('AddinPane', () => {
  it('offers the changes from Teams when the deployment runs the bot', async () => {
    const container = await render(true);

    expect(container.querySelectorAll('[role="tab"]')).toHaveLength(2);
    expect(container.textContent).toContain('the chat');
  });

  it('shows the chat alone when it does not, since nothing can arrive from Teams', async () => {
    const container = await render(false);

    expect(container.querySelectorAll('[role="tab"]')).toHaveLength(0);
    expect(container.textContent).toContain('the chat');
  });
});
