'use client';

import * as React from 'react';
import { CheckCircle } from 'lucide-react';
import { cn } from '@/lib/utils';

export interface StepperProps {
  steps: Array<{
    id: string;
    title: string;
    description?: string;
  }>;
  currentStep: number;
  className?: string;
}

export function Stepper({ steps, currentStep, className }: StepperProps) {
  return (
    <nav aria-label="Progress" className={cn('w-full', className)}>
      <ol className="flex items-center justify-between">
        {steps.map((step, index) => {
          const stepNumber = index + 1;
          const isCompleted = stepNumber < currentStep;
          const isCurrent = stepNumber === currentStep;
          const isUpcoming = stepNumber > currentStep;

          return (
            <li key={step.id} className="flex items-center flex-1">
              <div className="flex items-center">
                <div
                  className={cn('flex items-center justify-center w-10 h-10 rounded-full transition-all', {
                    'bg-primary text-primary-foreground': isCompleted,
                    'bg-primary/20 text-primary border-2 border-primary': isCurrent,
                    'bg-muted text-muted-foreground border-2 border-muted': isUpcoming,
                  })}
                >
                  {isCompleted ? (
                    <CheckCircle className="w-5 h-5" />
                  ) : (
                    <span className="text-sm font-medium">{stepNumber}</span>
                  )}
                </div>
                <div className="ml-3 min-w-0 flex-1">
                  <div
                    className={cn('text-sm font-medium', {
                      'text-primary': isCurrent,
                      'text-foreground': isCompleted,
                      'text-muted-foreground': isUpcoming,
                    })}
                  >
                    {step.title}
                  </div>
                  {step.description && (
                    <div
                      className={cn('text-xs', {
                        'text-primary/70': isCurrent,
                        'text-muted-foreground': isCompleted || isUpcoming,
                      })}
                    >
                      {step.description}
                    </div>
                  )}
                </div>
              </div>
              {index < steps.length - 1 && (
                <div
                  className={cn('flex-1 h-0.5 mx-4 transition-colors', {
                    'bg-primary': isCompleted,
                    'bg-muted': !isCompleted,
                  })}
                />
              )}
            </li>
          );
        })}
      </ol>
    </nav>
  );
}
