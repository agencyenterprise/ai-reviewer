import { describe, expect, it } from 'vitest';
import type { AnnotationSetStats } from '@/lib/generated-api';
import { annotationsExportFile, currentSetSlug } from './annotation-results-derive';

function stats(slug: string): AnnotationSetStats {
  return {
    slug,
    title: slug,
    item_count: 10,
    annotated_items: 0,
    annotation_count: 0,
    annotator_count: 0,
    agreements: 0,
    disagreements: 0,
    abstentions: 0,
  };
}

describe('currentSetSlug', () => {
  const sets = [stats('active_voice'), stats('advocacy_tone_v2')];

  it('shows the first set until one is picked', () => {
    expect(currentSetSlug(sets, null)).toBe('active_voice');
  });

  it('shows the set the admin picked', () => {
    expect(currentSetSlug(sets, 'advocacy_tone_v2')).toBe('advocacy_tone_v2');
  });

  it('shows nothing while the sets load or when there are none', () => {
    expect(currentSetSlug(undefined, null)).toBeNull();
    expect(currentSetSlug([], null)).toBeNull();
  });
});

describe('annotationsExportFile', () => {
  it('puts every set in one JSON file named for the day', async () => {
    const everySet = ['active_voice', 'advocacy_tone_v2'].map((slug) => ({
      slug,
      title: slug,
      workflow_type: slug,
      is_active: true,
      questions: [],
      items: [],
    }));

    const { filename, blob } = annotationsExportFile(everySet, new Date('2026-10-14T23:30:00Z'));

    expect(filename).toBe('annotations-2026-10-14.json');
    expect(blob.type).toBe('application/json');
    expect(JSON.parse(await blob.text()).map((set: { slug: string }) => set.slug)).toEqual([
      'active_voice',
      'advocacy_tone_v2',
    ]);
  });
});
