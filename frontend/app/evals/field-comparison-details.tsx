'use client';

import { useState } from 'react';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { ChevronDown, ChevronRight } from 'lucide-react';
import { FieldComparison } from './types';

interface FieldComparisonDetailsProps {
  comparison: FieldComparison;
}

export function FieldComparisonDetails({ comparison }: FieldComparisonDetailsProps) {
  const [showExamples, setShowExamples] = useState(false);

  const hasExamples = comparison.examples.length > 0;
  const accuracy = Math.round((comparison.passed_instances / comparison.total_instances) * 100);

  return (
    <div className="border rounded-lg p-3 space-y-2 bg-muted/20">
      <div className="flex items-center justify-between gap-2">
        <div className="flex items-center gap-2 flex-1 min-w-0">
          <Badge variant={comparison.passed ? 'success' : 'destructive'} className="shrink-0">
            {comparison.passed ? '✓' : '✗'}
          </Badge>
          <code className="text-sm font-mono truncate">{comparison.field_path}</code>
          <Badge variant="outline" className="text-xs shrink-0">
            {comparison.comparison_type}
          </Badge>
        </div>
        <div className="flex items-center gap-2 shrink-0">
          <Badge variant={accuracy >= 80 ? 'success' : accuracy >= 60 ? 'secondary' : 'destructive'}>
            {comparison.passed_instances}/{comparison.total_instances}
          </Badge>
          {hasExamples && (
            <Button variant="ghost" size="sm" onClick={() => setShowExamples(!showExamples)} className="h-7 px-2">
              {showExamples ? <ChevronDown className="h-3 w-3" /> : <ChevronRight className="h-3 w-3" />}
            </Button>
          )}
        </div>
      </div>

      <p className="text-xs text-muted-foreground pl-1">{comparison.rationale}</p>

      {comparison.matching_strategy && (
        <p className="text-xs text-muted-foreground italic pl-1">
          Strategy: {comparison.matching_strategy.replace(/_/g, ' ')}
        </p>
      )}

      {showExamples && hasExamples && (
        <div className="mt-2 space-y-2 border-t pt-2">
          <h5 className="text-xs font-medium">Mismatch Examples:</h5>
          {comparison.examples.map((example, idx) => (
            <div key={idx} className="bg-background p-2 rounded text-xs space-y-1 border">
              <div className="font-mono text-muted-foreground text-xs">{example.instance_identifier}</div>
              {example.note && <div className="text-muted-foreground italic">{example.note}</div>}
              <div className="grid grid-cols-2 gap-2 mt-1">
                <div>
                  <span className="font-medium text-xs">Expected:</span>
                  <pre className="mt-1 p-1.5 bg-muted/50 rounded overflow-x-auto text-xs">
                    {example.expected_value || 'null'}
                  </pre>
                </div>
                <div>
                  <span className="font-medium text-xs">Actual:</span>
                  <pre className="mt-1 p-1.5 bg-muted/50 rounded overflow-x-auto text-xs">
                    {example.actual_value || 'null'}
                  </pre>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
