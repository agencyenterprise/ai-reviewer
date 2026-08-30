'use client';

import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip';
import { cn } from '@/lib/utils';
import { Check, SquarePenIcon, X } from 'lucide-react';
import * as React from 'react';

export interface EditableTitleProps {
  title: string;
  onSave: (newTitle: string) => Promise<void> | void;
  className?: string;
  titleClassName?: string;
  disabled?: boolean;
  isLoading?: boolean;
}

export function EditableTitle({
  title,
  onSave,
  className,
  titleClassName,
  disabled = false,
  isLoading = false,
}: EditableTitleProps) {
  const [isEditing, setIsEditing] = React.useState(false);
  const [editedTitle, setEditedTitle] = React.useState(title);
  const [isSaving, setIsSaving] = React.useState(false);
  const inputRef = React.useRef<HTMLInputElement>(null);
  const isCancelingRef = React.useRef(false);

  React.useEffect(() => {
    setEditedTitle(title);
  }, [title]);

  React.useEffect(() => {
    if (isEditing && inputRef.current) {
      inputRef.current.focus();
      inputRef.current.select();
    }
  }, [isEditing]);

  const handleStartEdit = () => {
    if (disabled || isLoading) return;
    setEditedTitle(title);
    setIsEditing(true);
  };

  const handleCancel = () => {
    isCancelingRef.current = true;
    setEditedTitle(title);
    setIsEditing(false);
    // Reset the flag after a short delay to allow blur handler to check it
    setTimeout(() => {
      isCancelingRef.current = false;
    }, 100);
  };

  const handleSave = async () => {
    const trimmedTitle = editedTitle.trim();
    if (!trimmedTitle) {
      handleCancel();
      return;
    }

    if (trimmedTitle === title) {
      setIsEditing(false);
      return;
    }

    setIsSaving(true);
    try {
      await onSave(trimmedTitle);
      setIsEditing(false);
    } catch (error) {
      // On error, keep editing mode and let the parent handle the error
      console.error('Failed to save title:', error);
    } finally {
      setIsSaving(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      handleSave();
    } else if (e.key === 'Escape') {
      e.preventDefault();
      handleCancel();
    }
  };

  if (isEditing) {
    return (
      <div className={cn('flex items-center gap-2 w-full', className)}>
        <Input
          ref={inputRef}
          value={editedTitle}
          onChange={(e) => setEditedTitle(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={isSaving}
          className={cn('flex-1 w-full', titleClassName)}
        />
        <Button variant="ghost" size="icon" onClick={handleSave} disabled={isSaving} className="h-8 w-8">
          <Check className="h-4 w-4" />
        </Button>
        <Button variant="ghost" size="icon" onClick={handleCancel} disabled={isSaving} className="h-8 w-8">
          <X className="h-4 w-4" />
        </Button>
      </div>
    );
  }

  return (
    <div className={cn('flex items-center gap-2', className)}>
      <h1 className={cn(titleClassName)}>{title}</h1>
      {!disabled && !isLoading && (
        <Tooltip>
          <TooltipTrigger asChild>
            <Button variant="ghost" size="icon" onClick={handleStartEdit} className="h-8 w-8" aria-label="Edit title">
              <SquarePenIcon className="h-4 w-4" />
            </Button>
          </TooltipTrigger>
          <TooltipContent>Rename this project</TooltipContent>
        </Tooltip>
      )}
    </div>
  );
}
