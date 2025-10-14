'use client';

import { Badge } from '@/components/ui/badge';
import { Card, CardContent } from '@/components/ui/card';
import { BibliographyItem } from '@/lib/generated-api';
import { DocumentChunk } from '@/lib/generated-api/models/DocumentChunk';
import { Link, MessageCirclePlus } from 'lucide-react';
import { ExpandableResultSection } from './expandable-result-section';
import { AiGeneratedLabel } from '@/components/ai-generated-label';

export interface ChunkAnalysisCardProps {
  chunk: DocumentChunk;
  references: BibliographyItem[];
}

export function ChunkAnalysisCard({ chunk, references }: ChunkAnalysisCardProps) {
  const citationsWithBibliography = chunk.citations?.citations?.filter((citation) => citation.associatedBibliography);

  return (
    <Card>
      <CardContent className="space-y-4 py-0">
        <AiGeneratedLabel className="float-right" />

        <p className="text-sm font-medium mb-5">Chunk analysis</p>

        <ExpandableResultSection
          initialIsExpanded={true}
          title={
            <h3 className="font-semibold flex items-center gap-2">
              <MessageCirclePlus className="w-4 h-4" /> Claim extraction rationale
            </h3>
          }
        >
          <p>{chunk.claims?.rationale}</p>
        </ExpandableResultSection>

        <ExpandableResultSection
          title={
            <div className="flex items-center gap-2">
              <h3 className="font-semibold flex items-center gap-2">
                <Link className="w-4 h-4" /> Citations
              </h3>

              <Badge variant="outline">{citationsWithBibliography?.length || 0} with bibliography</Badge>
            </div>
          }
        >
          {chunk.citations?.citations?.length === 0 && <p className="text-muted-foreground">No citations found</p>}

          {chunk.citations?.citations?.map((citation, index) => (
            <div key={index} className="bg-muted p-4 rounded-md ml-4 grid grid-cols-2 gap-2">
              <p>
                <span className="font-medium">Associated text: </span> {citation.text}
              </p>
              <p>
                <span className="font-medium">Format: </span> {citation.format}
              </p>
              <p>
                <span className="font-medium">Type: </span> {citation.type}
              </p>
              <p>
                <span className="font-medium">Needs bibliography: </span> {citation.needsBibliography ? 'Yes' : 'No'}
              </p>
              <p>
                <span className="font-medium">Associated reference file: </span>{' '}
                {citation.indexOfAssociatedBibliography !== -1
                  ? references[citation.indexOfAssociatedBibliography - 1]?.nameOfAssociatedSupportingDocument
                  : 'None'}
              </p>
              <p className="col-span-2">
                <span className="font-medium">Associated bibliography: </span> {citation.associatedBibliography}
              </p>
              <p className="col-span-2">
                <span className="font-medium">Rationale: </span> {citation.rationale}
              </p>
            </div>
          ))}
        </ExpandableResultSection>
      </CardContent>
    </Card>
  );
}
