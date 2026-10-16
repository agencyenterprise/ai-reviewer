import { describe, expect, it } from 'vitest';
import { WorkflowRunType } from '@/lib/generated-api';
import { applyPreset, presetIsActive, presetOfferedCount } from './workflow-presets';

const { ActiveVoice, AdvocacyToneV2, ReferenceValidationV2, RecommendationCheck, ConcisionPrecision } = WorkflowRunType;

const EDITORIAL = [AdvocacyToneV2, ActiveVoice, ConcisionPrecision];
const OFFERED = [ReferenceValidationV2, RecommendationCheck, AdvocacyToneV2, ActiveVoice, ConcisionPrecision];

describe('presetIsActive', () => {
  it('is active when the selection is exactly the preset', () => {
    expect(presetIsActive(EDITORIAL, [ActiveVoice, ConcisionPrecision, AdvocacyToneV2], OFFERED)).toBe(true);
  });

  it('is not active for a subset or a superset of the preset', () => {
    expect(presetIsActive(EDITORIAL, [ActiveVoice, AdvocacyToneV2], OFFERED)).toBe(false);
    expect(presetIsActive(EDITORIAL, [...EDITORIAL, ReferenceValidationV2], OFFERED)).toBe(false);
  });

  it('ignores assessments the picker is not offering, on both sides', () => {
    // Concision is hidden for this user: the preset shrinks to what is on offer.
    const offered = [ReferenceValidationV2, AdvocacyToneV2, ActiveVoice];
    expect(presetIsActive(EDITORIAL, [ActiveVoice, AdvocacyToneV2], offered)).toBe(true);
    // A seeded type with no row neither confirms nor breaks the match.
    expect(presetIsActive(EDITORIAL, [ActiveVoice, AdvocacyToneV2, ConcisionPrecision], offered)).toBe(true);
  });

  it('is never active for a preset with nothing on offer', () => {
    expect(presetIsActive(EDITORIAL, [], [ReferenceValidationV2])).toBe(false);
  });
});

describe('applyPreset', () => {
  it('replaces the offered part of the selection with the preset', () => {
    expect(applyPreset(EDITORIAL, [ReferenceValidationV2, RecommendationCheck], OFFERED)).toEqual(EDITORIAL);
  });

  it('keeps a seeded type the picker does not list', () => {
    const offered = [ReferenceValidationV2, AdvocacyToneV2, ActiveVoice];
    expect(applyPreset(EDITORIAL, [ConcisionPrecision, ReferenceValidationV2], offered)).toEqual([
      ConcisionPrecision,
      AdvocacyToneV2,
      ActiveVoice,
    ]);
  });

  it('drops preset assessments that are not on offer', () => {
    expect(applyPreset(EDITORIAL, [], [AdvocacyToneV2])).toEqual([AdvocacyToneV2]);
  });
});

describe('presetOfferedCount', () => {
  it('counts the preset assessments the picker offers', () => {
    expect(presetOfferedCount(EDITORIAL, OFFERED)).toBe(3);
    expect(presetOfferedCount([ReferenceValidationV2, AdvocacyToneV2, RecommendationCheck], OFFERED)).toBe(3);
  });

  it('leaves out the ones it does not', () => {
    expect(presetOfferedCount(EDITORIAL, [ReferenceValidationV2, AdvocacyToneV2])).toBe(1);
  });
});
