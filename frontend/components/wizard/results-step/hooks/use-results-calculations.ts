import { ClaimSubstantiatorState } from '@/lib/generated-api';

export function useResultsCalculations(detailedResults: ClaimSubstantiatorState | undefined) {
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

  const totalClaims = detailedResults.claimsByChunk?.reduce((sum, chunk) => sum + chunk.claims.length, 0) || 0;

  const totalCitations = detailedResults.citationsByChunk?.reduce((sum, chunk) => sum + chunk.citations.length, 0) || 0;

  const totalUnsubstantiated =
    detailedResults.claimSubstantiationsByChunk?.reduce(
      (sum, chunk) => sum + chunk.filter((sub) => !sub.isSubstantiated).length,
      0,
    ) || 0;

  const chunksWithClaims = detailedResults.claimsByChunk?.filter((chunk) => chunk.claims.length > 0).length || 0;

  const chunksWithCitations =
    detailedResults.citationsByChunk?.filter((chunk) => chunk.citations.length > 0).length || 0;

  const supportedReferences =
    detailedResults.references?.filter((ref) => ref.hasAssociatedSupportingDocument).length || 0;

  const totalChunks = Math.max(
    detailedResults.claimsByChunk?.length || 0,
    detailedResults.citationsByChunk?.length || 0,
  );

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
