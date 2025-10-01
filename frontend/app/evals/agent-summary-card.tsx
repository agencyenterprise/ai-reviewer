'use client';

import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { BotIcon, ChevronDown, ChevronRight, Clock } from 'lucide-react';
import { TestCase } from './types';
import { TestCaseItem } from './test-case-item';

interface AgentSummary {
  agentName: string;
  testCases: TestCase[];
  total: number;
  passed: number;
  failed: number;
  accuracy: number;
  totalDuration: number;
  averageDuration: number;
}

interface AgentSummaryCardProps {
  summary: AgentSummary;
  showOnlyFailed?: boolean;
}

export function AgentSummaryCard({ summary, showOnlyFailed = false }: AgentSummaryCardProps) {
  const [isExpanded, setIsExpanded] = useState(true);

  const toggleExpanded = () => {
    setIsExpanded(!isExpanded);
  };

  const formatDuration = (duration: number) => {
    return `${duration.toFixed(2)}s`;
  };

  return (
    <Card>
      <CardHeader className="pb-3">
        <div className="cursor-pointer" onClick={toggleExpanded}>
          <div className="flex items-center gap-2 justify-between">
            <div className="flex items-center gap-2">
              {isExpanded ? (
                <ChevronDown className="h-4 w-4 text-muted-foreground" />
              ) : (
                <ChevronRight className="h-4 w-4 text-muted-foreground" />
              )}
              <div className="flex items-center gap-2">
                <BotIcon className="h-4 w-4" />
                <CardTitle>{summary.agentName}</CardTitle>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <Badge
                variant={summary.accuracy >= 80 ? 'success' : summary.accuracy >= 60 ? 'secondary' : 'destructive'}
              >
                {summary.accuracy}% Accuracy
              </Badge>
            </div>
          </div>
        </div>
      </CardHeader>

      <CardContent className="pt-0">
        {/* Summary Metrics */}
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-4">
          <div className="text-center p-3 bg-muted/30 rounded-lg">
            <div className="text-lg font-bold text-foreground">{summary.total}</div>
            <div className="text-xs text-muted-foreground">Total Tests</div>
          </div>
          <div className="text-center p-3 bg-green-50 rounded-lg">
            <div className="text-lg font-bold text-green-600">{summary.passed}</div>
            <div className="text-xs text-muted-foreground">Passed</div>
          </div>
          <div className="text-center p-3 bg-red-50 rounded-lg">
            <div className="text-lg font-bold text-red-600">{summary.failed}</div>
            <div className="text-xs text-muted-foreground">Failed</div>
          </div>
          <div className="text-center p-3 bg-blue-50 rounded-lg">
            <div className="text-lg font-bold text-blue-600">{summary.accuracy}%</div>
            <div className="text-xs text-muted-foreground">Accuracy</div>
          </div>
          <div className="text-center p-3 bg-purple-50 rounded-lg">
            <div className="text-lg font-bold text-purple-600 flex items-center justify-center gap-1">
              <Clock className="h-3 w-3" />
              {formatDuration(summary.averageDuration)}
            </div>
            <div className="text-xs text-muted-foreground">Avg Duration</div>
          </div>
        </div>

        {/* Test Cases */}
        {isExpanded && (
          <div className="space-y-2 border-t pt-4">
            <h4 className="font-medium text-sm text-muted-foreground">Test Cases</h4>
            {summary.testCases
              .filter((testCase) => !showOnlyFailed || testCase.outcome === 'failed')
              .map((testCase, index) => (
                <TestCaseItem key={index} testCase={testCase} />
              ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

// Utility function to group test cases by agent name
export function groupTestCasesByAgent(testCases: TestCase[]): AgentSummary[] {
  const agentGroups = new Map<string, TestCase[]>();

  // Group test cases by agent name
  testCases.forEach((testCase) => {
    const agentName = testCase.agent_test_case.agent.name;
    if (!agentGroups.has(agentName)) {
      agentGroups.set(agentName, []);
    }
    agentGroups.get(agentName)!.push(testCase);
  });

  // Calculate summary statistics for each agent group
  return Array.from(agentGroups.entries())
    .map(([agentName, cases]) => {
      const total = cases.length;
      const passed = cases.filter((c) => c.outcome === 'passed').length;
      const failed = cases.filter((c) => c.outcome === 'failed').length;
      const accuracy = total > 0 ? Math.round((passed / total) * 100) : 0;
      const totalDuration = cases.reduce((sum, c) => sum + c.call.duration, 0);
      const averageDuration = total > 0 ? totalDuration / total : 0;

      return {
        agentName,
        testCases: cases,
        total,
        passed,
        failed,
        accuracy,
        totalDuration,
        averageDuration,
      };
    })
    .sort((a, b) => b.accuracy - a.accuracy); // Sort by accuracy descending
}
