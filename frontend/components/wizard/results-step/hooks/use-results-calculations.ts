import { DetailedResults } from "../../types"

export function useResultsCalculations(detailedResults: DetailedResults | undefined) {
    if (!detailedResults) {
        return {
            totalClaims: 0,
            totalCitations: 0,
            totalUnsubstantiated: 0,
            totalChunks: 0,
            chunksWithClaims: 0,
            chunksWithCitations: 0,
            supportedReferences: 0
        }
    }

    const totalClaims = detailedResults.claims_by_chunk.reduce(
        (sum, chunk) => sum + chunk.claims.length,
        0
    )

    const totalCitations = detailedResults.citations_by_chunk.reduce(
        (sum, chunk) => sum + chunk.citations.length,
        0
    )

    const totalUnsubstantiated = detailedResults.claim_substantiations_by_chunk.reduce(
        (sum, chunk) => sum + chunk.filter(sub => !sub.is_substantiated).length,
        0
    )

    const chunksWithClaims = detailedResults.claims_by_chunk.filter(
        chunk => chunk.claims.length > 0
    ).length

    const chunksWithCitations = detailedResults.citations_by_chunk.filter(
        chunk => chunk.citations.length > 0
    ).length

    const supportedReferences = detailedResults.references.filter(
        ref => ref.has_associated_supporting_document
    ).length

    const totalChunks = Math.max(
        detailedResults.claims_by_chunk.length,
        detailedResults.citations_by_chunk.length
    )

    return {
        totalClaims,
        totalCitations,
        totalUnsubstantiated,
        totalChunks,
        chunksWithClaims,
        chunksWithCitations,
        supportedReferences
    }
}
