import * as React from 'react';
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from '@/components/ui/accordion';
import { Link as LinkIcon } from 'lucide-react';
import { CitationSuggestionResultWithClaimIndexOutput, BibliographyItem } from '@/lib/generated-api';
import { scoreReference } from '@/lib/reference-scoring';
import { CitationReferenceItem } from './citation-reference-item';

interface ChunkCitationSuggestionsProps {
  suggestions: CitationSuggestionResultWithClaimIndexOutput[];
  references: BibliographyItem[];
}

export function ChunkCitationSuggestions({ suggestions, references }: ChunkCitationSuggestionsProps) {
  if (!suggestions || suggestions.length === 0) {
    return null;
  }

  return (
    <Accordion type="single" collapsible className="border rounded-lg">
      <AccordionItem value="suggestions" className="border-none">
        <AccordionTrigger className="px-4 py-2 hover:no-underline">
          <div className="flex items-center gap-2">
            <LinkIcon className="w-4 h-4 text-purple-600" />
            <span className="font-bold">Citation Suggestions ({suggestions.length})</span>
            <span className="text-xs text-muted-foreground font-normal">
              {suggestions.reduce((sum, s) => sum + (s.relevantReferences?.length || 0), 0)} total references
            </span>
          </div>
        </AccordionTrigger>
        <AccordionContent className="px-4 pb-4">
          <div className="space-y-4">
            {suggestions.map((suggestion, si) => {
              const sortedRefs = [...(suggestion.relevantReferences || [])].sort(
                (a, b) => scoreReference(b) - scoreReference(a),
              );
              return (
                <div key={si} className="space-y-3">
                  <div className="text-sm text-muted-foreground">
                    <strong>
                      Claim {suggestion.claimIndex !== undefined ? suggestion.claimIndex + 1 : 'Unknown'}:
                    </strong>{' '}
                    {suggestion.rationale}
                  </div>
                  <div className="space-y-3">
                    {sortedRefs.map((reference, ri) => (
                      <CitationReferenceItem key={ri} reference={reference} references={references} />
                    ))}
                  </div>
                </div>
              );
            })}
          </div>
        </AccordionContent>
      </AccordionItem>
    </Accordion>
  );
}
