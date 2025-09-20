'use client';

import * as React from 'react';
import { Download } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../../ui/card';
import { Button } from '../../ui/button';
import { Tooltip, TooltipContent, TooltipTrigger } from '../../ui/tooltip';
import { AnalysisResults } from '../types';
import { useResultsCalculations } from './hooks/use-results-calculations';
import { SummaryCards, TabNavigation } from './components';
import { SummaryTab, ClaimsTab, CitationsTab, ReferencesTab, FilesTab, ChunksTab } from './tabs';
import { TabType } from './constants';
import { ClaimSubstantiatorStateOutput } from '@/lib/generated-api';
import { DocumentExplorerTab } from './tabs/document-explorer-tab';
import { downloadAsJson } from '@/lib/utils';

interface ResultsVisualizationProps {
  results: AnalysisResults | null;
}

export function ResultsVisualization({ results }: ResultsVisualizationProps) {
  const detailedResults = results?.fullResults as ClaimSubstantiatorStateOutput | undefined;
  const [activeTab, setActiveTab] = React.useState<TabType>('summary');

  const calculations = useResultsCalculations(detailedResults);

  const handleSaveResults = () => {
    if (results) {
      const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
      const filename = `analysis-results-${timestamp}`;
      downloadAsJson(results, filename);
    }
  };

  if (!results || !detailedResults) {
    return (
      <Card className="max-w-4xl mx-auto">
        <CardHeader>
          <CardTitle>No Results Available</CardTitle>
          <CardDescription>No analysis results to display</CardDescription>
        </CardHeader>
      </Card>
    );
  }

  const renderActiveTab = () => {
    switch (activeTab) {
      case 'summary':
        return (
          <SummaryTab
            results={detailedResults}
            totalChunks={calculations.totalChunks}
            chunksWithClaims={calculations.chunksWithClaims}
            chunksWithCitations={calculations.chunksWithCitations}
            supportedReferences={calculations.supportedReferences}
          />
        );
      case 'claims':
        return <ClaimsTab results={detailedResults} />;
      case 'citations':
        return <CitationsTab results={detailedResults} />;
      case 'references':
        return <ReferencesTab results={detailedResults} />;
      case 'files':
        return <FilesTab results={detailedResults} />;
      case 'chunks':
        return <ChunksTab results={detailedResults} />;
      case 'document-explorer':
        return <DocumentExplorerTab results={detailedResults} />;
    }
  };

  return (
    <div className="space-y-6 max-w-6xl mx-auto">
      <SummaryCards
        totalClaims={calculations.totalClaims}
        totalCitations={calculations.totalCitations}
        totalUnsubstantiated={calculations.totalUnsubstantiated}
      />

      <div className="flex justify-center">
        <Tooltip>
          <TooltipTrigger asChild>
            <Button onClick={handleSaveResults} variant="outline" size="sm" className="gap-2">
              <Download className="h-4 w-4" />
              Save Raw Analysis Results
            </Button>
          </TooltipTrigger>
          <TooltipContent>
            <p>Download results as JSON to view them again without re-analyzing documents</p>
          </TooltipContent>
        </Tooltip>
      </div>

      <TabNavigation activeTab={activeTab} onTabChange={setActiveTab} />

      <Card>
        <CardContent className="p-6">{renderActiveTab()}</CardContent>
      </Card>
    </div>
  );
}
