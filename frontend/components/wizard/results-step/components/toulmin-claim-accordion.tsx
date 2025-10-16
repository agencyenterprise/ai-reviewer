'use client';

import { Button } from '@/components/ui/button';
import { ToulminClaim } from '@/lib/generated-api/models/ToulminClaim';
import { cn } from '@/lib/utils';
import { ChevronDown, ChevronRight, Scale } from 'lucide-react';
import { useState } from 'react';

export interface ToulminClaimAccordionProps {
  claim: ToulminClaim;
  className?: string;
}

export function ToulminClaimAccordion({ claim, className }: ToulminClaimAccordionProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  return (
    <div className={cn('border-b pb-2 space-y-4', className)}>
      <div className="flex items-center justify-between">
        <h3 className="flex items-center gap-2 font-semibold">
          <Scale className="h-4 w-4" />
          Toulmin Argument Structure
        </h3>

        <Button
          variant="ghost"
          size="xs"
          onClick={() => setIsExpanded(!isExpanded)}
          className="text-gray-600 hover:text-gray-900"
        >
          {isExpanded ? (
            <>
              <ChevronDown />
              Hide Details
            </>
          ) : (
            <>
              <ChevronRight />
              Show Details
            </>
          )}
        </Button>
      </div>

      {isExpanded && (
        <div className="space-y-3">
          <p>
            <span className="font-medium">Extracted Claim:</span> {claim.claim}
          </p>

          <p>
            <span className="font-medium">Related text:</span> {claim.text}
          </p>

          <p>
            <span className="font-medium">Rationale:</span> {claim.rationale}
          </p>

          <h4 className="font-medium text-base">Toulmin Elements</h4>
          <div className="space-y-2">
            <div>
              <span className="font-medium">Data:</span>{' '}
              {claim.data && claim.data.length > 0 ? (
                <ul className="list-disc pl-5">
                  {claim.data.map((data) => (
                    <li key={data}>{data}</li>
                  ))}
                </ul>
              ) : (
                <span className="text-muted-foreground">None</span>
              )}
            </div>
            <div>
              <span className="font-medium">Warrants:</span>{' '}
              {claim.warrants && claim.warrants.length > 0 ? (
                <ul className="list-disc pl-5">
                  {claim.warrants.map((warrant) => (
                    <li key={warrant}>{warrant}</li>
                  ))}
                </ul>
              ) : (
                <span className="text-muted-foreground">None</span>
              )}
            </div>
            <div>
              <span className="font-medium">Qualifiers:</span>{' '}
              {claim.qualifiers && claim.qualifiers.length > 0 ? (
                <ul className="list-disc pl-5">
                  {claim.qualifiers.map((qualifier) => (
                    <li key={qualifier}>{qualifier}</li>
                  ))}
                </ul>
              ) : (
                <span className="text-muted-foreground">None</span>
              )}
            </div>
            <div>
              <span className="font-medium">Rebuttals:</span>{' '}
              {claim.rebuttals && claim.rebuttals.length > 0 ? (
                <ul className="list-disc pl-5">
                  {claim.rebuttals.map((rebuttal) => (
                    <li key={rebuttal}>{rebuttal}</li>
                  ))}
                </ul>
              ) : (
                <span className="text-muted-foreground">None</span>
              )}
            </div>
            <div>
              <span className="font-medium">Backing:</span>{' '}
              {claim.backing && claim.backing.length > 0 ? (
                <ul className="list-disc pl-5">
                  {claim.backing.map((backing) => (
                    <li key={backing}>{backing}</li>
                  ))}
                </ul>
              ) : (
                <span className="text-muted-foreground">None</span>
              )}
            </div>
            <div>
              <span className="font-medium">Warrant Expression:</span>{' '}
              {claim.warrantExpression ? (
                <span>{claim.warrantExpression}</span>
              ) : (
                <span className="text-muted-foreground">None</span>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
