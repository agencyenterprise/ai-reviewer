import {
  Citation,
  Claim,
  ClaimSubstantiationResultWithClaimIndex,
  ClaimSubstantiatorState,
  BibliographyItem,
} from '@/lib/generated-api';

export enum ClaimCategory {
  NO_CITATION_NEEDED = 'NO_CITATION_NEEDED',
  MISSING_CITATION = 'MISSING_CITATION',
  UNVERIFIABLE_CITATION = 'UNVERIFIABLE_CITATION',
  CONTRADICTORY = 'CONTRADICTORY',
  VERIFIED = 'VERIFIED',
}

export const claimCategoryTitles: Record<ClaimCategory, string> = {
  [ClaimCategory.NO_CITATION_NEEDED]: 'No citation needed',
  [ClaimCategory.MISSING_CITATION]: 'Missing citation',
  [ClaimCategory.UNVERIFIABLE_CITATION]: 'Unverifiable citation',
  [ClaimCategory.CONTRADICTORY]: 'Contradictory claim',
  [ClaimCategory.VERIFIED]: 'Verified claim',
};

export const claimCategoryDescriptions: Record<ClaimCategory, string> = {
  [ClaimCategory.NO_CITATION_NEEDED]: 'The claim does not need a citation.',
  [ClaimCategory.MISSING_CITATION]: 'The claim should be backed up by a reference, but none is provided.',
  [ClaimCategory.UNVERIFIABLE_CITATION]:
    'The claim cites a reference, but the referenced document isn’t available for verification.',
  [ClaimCategory.CONTRADICTORY]: 'The cited reference does not support the claim or directly contradicts it.',
  [ClaimCategory.VERIFIED]: 'The claim is supported by the cited reference.',
};

export const claimCategoryBaseColors: Record<ClaimCategory, 'none' | 'yellow' | 'red' | 'green'> = {
  [ClaimCategory.NO_CITATION_NEEDED]: 'none',
  [ClaimCategory.MISSING_CITATION]: 'yellow',
  [ClaimCategory.UNVERIFIABLE_CITATION]: 'yellow',
  [ClaimCategory.CONTRADICTORY]: 'red',
  [ClaimCategory.VERIFIED]: 'green',
};

export function classifyClaim(
  claim: Claim,
  claimSubstantiation: ClaimSubstantiationResultWithClaimIndex,
  chunkCitations: Citation[],
  references: BibliographyItem[],
): ClaimCategory {
  if (!claim.needsSubstantiation) {
    return ClaimCategory.NO_CITATION_NEEDED;
  }

  if (chunkCitations.length === 0) {
    return ClaimCategory.MISSING_CITATION;
  }

  if (claimSubstantiation.isSubstantiated) {
    return ClaimCategory.VERIFIED;
  }

  const associatedBibliographyIndexes = chunkCitations.map((citation) => citation.indexOfAssociatedBibliography);
  const associatedBibliographyReferencesExists = associatedBibliographyIndexes.map(
    (index) => references[index - 1]?.hasAssociatedSupportingDocument,
  );

  if (!associatedBibliographyReferencesExists.every(Boolean)) {
    return ClaimCategory.UNVERIFIABLE_CITATION;
  } else {
    return ClaimCategory.CONTRADICTORY;
  }
}

// The order of priority for classifying a chunk
// The items that come first in the array are the most important
const chunkClassificationPriorityOrder: ClaimCategory[] = [
  ClaimCategory.CONTRADICTORY,
  ClaimCategory.MISSING_CITATION,
  ClaimCategory.UNVERIFIABLE_CITATION,
  ClaimCategory.VERIFIED,
  ClaimCategory.NO_CITATION_NEEDED,
];

export function classifyChunk(
  results: ClaimSubstantiatorState,
  chunkIndex: number,
  references: BibliographyItem[],
): ClaimCategory {
  const claims = results.claimsByChunk?.[chunkIndex]?.claims || [];
  const citations = results.citationsByChunk?.[chunkIndex]?.citations || [];
  const substantiations = results.claimSubstantiationsByChunk?.[chunkIndex] || [];

  if (claims.length === 0) {
    return ClaimCategory.NO_CITATION_NEEDED;
  }

  const categories = claims.map((claim, claimIndex) =>
    classifyClaim(claim, substantiations[claimIndex] ?? [], citations, references),
  );
  return categories.sort(
    (a, b) => chunkClassificationPriorityOrder.indexOf(a) - chunkClassificationPriorityOrder.indexOf(b),
  )[0];
}
