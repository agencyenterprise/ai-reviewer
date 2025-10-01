'use client';

import React from 'react';
import { ClaimSubstantiationResultWithClaimIndex } from '@/lib/generated-api';

interface SubstantiationResultsProps {
  substantiation?: ClaimSubstantiationResultWithClaimIndex;
  className?: string;
}

export function SubstantiationResults({ substantiation, className = '' }: SubstantiationResultsProps) {
  if (!substantiation) {
    return null;
  }

  return (
    <div className={`space-y-3 ${className}`}>
      {/* Substantiated Case */}
      {substantiation.isSubstantiated && (
        <div className="p-3 bg-green-50 border border-green-200 rounded-lg">
          <div className="flex items-start gap-2">
            <div className="w-2 h-2 bg-green-500 rounded-full mt-2 flex-shrink-0" />
            <div className="space-y-2">
              <h4 className="font-medium text-green-800">Claim Substantiated</h4>
              <p className="text-sm text-green-700">
                <strong>Rationale:</strong> {substantiation.rationale}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* UnSubstantiated Case */}
      {!substantiation.isSubstantiated && (
        <div className="p-3 bg-red-50 border border-red-200 rounded-lg">
          <div className="flex items-start gap-2">
            <div className="w-2 h-2 bg-red-500 rounded-full mt-2 flex-shrink-0" />
            <div className="space-y-2">
              <h4 className="font-medium text-red-800">Claim Unsubstantiated</h4>
              <p className="text-sm text-red-700">
                <strong>Rationale:</strong> {substantiation.rationale}
              </p>
            </div>
          </div>
          {substantiation.feedback && (
            <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg mt-4">
              <p className="text-sm text-blue-600 mt-1">
                <strong>Feedback to resolve:</strong> {substantiation.feedback}
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
