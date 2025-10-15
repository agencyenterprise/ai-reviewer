'use client';

import { ClaimSubstantiatorStateOutput } from '@/lib/generated-api';
import { Markdown } from '@/components/markdown';
import * as React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { AlertCircle, BookOpen } from 'lucide-react';
import { TabWithLoadingStates } from './tab-with-loading-states';

interface LiteratureReviewTabProps {
  results: ClaimSubstantiatorStateOutput;
  isProcessing?: boolean;
}

export function LiteratureReviewTab({ results, isProcessing = false }: LiteratureReviewTabProps) {
  return (
    <TabWithLoadingStates
      title="Literature Review"
      data={results.literatureReview}
      isProcessing={isProcessing}
      hasData={(review) => !!review}
      loadingMessage={{
        title: 'Conducting literature review...',
        description: 'This may take some minutes as we analyze the bibliography and supporting documents',
      }}
      emptyMessage={{
        icon: <AlertCircle className="h-12 w-12 text-muted-foreground" />,
        title: 'No literature review available',
        description: 'The literature review agent was not enabled for this analysis',
      }}
      emptyStateChildren={
        <div className="text-sm text-muted-foreground text-left max-w-md">
          <p className="mb-2">This may be because:</p>
          <ul className="list-disc pl-5 space-y-1">
            <li>The literature review option was not selected during upload</li>
            <li>An error occurred during the literature review process</li>
          </ul>
        </div>
      }
      skeletonType="paragraphs"
      skeletonCount={6}
    >
      {(literatureReview) => (
        <>
          <div className="flex items-center gap-2">
            <BookOpen className="h-5 w-5 text-blue-600" />
            <span className="text-sm font-medium">AI-Generated Report</span>
          </div>

          <Card>
            <CardHeader>
              <CardTitle className="text-base">Literature Review Analysis</CardTitle>
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
        </>
      )}
    </TabWithLoadingStates>
  );
}
