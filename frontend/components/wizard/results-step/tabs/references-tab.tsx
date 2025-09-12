'use client';

import * as React from 'react';
import { DetailedResults } from '../../types';

interface ReferencesTabProps {
  results: DetailedResults;
}

export function ReferencesTab({ results }: ReferencesTabProps) {
  return (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold">References</h3>
      <div className="space-y-3">
        {results.references.map((reference, index) => (
          <div key={index} className="border rounded-lg p-4">
            <div className="flex items-start justify-between">
              <p className="text-sm flex-1">{reference.text}</p>
              <div className="ml-3 flex items-center gap-3">
                <div
                  className={`px-2 py-1 rounded text-xs ${
                    reference.has_associated_supporting_document
                      ? 'bg-green-100 text-green-800'
                      : 'bg-orange-100 text-orange-800'
                  }`}
                >
                  {reference.has_associated_supporting_document ? 'Document provided' : 'Document not provided'}
                </div>
                {reference.has_associated_supporting_document && (
                  <span className="text-xs text-muted-foreground">
                    <strong>Related document:</strong>{' '}
                    {results.supporting_files[reference.index_of_associated_supporting_document - 1]?.file_name}
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
