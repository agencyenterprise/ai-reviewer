'use client';

import { ClaimSubstantiatorStateOutput } from '@/lib/generated-api';
import { FileText } from 'lucide-react';
import * as React from 'react';
import { TabWithLoadingStates } from './tab-with-loading-states';

interface ReferencesTabProps {
  results: ClaimSubstantiatorStateOutput;
  isProcessing?: boolean;
}

export function ReferencesTab({ results, isProcessing = false }: ReferencesTabProps) {
  return (
    <TabWithLoadingStates
      title="References"
      data={results.references}
      isProcessing={isProcessing}
      hasData={(references) => (references?.length || 0) > 0}
      loadingMessage={{
        title: 'Extracting bibliography...',
        description: 'Identifying references in the document',
      }}
      emptyMessage={{
        icon: <FileText className="h-12 w-12 text-muted-foreground" />,
        title: 'No references found',
        description: "This document doesn't contain a bibliography or reference section",
      }}
      skeletonType="list"
      skeletonCount={5}
    >
      {(references) => (
        <div className="space-y-3">
          {references.map((reference, index) => (
            <div key={index} className="border rounded-lg p-4">
              <div className="flex items-start justify-between">
                <p className="text-sm flex-1">{reference.text}</p>
                <div className="ml-3 flex items-center gap-3">
                  <div
                    className={`px-2 py-1 rounded text-xs ${
                      reference.hasAssociatedSupportingDocument
                        ? 'bg-green-100 text-green-800'
                        : 'bg-orange-100 text-orange-800'
                    }`}
                  >
                    {reference.hasAssociatedSupportingDocument ? 'Document provided' : 'Document not provided'}
                  </div>
                  {reference.hasAssociatedSupportingDocument && (
                    <span className="text-xs text-muted-foreground">
                      <strong>Related document:</strong>{' '}
                      {results.supportingFiles?.[reference.indexOfAssociatedSupportingDocument - 1]?.fileName}
                    </span>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </TabWithLoadingStates>
  );
}
