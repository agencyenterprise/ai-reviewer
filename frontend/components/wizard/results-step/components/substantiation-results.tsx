'use client';

import { Button } from '@/components/ui/button';
import { BibliographyItem, ClaimSubstantiationResultWithClaimIndex, FileDocument } from '@/lib/generated-api';
import { cn } from '@/lib/utils';
import { ChevronDown, ChevronRight, FileSearch } from 'lucide-react';
import { useState } from 'react';
import { EvidenceAlignmentLevelBadge } from './evidence-alignment-level-badge';
import Link from 'next/link';
import { apiUrl } from '@/lib/api';

interface SubstantiationResultsProps {
  substantiation: ClaimSubstantiationResultWithClaimIndex;
  references: BibliographyItem[];
  supportingFiles: FileDocument[];
  className?: string;
}

export function SubstantiationResults({
  substantiation,
  references,
  supportingFiles,
  className = '',
}: SubstantiationResultsProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  return (
    <div className={cn('border-b pb-2 space-y-4', className)}>
      <div className="space-y-1">
        <div className="flex items-center justify-between">
          <h3 className="flex items-center gap-2 font-semibold">
            <FileSearch className="h-4 w-4" />
            Claim-Reference Validation
          </h3>

          <Button
            variant="ghost"
            size="xs"
            className="text-gray-600 hover:text-gray-900"
            onClick={() => setIsExpanded(!isExpanded)}
          >
            {isExpanded ? (
              <>
                <ChevronDown />
                Hide Details
              </>
            ) : (
              <>
                <ChevronRight />
                Show Details
              </>
            )}
          </Button>
        </div>

        <EvidenceAlignmentLevelBadge evidenceAlignment={substantiation.evidenceAlignment} variant="solid" />
      </div>

      {isExpanded && (
        <div className="space-y-2">
          <p>
            <span className="font-medium">Evidence Alignment:</span> {substantiation.evidenceAlignment}
          </p>
          <p>
            <span className="font-medium">Rationale:</span> {substantiation.rationale}
          </p>
          <p>
            <span className="font-medium">Feedback to resolve:</span> {substantiation.feedback}
          </p>
          <h4 className="font-medium">Evidence sources:</h4>
          {substantiation.evidenceSources.length === 0 && (
            <p className="text-muted-foreground">No evidence sources found.</p>
          )}
          {substantiation.evidenceSources.map((source, index) => {
            const matchedReference = references.find(
              (reference) => reference.nameOfAssociatedSupportingDocument === source.referenceFileName,
            );
            const matchedFile = supportingFiles.find((file) => file.fileName === source.referenceFileName);

            return (
              <div key={index} className="bg-muted p-3 rounded-md leading-relaxed space-y-1">
                <p className="font-medium">
                  Source {index + 1} of {substantiation.evidenceSources.length}
                </p>
                <p>
                  <span className="font-medium">Reference:</span>{' '}
                  <Link
                    href={`${apiUrl}/api/files/download/${matchedFile?.filePath.split('/').pop()}/${matchedFile?.fileName}`}
                    target="_blank"
                    className="text-blue-600 underline"
                  >
                    {source.referenceFileName}
                  </Link>{' '}
                  <span className="text-muted-foreground"> - {matchedReference?.text}</span>
                </p>
                <p>
                  <span className="font-medium">Location:</span> {source.location}
                </p>
                <p>
                  <span className="font-medium">Quote:</span> <span className="italic">&quot;{source.quote}&quot;</span>
                </p>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
