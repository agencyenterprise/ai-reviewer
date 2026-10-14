import { act } from 'react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import {
  exportAnnotationsApiAdminAnnotationsExportGet,
  getNextAnnotationTaskApiAnnotationsSetsSlugNextGet,
  listAnnotatedItemsApiAdminAnnotationsSetsSlugItemsGet,
  type AnnotationTask,
} from '@/lib/generated-api';
import { flush, renderInto, testQueryClient, withQueryClient } from '@/lib/test-render';
import { useAnnotatedItems, useExportAnnotations, useNextAnnotationTask } from './use-annotations';

vi.mock('@/lib/generated-api', async (original) => ({
  ...(await original<typeof import('@/lib/generated-api')>()),
  getNextAnnotationTaskApiAnnotationsSetsSlugNextGet: vi.fn(),
  listAnnotatedItemsApiAdminAnnotationsSetsSlugItemsGet: vi.fn(),
  exportAnnotationsApiAdminAnnotationsExportGet: vi.fn(),
}));

const fetchNext = vi.mocked(getNextAnnotationTaskApiAnnotationsSetsSlugNextGet);
const fetchItems = vi.mocked(listAnnotatedItemsApiAdminAnnotationsSetsSlugItemsGet);
const fetchExport = vi.mocked(exportAnnotationsApiAdminAnnotationsExportGet);

function task(itemId: string): AnnotationTask {
  return {
    set: { slug: 'active_voice', title: 'Active Voice', guidance: '', questions: [] },
    item_id: itemId,
    passage: { document: 'Doc.', anchor: 'Doc', line: 1 },
    item_count: 2,
    answered_by_me: 0,
  };
}

beforeEach(() => vi.resetAllMocks());
afterEach(() => vi.clearAllMocks());

describe('useNextAnnotationTask', () => {
  let shown: string | null | undefined;
  function NextTask() {
    shown = useNextAnnotationTask('active_voice', [], 0).data?.task.item_id;
    return null;
  }

  it('asks the server again when a check is opened a second time', async () => {
    fetchNext.mockResolvedValueOnce(task('first')).mockResolvedValueOnce(task('second'));
    const client = testQueryClient();

    const visit = await renderInto(withQueryClient(client, <NextTask />));
    await flush();
    expect(shown).toBe('first');
    await visit.unmount();
    await flush();

    // Leaving the check and coming back starts at round 0 again. The answered
    // item must not be replayed from the cache.
    const again = await renderInto(withQueryClient(client, <NextTask />));
    await flush();
    expect(fetchNext).toHaveBeenCalledTimes(2);
    expect(shown).toBe('second');
    await again.unmount();
  });
});

describe('useAnnotatedItems', () => {
  function SetItems({ slug }: { slug: string | null }) {
    useAnnotatedItems(slug, false);
    return null;
  }

  it('loads the items of the set on screen, and none before a set is known', async () => {
    fetchItems.mockResolvedValue([]);
    const client = testQueryClient();

    const view = await renderInto(withQueryClient(client, <SetItems slug={null} />));
    await flush();
    expect(fetchItems).not.toHaveBeenCalled();

    await view.rerender(withQueryClient(client, <SetItems slug="advocacy_tone_v2" />));
    await flush();
    expect(fetchItems).toHaveBeenLastCalledWith(
      expect.objectContaining({ path: { slug: 'advocacy_tone_v2' }, query: { only_disagreements: false } }),
    );
    await view.unmount();
  });
});

describe('useExportAnnotations', () => {
  it('fetches every set at once, not one set', async () => {
    fetchExport.mockResolvedValue([]);
    let exportAll!: () => Promise<unknown>;
    function Export() {
      exportAll = useExportAnnotations().mutateAsync;
      return null;
    }

    const view = await renderInto(withQueryClient(testQueryClient(), <Export />));
    await act(async () => exportAll());

    expect(fetchExport).toHaveBeenCalledTimes(1);
    expect(fetchExport).toHaveBeenCalledWith();
    expect(fetchItems).not.toHaveBeenCalled();
    await view.unmount();
  });
});
