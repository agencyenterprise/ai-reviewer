'use client';

import { Badge } from '@/components/ui/badge';
import { Card, CardContent } from '@/components/ui/card';
import { ChevronDown, ChevronRight, Clock } from 'lucide-react';
import { useState } from 'react';
import { FieldComparisonDetails } from './field-comparison-details';
import { TestCase } from './types';
import { formatDuration, formatIncEx, getFlattenedObjectKeys, getFlattenedObjectValue } from './util';

interface TestCaseItemProps {
  testCase: TestCase;
  consistencyProbability: number;
}

export function TestCaseItem({ testCase }: TestCaseItemProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  const [showFullOutput, setShowFullOutput] = useState(false);

  const toggleExpanded = () => {
    setIsExpanded(!isExpanded);
  };

  return (
    <Card className="py-1">
      <div className="cursor-pointer px-4 py-2" onClick={toggleExpanded}>
        <div className="flex items-center gap-2 justify-between">
          <div className="flex items-center gap-2">
            {isExpanded ? (
              <ChevronDown className="h-4 w-4 text-muted-foreground" />
            ) : (
              <ChevronRight className="h-4 w-4 text-muted-foreground" />
            )}
            <div className="flex flex-col gap-1">
              <p className="text-sm font-medium flex items-center gap-2">
                {testCase.agent_test_case.name}
                <span className="flex items-center gap-1 text-xs text-muted-foreground">
                  <Clock className="h-3 w-3" />
                  {formatDuration(testCase.call.duration)}
                </span>
              </p>
              <p className="text-xs text-muted-foreground wrap-anywhere">{testCase.nodeid}</p>
            </div>
          </div>
          <div className="flex items-center gap-1 flex-col">
            <Badge variant={testCase.outcome === 'passed' ? 'success' : 'destructive'}>
              {testCase.outcome === 'passed' ? 'Passed' : 'Failed'}
            </Badge>
          </div>
        </div>
      </div>

      {isExpanded && (
        <CardContent className="pt-0">
          <div className="space-y-6">
            {/* Test Configuration */}
            <div>
              <h4 className="font-medium mb-3">Test Configuration</h4>
              <div className="bg-muted/30 p-3 rounded-lg">
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  <div className="space-y-2">
                    <div className="flex justify-between">
                      <span className="font-medium text-sm">Agent:</span>
                      <span className="text-sm text-muted-foreground">{testCase.agent_test_case.agent.name}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="font-medium text-sm">Run Count:</span>
                      <span className="text-sm text-muted-foreground">
                        {testCase.agent_test_case.evaluation_config.run_count}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="font-medium text-sm">Evaluator Model:</span>
                      <span className="text-sm text-muted-foreground">
                        {testCase.agent_test_case.evaluation_config.evaluator_model}
                      </span>
                    </div>
                  </div>
                  <div className="space-y-2">
                    <div>
                      <span className="font-medium text-sm">Strict Fields:</span>
                      <div className="mt-1 text-sm text-muted-foreground wrap-break-word bg-background p-2 rounded border max-h-32 overflow-y-auto">
                        <pre className="whitespace-pre-wrap font-mono text-xs">
                          {formatIncEx(testCase.agent_test_case.evaluation_config.strict_fields)}
                        </pre>
                      </div>
                    </div>
                  </div>
                  <div className="space-y-2">
                    <div>
                      <span className="font-medium text-sm">LLM Fields:</span>
                      <div className="mt-1 text-sm text-muted-foreground wrap-break-word bg-background p-2 rounded border max-h-32 overflow-y-auto">
                        <pre className="whitespace-pre-wrap font-mono text-xs">
                          {formatIncEx(testCase.agent_test_case.evaluation_config.llm_fields)}
                        </pre>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Prompt args */}
            <div>
              <h4 className="font-medium mb-3">Prompt args</h4>
              <div className="bg-muted/30 p-3 rounded-lg space-y-2">
                {Object.entries(testCase.agent_test_case.prompt_kwargs).map(([key, value]) => (
                  <div key={key} className="space-y-1">
                    <span className="font-medium text-sm">{key}:</span>
                    <div className="text-sm text-muted-foreground bg-background p-2 rounded border max-h-32 overflow-y-auto whitespace-pre-wrap">
                      {value}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Field-Level Analysis */}
            {testCase.agent_test_case.evaluation_result?.field_comparisons &&
              testCase.agent_test_case.evaluation_result.field_comparisons.length > 0 && (
                <div>
                  <h4 className="font-medium mb-3">Field-Level Analysis</h4>
                  <div className="space-y-2">
                    {testCase.agent_test_case.evaluation_result.field_comparisons.map((comp, idx) => (
                      <FieldComparisonDetails key={idx} comparison={comp} />
                    ))}
                  </div>
                </div>
              )}

            {/* Expected vs Actual Output - Collapsible */}
            <div className="border-t pt-4">
              <div className="flex items-center justify-between mb-3">
                <h4 className="font-medium">Full Output Comparison</h4>
                <button
                  onClick={() => setShowFullOutput(!showFullOutput)}
                  className="text-xs text-muted-foreground hover:text-foreground flex items-center gap-1 transition-colors"
                >
                  {showFullOutput ? (
                    <>
                      <ChevronDown className="h-3 w-3" />
                      Hide
                    </>
                  ) : (
                    <>
                      <ChevronRight className="h-3 w-3" />
                      Show details
                    </>
                  )}
                </button>
              </div>
              {showFullOutput && (
                <div className="space-y-4">
                  {testCase.agent_test_case.actual_outputs.map((output, outputIndex) => (
                    <div key={outputIndex}>
                      {outputIndex > 0 && <div className="border-t pt-4 mb-4" />}
                      {testCase.agent_test_case.evaluation_config.run_count > 1 && (
                        <p className="text-xs text-muted-foreground mb-2">Run {outputIndex + 1}</p>
                      )}
                      {(() => {
                        const expectedKeys = getFlattenedObjectKeys(testCase.agent_test_case.expected_output);
                        const actualKeys = getFlattenedObjectKeys(output);
                        const allKeys = [...new Set([...expectedKeys, ...actualKeys])].sort((a, b) =>
                          a.localeCompare(b),
                        );

                        return (
                          <div className="rounded-lg overflow-hidden border">
                            <table className="w-full">
                              <thead className="bg-muted/30">
                                <tr className="border-b">
                                  <th className="text-left p-3 font-medium text-sm">Field</th>
                                  <th className="text-left p-3 font-medium text-sm">Expected</th>
                                  <th className="text-left p-3 font-medium text-sm">Actual</th>
                                </tr>
                              </thead>
                              <tbody>
                                {allKeys.map((key) => {
                                  const expectedValue = getFlattenedObjectValue(
                                    testCase.agent_test_case.expected_output,
                                    key,
                                  );
                                  const actualValue = getFlattenedObjectValue(output, key);

                                  return (
                                    <tr key={key} className="border-b last:border-b-0">
                                      <td className="p-3 font-mono text-xs wrap-anywhere align-top w-[20%]">{key}</td>
                                      <td className="p-3 wrap-anywhere align-top w-[40%]">
                                        {expectedValue !== undefined ? (
                                          <p className="text-sm text-muted-foreground whitespace-pre-wrap">
                                            {String(expectedValue)}
                                          </p>
                                        ) : (
                                          <span className="text-xs text-muted-foreground italic">Not specified</span>
                                        )}
                                      </td>
                                      <td className="p-3 wrap-anywhere align-top w-[40%]">
                                        {actualValue !== undefined ? (
                                          <p className="text-sm text-muted-foreground whitespace-pre-wrap">
                                            {String(actualValue)}
                                          </p>
                                        ) : (
                                          <span className="text-xs text-muted-foreground italic">Not provided</span>
                                        )}
                                      </td>
                                    </tr>
                                  );
                                })}
                              </tbody>
                            </table>
                          </div>
                        );
                      })()}
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Evaluation Results */}
            <div className="border-t pt-4">
              <h4 className="font-medium mb-3">Evaluation Results</h4>
              <div className="bg-muted/30 p-3 rounded-lg space-y-2">
                <div className="flex items-center gap-2">
                  <span className="font-medium text-sm">Overall Result:</span>
                  <Badge variant={testCase.agent_test_case.evaluation_result?.passed ? 'success' : 'destructive'}>
                    {testCase.agent_test_case.evaluation_result?.passed ? 'Passed' : 'Failed'}
                  </Badge>
                </div>
                <div>
                  <span className="font-medium text-sm">Evaluation Rationale:</span>
                  <div className="text-sm text-muted-foreground mt-1 bg-background p-2 rounded border max-h-64 overflow-y-auto whitespace-pre-wrap font-mono">
                    {testCase.agent_test_case.evaluation_result?.rationale}
                  </div>
                </div>
              </div>
            </div>

            {/* Error Information */}
            {testCase.call.crash && (
              <div className="border-t pt-4">
                <h4 className="font-medium mb-3 text-red-600">Error Information</h4>
                <div className="bg-red-50 p-3 rounded-lg">
                  <div className="space-y-2">
                    <div>
                      <span className="font-medium text-sm text-red-800">Error Message:</span>
                      <p className="text-sm text-red-700 mt-1 whitespace-pre-wrap font-mono">
                        {testCase.call.crash.message}
                      </p>
                    </div>
                    <div>
                      <span className="font-medium text-sm text-red-800">File:</span>
                      <p className="text-sm text-red-700 mt-1 font-mono">{testCase.call.crash.path}</p>
                    </div>
                    <div>
                      <span className="font-medium text-sm text-red-800">Line:</span>
                      <p className="text-sm text-red-700 mt-1">{testCase.call.crash.lineno}</p>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </CardContent>
      )}
    </Card>
  );
}
