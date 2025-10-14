import * as React from 'react';
import { FileIcon } from 'lucide-react';
import { ChunkItem } from '../components/chunk-display';
import { Reference, BibliographyItem } from '@/lib/generated-api';
import {
  getConfidenceBadgeClasses,
  getQualityBadgeClasses,
  getRecommendedActionBadgeClasses,
  getReferenceTypeBadgeClasses,
  toTitleCase,
} from '@/lib/badge-styles';

interface CitationReferenceItemProps {
  reference: Reference;
  references: BibliographyItem[];
}

export function CitationReferenceItem({ reference, references }: CitationReferenceItemProps) {
  return (
    <ChunkItem>
      <div className="space-y-2">
        <div className="flex items-start justify-between">
          <h5 className="font-medium text-sm">{reference.title}</h5>
          <div className="flex items-center gap-2 flex-wrap">
            <span className={`px-2 py-1 rounded text-xs ${getReferenceTypeBadgeClasses(reference.type)}`}>
              {reference.type}
            </span>
            {reference.isAlreadyCitedElsewhere && (
              <span className="px-2 py-1 rounded text-xs bg-cyan-100 text-cyan-800">Already cited</span>
            )}
            <span
              className={`px-2 py-1 rounded text-xs ${getRecommendedActionBadgeClasses(reference.recommendedAction)}`}
            >
              {toTitleCase(reference.recommendedAction)}
            </span>
            <span
              className={`px-2 py-1 rounded text-xs ${getConfidenceBadgeClasses(reference.confidenceInRecommendation)}`}
            >
              {toTitleCase(reference.confidenceInRecommendation)} Confidence
            </span>
            <span className={`px-2 py-1 rounded text-xs ${getQualityBadgeClasses(reference.publicationQuality)}`}>
              {toTitleCase(reference.publicationQuality)}
            </span>
          </div>
        </div>

        <div className="text-xs text-muted-foreground">
          <p>
            <strong>Link:</strong>{' '}
            <a
              href={reference.link}
              target="_blank"
              rel="noopener noreferrer"
              className="text-blue-600 hover:underline"
            >
              {reference.link}
            </a>
          </p>
        </div>

        {reference.indexOfAssociatedExistingReference !== -1 && (
          <div className="text-xs">
            <p>
              <strong>Existing Bibliography Reference (#{reference.indexOfAssociatedExistingReference}):</strong>
            </p>
            {references[reference.indexOfAssociatedExistingReference - 1] ? (
              <div className="bg-amber-50 border border-amber-200 rounded p-2 mt-1 space-y-1">
                <p className="text-muted-foreground italic">
                  {references[reference.indexOfAssociatedExistingReference - 1].text}
                </p>
                {references[reference.indexOfAssociatedExistingReference - 1].hasAssociatedSupportingDocument && (
                  <div className="flex items-center gap-1 text-blue-600">
                    <FileIcon className="w-3 h-3" />
                    <span>
                      Has supporting document:{' '}
                      {references[reference.indexOfAssociatedExistingReference - 1].nameOfAssociatedSupportingDocument}
                    </span>
                  </div>
                )}
              </div>
            ) : (
              <p className="text-red-600 text-xs">Reference not found in bibliography</p>
            )}
          </div>
        )}

        <div className="text-xs">
          <p>
            <strong>Bibliography Entry:</strong>
          </p>
          <p className="text-muted-foreground italic">{reference.bibliographyInfo}</p>
        </div>

        <div className="text-xs">
          <p>
            <strong>Related Excerpt (from our document):</strong>
          </p>
          <p className="text-muted-foreground">&quot;{reference.relatedExcerpt}&quot;</p>
        </div>

        <div className="text-xs">
          <p>
            <strong>Related Excerpt (from reference):</strong>
          </p>
          <p className="text-muted-foreground">&quot;{reference.relatedExcerptFromReference}&quot;</p>
        </div>

        <div className="text-xs">
          <p>
            <strong>Rationale:</strong>
          </p>
          <p className="text-muted-foreground">{reference.rationale}</p>
        </div>

        <div className="text-xs">
          <p>
            <strong>Recommended Action:</strong>
          </p>
          <p className="text-muted-foreground">{reference.explanationForRecommendedAction}</p>
        </div>
      </div>
    </ChunkItem>
  );
}
