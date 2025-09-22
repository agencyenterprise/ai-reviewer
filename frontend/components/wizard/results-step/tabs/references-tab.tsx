'use client';

import { ClaimSubstantiatorStateOutput } from '@/lib/generated-api';
import * as React from 'react';

interface ReferencesTabProps {
  results: ClaimSubstantiatorStateOutput;
}

export function ReferencesTab({ results }: ReferencesTabProps) {
  return (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold">References</h3>
      <div className="space-y-3">
        {results.references?.map((reference, index) => (
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
    </div>
  );
}
