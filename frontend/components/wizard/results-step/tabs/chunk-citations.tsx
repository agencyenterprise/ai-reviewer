import * as React from 'react';
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from '@/components/ui/accordion';
import { Link as LinkIcon, FileIcon } from 'lucide-react';
import { Citation, BibliographyItem, FileDocument } from '@/lib/generated-api';
import { ChunkItem } from '../components/chunk-display';

interface ChunkCitationsProps {
  citations: Citation[];
  references: BibliographyItem[];
  supportingFiles: FileDocument[];
}

export function ChunkCitations({ citations, references, supportingFiles }: ChunkCitationsProps) {
  if (!citations || citations.length === 0) {
    return null;
  }

  return (
    <Accordion type="single" collapsible className="border rounded-lg">
      <AccordionItem value="citations" className="border-none">
        <AccordionTrigger className="px-4 py-2 hover:no-underline">
          <div className="flex items-center gap-2">
            <LinkIcon className="w-4 h-4" />
            <span className="font-bold">Citations ({citations.length})</span>
            <span className="text-xs text-muted-foreground font-normal">
              {citations.filter((c) => c.associatedBibliography).length} with bibliography
            </span>
          </div>
        </AccordionTrigger>
        <AccordionContent className="px-4 pb-4">
          <div className="space-y-2">
            {citations.map((citation, ci) => (
              <ChunkItem key={ci}>
                <p className="">
                  <strong>Citation:</strong> {citation.text}
                </p>
                <div className="flex gap-2 text-xs mt-1">
                  <span className="px-2 py-1 bg-blue-100 text-blue-800 rounded">{citation.type}</span>
                  <span className="px-2 py-1 bg-gray-100 text-gray-800 rounded">{citation.format}</span>
                </div>
                {citation.associatedBibliography && (
                  <div className="text-xs text-muted-foreground mt-1">
                    <strong>Associated bibliography:</strong> {citation.associatedBibliography}
                    {citation.format &&
                      references[citation.indexOfAssociatedBibliography - 1]?.hasAssociatedSupportingDocument && (
                        <div className="text-xs text-muted-foreground flex items-center gap-1 mt-1">
                          <strong>Related supporting document:</strong>
                          <FileIcon className="w-3 h-3" />
                          {
                            supportingFiles[
                              references[citation.indexOfAssociatedBibliography - 1]
                                ?.indexOfAssociatedSupportingDocument - 1
                            ]?.fileName
                          }
                        </div>
                      )}
                    {citation.indexOfAssociatedBibliography &&
                      references[citation.indexOfAssociatedBibliography - 1] &&
                      !references[citation.indexOfAssociatedBibliography - 1].hasAssociatedSupportingDocument && (
                        <div className="text-xs text-muted-foreground mt-1">
                          <strong>No related supporting document:</strong>
                        </div>
                      )}
                  </div>
                )}
              </ChunkItem>
            ))}
          </div>
        </AccordionContent>
      </AccordionItem>
    </Accordion>
  );
}
