'use client';

import * as React from 'react';
import { ChevronDown, ChevronRight } from 'lucide-react';

interface CollapsibleFeedbackProps {
  shouldMinimize: boolean;
  isExpanded: boolean;
  onToggle: () => void;
  buttonText: string;
  children: React.ReactNode;
  expandedContent: React.ReactNode;
  className?: string;
}

export function CollapsibleFeedback({
  shouldMinimize,
  isExpanded,
  onToggle,
  buttonText,
  children,
  expandedContent,
  className = '',
}: CollapsibleFeedbackProps) {
  if (shouldMinimize) {
    return (
      <div className={`mt-1 ${className}`}>
        {children}
        <button
          onClick={onToggle}
          className="flex items-center gap-1 text-xs text-amber-600 hover:text-amber-800 transition-colors"
        >
          {isExpanded ? <ChevronDown className="h-3 w-3" /> : <ChevronRight className="h-3 w-3" />}
          <span className="underline">{buttonText}</span>
        </button>
        {isExpanded && <div className="mt-2 ml-4">{expandedContent}</div>}
      </div>
    );
  }

  return <div className={className}>{children}</div>;
}
