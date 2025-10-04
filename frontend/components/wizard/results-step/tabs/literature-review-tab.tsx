'use client';

import { ClaimSubstantiatorStateOutput } from '@/lib/generated-api';
import { Markdown } from '@/components/markdown';
import * as React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { AlertCircle, BookOpen } from 'lucide-react';

interface LiteratureReviewTabProps {
  results: ClaimSubstantiatorStateOutput;
}

export function LiteratureReviewTab({ results }: LiteratureReviewTabProps) {
  const literatureReview = results.literatureReview;

  if (!literatureReview) {
    return (
      <div className="space-y-4">
        <h3 className="text-lg font-semibold">Literature Review</h3>
        <div className="bg-yellow-200/40 p-4 rounded-lg text-sm">
          <h4 className="font-bold mb-2 flex items-center gap-2">
            <AlertCircle className="w-4 h-4" />
            No literature review was generated for this analysis
          </h4>
          <p className="mb-2">This may be because:</p>
          <ul className="list-disc pl-5 space-y-1">
            <li>The literature review agent was not included in the workflow configuration</li>
            <li>The analysis is still in progress</li>
            <li>An error occurred during the literature review process</li>
          </ul>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2">
        <BookOpen className="h-5 w-5 text-blue-600" />
        <h3 className="text-lg font-semibold">Literature Review</h3>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">AI-Generated Literature Review Report</CardTitle>
          <CardDescription>
            This report analyzes the document&apos;s content and bibliography to identify potential citation
            improvements and additional references.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="prose prose-sm max-w-none">
            <Markdown>{literatureReview}</Markdown>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
