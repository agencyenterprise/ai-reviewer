import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { act } from 'react';
import {
  AppendMessage,
  AssistantRuntimeProvider,
  useExternalStoreRuntime,
  type ThreadMessageLike,
} from '@assistant-ui/react';
import { listChecksApiMicrosoftWordChatChecksGet, type PaneCheck } from '@/lib/generated-api';
import { flush, renderInto, Rendered, testQueryClient, withQueryClient } from '@/lib/test-render';
import { Thread } from '@/components/assistant-ui/elements/thread.aui';
import { ChecksMenu, CheckSlashPopover } from './pane-checks';
import { AddinSessionContext } from './session-context';

vi.mock('@/lib/generated-api', async (original) => ({
  ...(await original<typeof import('@/lib/generated-api')>()),
  listChecksApiMicrosoftWordChatChecksGet: vi.fn(),
}));

const list = vi.mocked(listChecksApiMicrosoftWordChatChecksGet);
const session = { email: 'ana@contoso.com', authorize: async () => 'Bearer tok', expire: vi.fn() };
const CHECKS: PaneCheck[] = [
  { skill: 'abbreviation-scan', name: 'Abbreviation Scan', description: 'Abbreviations defined?', experimental: false },
  { skill: 'reviewer-2', name: 'Reviewer 2', description: 'A full peer review.', experimental: true },
];

const sent: string[] = [];

function Harness() {
  const runtime = useExternalStoreRuntime<ThreadMessageLike>({
    messages: [],
    convertMessage: (message) => message,
    onNew: async (message: AppendMessage) => {
      sent.push(message.content.map((part) => (part.type === 'text' ? part.text : '')).join(''));
    },
  });
  return (
    <AddinSessionContext.Provider value={session}>
      <AssistantRuntimeProvider runtime={runtime}>
        <Thread components={{ ComposerTools: ChecksMenu, SlashPopover: CheckSlashPopover }} />
      </AssistantRuntimeProvider>
    </AddinSessionContext.Provider>
  );
}

let rendered: Rendered | null = null;

async function click(element: Element | null | undefined): Promise<void> {
  if (!element) throw new Error(`nothing to click in: ${document.body.textContent}`);
  await act(async () => (element as HTMLElement).click());
  await flush();
}

function byText(text: string): Element | undefined {
  return [...document.querySelectorAll('[cmdk-item], button')].find((el) => el.textContent?.includes(text));
}

beforeEach(async () => {
  sent.length = 0;
  // cmdk and Radix measure and scroll; jsdom does neither.
  vi.stubGlobal(
    'ResizeObserver',
    class {
      observe() {}
      unobserve() {}
      disconnect() {}
    },
  );
  Element.prototype.scrollIntoView = () => {};
  list.mockResolvedValue(CHECKS);
  rendered = await renderInto(withQueryClient(testQueryClient(), <Harness />));
  await flush();
});

afterEach(async () => {
  await rendered?.unmount();
  rendered = null;
  vi.unstubAllGlobals();
  vi.resetAllMocks();
});

describe('the checks in the pane composer', () => {
  it('asks for the checks as the signed-in account', () => {
    expect(list).toHaveBeenCalledWith({ headers: { Authorization: 'Bearer tok' } });
  });

  it('a check picked from the list is sent straight away, by name and skill', async () => {
    await click(document.querySelector('button[aria-label="Run a check"]'));
    await click(byText('Reviewer 2'));

    expect(sent).toEqual(['Run the Reviewer 2 check on this document (the "reviewer-2" skill).']);
  });
});
