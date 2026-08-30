'use client';

import * as React from 'react';
import * as RadioGroupPrimitive from '@radix-ui/react-radio-group';
import { CircleIcon } from 'lucide-react';
import { cn } from '@/lib/utils';
import { ReactNode } from 'react';

export { RadioGroup } from './radio-group';

interface RadioGroupItemWithDescriptionProps {
  id: string;
  value: string;
  label: string;
  description: string;
  disabled?: boolean;
  /** Rendered under the description, for options that need more than a line. */
  help?: ReactNode;
}

export function RadioGroupItemWithDescription({
  id,
  value,
  label,
  description,
  disabled = false,
  help,
}: RadioGroupItemWithDescriptionProps) {
  return (
    <label
      htmlFor={id}
      className={cn(
        'border rounded-lg p-4 cursor-pointer hover:bg-accent/50 transition-all block space-y-1',
        value === id ? 'border-primary border-1' : 'border',
        disabled && 'cursor-not-allowed opacity-50',
      )}
    >
      <div className="flex items-center space-x-2">
        <RadioGroupPrimitive.Item
          id={id}
          value={id}
          disabled={disabled}
          data-slot="radio-group-item"
          className={cn(
            'border-input text-primary focus-visible:border-ring focus-visible:ring-ring/50 aria-invalid:ring-destructive/20 dark:aria-invalid:ring-destructive/40 aria-invalid:border-destructive dark:bg-input/30 aspect-square size-4 shrink-0 rounded-full border shadow-xs transition-[color,box-shadow] outline-none focus-visible:ring-[3px] disabled:cursor-not-allowed disabled:opacity-50',
          )}
        >
          <RadioGroupPrimitive.Indicator
            data-slot="radio-group-indicator"
            className="relative flex items-center justify-center"
          >
            <CircleIcon className="fill-primary absolute top-1/2 left-1/2 size-2 -translate-x-1/2 -translate-y-1/2" />
          </RadioGroupPrimitive.Indicator>
        </RadioGroupPrimitive.Item>
        <span className={cn('text-sm font-medium leading-none select-none', disabled && 'opacity-70')}>{label}</span>
      </div>
      <p className="text-sm text-muted-foreground pl-6">{description}</p>
      {help && <p className="text-sm pl-6">{help}</p>}
    </label>
  );
}
