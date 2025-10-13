import { ClaimSubstantiatorStateOutput, EvidenceAlignmentLevel } from '@/lib/generated-api';

export function useResultsCalculations(detailedResults: ClaimSubstantiatorStateOutput | undefined) {
  if (!detailedResults) {
    return {
      totalClaims: 0,
      totalCitations: 0,
      totalUnsubstantiated: 0,
      totalChunks: 0,
      chunksWithClaims: 0,
      chunksWithCitations: 0,
      supportedReferences: 0,
    };
  }

  const totalClaims = detailedResults.chunks?.reduce((sum, chunk) => sum + (chunk.claims?.claims?.length || 0), 0) || 0;

  const totalCitations =
    detailedResults.chunks?.reduce((sum, chunk) => sum + (chunk.citations?.citations?.length || 0), 0) || 0;

  const totalUnsubstantiated =
    detailedResults.chunks?.reduce(
      (sum, chunk) =>
        sum +
        (chunk.substantiations?.filter(
          (sub) =>
            sub.evidenceAlignment === EvidenceAlignmentLevel.Unsupported ||
            sub.evidenceAlignment === EvidenceAlignmentLevel.Contradicted,
        ).length || 0),
      0,
    ) || 0;

  const chunksWithClaims =
    detailedResults.chunks?.filter((chunk) => (chunk.claims?.claims?.length || 0) > 0).length || 0;

  const chunksWithCitations =
    detailedResults.chunks?.filter((chunk) => (chunk.citations?.citations?.length || 0) > 0).length || 0;

  const supportedReferences =
    detailedResults.references?.filter((ref) => ref.hasAssociatedSupportingDocument).length || 0;

  const totalChunks = Math.max(detailedResults.chunks?.length || 0, detailedResults.chunks?.length || 0);

  return {
    totalClaims,
    totalCitations,
    totalUnsubstantiated,
    totalChunks,
    chunksWithClaims,
    chunksWithCitations,
    supportedReferences,
  };
}
