'use client';

import { Card, CardContent } from '@/components/ui/card';
import { ChunkReevaluationResponse, ClaimSubstantiatorStateOutput } from '@/lib/generated-api';
import { Loader2 } from 'lucide-react';
import Image from 'next/image';
import { useEffect, useRef, useState } from 'react';
import { ChunkSidebarContent } from '../components/chunk-sidebar-content';
import { DocumentReconstructor } from '../components/document-reconstructor';
import { ErrorsCard } from '../components/errors-card';

interface DocumentExplorerTabProps {
  results: ClaimSubstantiatorStateOutput;
  onChunkReevaluation: (response: ChunkReevaluationResponse) => void;
  isProcessing?: boolean;
}

export function DocumentExplorerTab({ results, onChunkReevaluation, isProcessing = false }: DocumentExplorerTabProps) {
  const errors = results.errors || [];
  const workflowErrors = errors.filter((error) => error.chunkIndex === null);
  const hasChunks = (results.chunks?.length || 0) > 0;

  const [selectedChunkIndex, setSelectedChunkIndex] = useState<number | null>(null);
  const selectedChunk = results.chunks?.find((chunk) => chunk.chunkIndex === selectedChunkIndex);
  const sidebarRef = useRef<HTMLDivElement>(null);

  // Scroll sidebar to top when selected chunk changes
  useEffect(() => {
    if (sidebarRef.current && selectedChunkIndex !== null) {
      sidebarRef.current.scrollTop = 0;
    }
  }, [selectedChunkIndex]);

  if (isProcessing && !hasChunks) {
    return (
      <div className="space-y-4">
        {workflowErrors.length > 0 && <ErrorsCard errors={workflowErrors} />}
        <div className="flex items-center justify-center py-12">
          <div className="text-center space-y-3">
            <Loader2 className="h-8 w-8 animate-spin text-primary mx-auto" />
            <p className="text-sm text-muted-foreground">Breaking document into sections...</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-2">
      {workflowErrors.length > 0 && <ErrorsCard errors={workflowErrors} />}

      <div className="grid grid-cols-12 gap-4">
        <div className="col-span-7 pb-100 leading-relaxed">
          <DocumentReconstructor
            results={results}
            selectedChunkIndex={selectedChunkIndex}
            onChunkSelect={setSelectedChunkIndex}
          />
        </div>
        <div
          ref={sidebarRef}
          className="col-span-5 bg-muted p-4 rounded-lg sticky top-0 text-sm overflow-auto max-h-[calc(100vh-2rem)] pb-40"
        >
          {!selectedChunk && (
            <Card>
              <CardContent className="flex flex-col justify-center space-y-2 py-8 text-center items-center">
                <Image
                  src="/undraw_chat-with-ai_ir62.svg"
                  alt="Document Explorer"
                  width={200}
                  height={100}
                  className="mb-8"
                />
                {isProcessing && (
                  <>
                    <div className="flex items-center justify-center gap-2">
                      <Loader2 className="h-6 w-6 animate-spin" />
                      <p className="font-medium text-xl">Analyzing document</p>
                    </div>
                    <p className="text-gray-600">
                      You can leave this page and come back later to view the results as the analysis runs in the
                      background.
                    </p>
                  </>
                )}
                {!isProcessing && (
                  <>
                    <p className="font-medium text-xl">Select a paragraph</p>
                    <p className="text-gray-600">Select a paragraph to view analysis results</p>
                  </>
                )}
              </CardContent>
            </Card>
          )}
          {selectedChunk && (
            <ChunkSidebarContent
              results={results}
              chunkIndex={selectedChunkIndex}
              isWorkflowRunning={isProcessing}
              onChunkReevaluation={onChunkReevaluation}
            />
          )}
        </div>
      </div>
    </div>
  );
}
