import { DocumentChunkOutput, EvidenceAlignmentLevel } from './generated-api';

export enum SeverityLevel {
  None = 'none',
  Low = 'low',
  Medium = 'medium',
  High = 'high',
  Good = 'good',
}

export function getSeverity(chunk: DocumentChunkOutput) {
  const substantiations = chunk.substantiations || [];
  const needsSubstantiation = chunk.claimCommonKnowledgeResults || [];

  if (substantiations.length === 0) {
    if (needsSubstantiation.some((result) => result.needsSubstantiation)) {
      return SeverityLevel.Medium;
    }
    return SeverityLevel.None;
  }

  if (
    substantiations.some((substantiation) => substantiation.evidenceAlignment === EvidenceAlignmentLevel.Unsupported)
  ) {
    return SeverityLevel.High;
  }

  if (
    substantiations.some(
      (substantiation) => substantiation.evidenceAlignment === EvidenceAlignmentLevel.PartiallySupported,
    )
  ) {
    return SeverityLevel.Medium;
  }

  if (
    substantiations.some((substantiation) => substantiation.evidenceAlignment === EvidenceAlignmentLevel.Unverifiable)
  ) {
    return SeverityLevel.Low;
  }

  if (substantiations.some((substantiation) => substantiation.evidenceAlignment === EvidenceAlignmentLevel.Supported)) {
    return SeverityLevel.Good;
  }

  return SeverityLevel.None;
}

export const severityColors: Record<SeverityLevel, 'none' | 'yellow' | 'red' | 'green' | 'blue'> = {
  [SeverityLevel.None]: 'none',
  [SeverityLevel.Low]: 'blue',
  [SeverityLevel.Medium]: 'yellow',
  [SeverityLevel.High]: 'red',
  [SeverityLevel.Good]: 'green',
};
