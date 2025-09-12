'use client';

import { FileText, X } from 'lucide-react';
import { Button } from '../../ui/button';
import { formatFileSize } from './utils';

export interface FileListItemProps {
  file: File;
  type: 'main' | 'supporting';
  onRemove: () => void;
}

export const FileListItem = ({ file, type, onRemove }: FileListItemProps) => {
  const isMain = type === 'main';
  const bgClass = isMain ? 'bg-primary/5 border-primary/20' : 'bg-muted/10 border-muted/20';
  const iconClass = isMain ? 'text-primary' : 'text-muted-foreground';
  const tagClass = isMain ? 'bg-primary/20 text-primary' : 'bg-muted/60 text-muted-foreground';

  return (
    <div className={`flex items-center justify-between p-3 border rounded-lg ${bgClass}`}>
      <div className="flex items-center gap-2 min-w-0 flex-1">
        <FileText className={`w-4 h-4 flex-shrink-0 ${iconClass}`} />
        <div className="min-w-0 flex-1">
          <p className="text-sm font-medium truncate">{file.name}</p>
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            <span className={`px-1.5 py-0.5 rounded ${tagClass}`}>{isMain ? 'Main' : 'Supporting'}</span>
            <span>{formatFileSize(file.size)}</span>
          </div>
        </div>
      </div>
      <Button
        variant="ghost"
        size="icon"
        onClick={onRemove}
        className="h-6 w-6 text-muted-foreground hover:text-destructive"
      >
        <X className="w-3 h-3" />
      </Button>
    </div>
  );
};
