'use client';

import { Button } from '@/components/ui/button';
import { Table, TableBody, TableCell, TableRow } from '@/components/ui/table';
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
          size="sm"
          onClick={() => setIsExpanded(!isExpanded)}
          className="flex items-center gap-1 text-sm text-gray-600 hover:text-gray-900"
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
          <p className="text-sm leading-relaxed">
            <span className="font-medium">Extracted Claim:</span> {claim.claim}
          </p>

          <p className="text-sm leading-relaxed">
            <span className="font-medium">Related text:</span> {claim.text}
          </p>

          <p className="text-sm leading-relaxed">
            <span className="font-medium">Rationale:</span> {claim.rationale}
          </p>

          <h4 className="font-medium">Toulmin Elements:</h4>
          <Table>
            <TableBody>
              <TableRow>
                <TableCell>Data</TableCell>
                <TableCell>
                  <ul className="list-disc pl-5">
                    {claim.data?.map((data) => (
                      <li key={data}>{data}</li>
                    ))}
                  </ul>
                </TableCell>
              </TableRow>
              <TableRow>
                <TableCell>Warrants</TableCell>
                <TableCell>
                  <ul className="list-disc pl-5">
                    {claim.warrants?.map((warrant) => (
                      <li key={warrant}>{warrant}</li>
                    ))}
                  </ul>
                </TableCell>
              </TableRow>
              <TableRow>
                <TableCell>Qualifiers</TableCell>
                <TableCell>
                  <ul className="list-disc pl-5">
                    {claim.qualifiers?.map((qualifier) => (
                      <li key={qualifier}>{qualifier}</li>
                    ))}
                  </ul>
                </TableCell>
              </TableRow>
              <TableRow>
                <TableCell>Rebuttals</TableCell>
                <TableCell>
                  <ul className="list-disc pl-5">
                    {claim.rebuttals?.map((rebuttal) => (
                      <li key={rebuttal}>{rebuttal}</li>
                    ))}
                  </ul>
                </TableCell>
              </TableRow>
              <TableRow>
                <TableCell>Backing</TableCell>
                <TableCell>
                  <ul className="list-disc pl-5">
                    {claim.backing?.map((backing) => (
                      <li key={backing}>{backing}</li>
                    ))}
                  </ul>
                </TableCell>
              </TableRow>
              <TableRow>
                <TableCell>Warrant Expression</TableCell>
                <TableCell>{claim.warrantExpression}</TableCell>
              </TableRow>
            </TableBody>
          </Table>
        </div>
      )}
    </div>
  );
}
