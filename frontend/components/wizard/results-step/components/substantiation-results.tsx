'use client';

import React from 'react';
import { ClaimCommonKnowledgeResultWithClaimIndex, ClaimSubstantiationResultWithClaimIndex } from '@/lib/generated-api';
import { SeverityBadge } from './severity-badge';

interface SubstantiationResultsProps {
  substantiation?: ClaimSubstantiationResultWithClaimIndex;
  commonKnowledgeResult?: ClaimCommonKnowledgeResultWithClaimIndex;
  className?: string;
}

export function SubstantiationResults({
  substantiation,
  commonKnowledgeResult,
  className = '',
}: SubstantiationResultsProps) {
  if (!substantiation) {
    return null;
  }

  const isCommonKnowledge = commonKnowledgeResult?.isCommonKnowledge || false;
  const needsSubstantiation = commonKnowledgeResult?.needsSubstantiation || false;
  let title_extra_details = '';
  if (isCommonKnowledge) {
    title_extra_details = needsSubstantiation
      ? ' (May Be Common Knowledge But Still Needs Substantiation)'
      : ' (May Be Common Knowledge That Does Not Need Substantiation)';
  } else {
    title_extra_details = needsSubstantiation ? ' (Needs Substantiation)' : ' (Does Not Need Substantiation)';
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
        <div
          className={`p-3 border rounded-lg ${
            !needsSubstantiation ? 'bg-orange-50 border-orange-200' : 'bg-red-50 border-red-200'
          }`}
        >
          <div className="flex items-start gap-2">
            <div
              className={`w-2 h-2 rounded-full mt-2 flex-shrink-0 ${
                !needsSubstantiation ? 'bg-orange-500' : 'bg-red-500'
              }`}
            />
            <div className="space-y-2">
              <h4 className={`font-medium ${!needsSubstantiation ? 'text-orange-800' : 'text-red-800'}`}>
                Claim Unsubstantiated {title_extra_details} <SeverityBadge severity={substantiation.severity} />
              </h4>
              <p className={`text-sm ${!needsSubstantiation ? 'text-orange-700' : 'text-red-700'}`}>
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
