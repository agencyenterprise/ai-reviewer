'use client';

import { FileUpload } from '../../ui/file-upload';
import { FileListItem } from './file-list-item';

export interface UploadSectionProps {
  title: string;
  description: string;
  badgeText: string;
  badgeClass: string;
  onFilesChange: (files: File[]) => void;
  multiple: boolean;
  files: File[];
  fileType: 'main' | 'supporting';
  onRemoveFile: (index?: number) => void;
}

export const UploadSection = ({
  title,
  description,
  badgeText,
  badgeClass,
  onFilesChange,
  multiple,
  files,
  fileType,
  onRemoveFile,
}: UploadSectionProps) => (
  <div className="space-y-6">
    <div className="space-y-2">
      <div className="flex items-center gap-3">
        <h3 className="text-lg font-semibold">{title}</h3>
        <span className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium ${badgeClass}`}>
          {badgeText}
        </span>
      </div>
      <p className="text-sm text-muted-foreground">{description}</p>
    </div>

    <FileUpload
      onFilesChange={onFilesChange}
      accept=".pdf,.doc,.docx,.txt,.md,.rtf,.html"
      multiple={multiple}
      maxSize={10}
      className="h-36 transition-all duration-200"
      compact
    />

    {files.length > 0 && (
      <div className="mt-4 space-y-2">
        {files.map((file, index) => (
          <FileListItem
            key={multiple ? index : 'single'}
            file={file}
            type={fileType}
            onRemove={() => onRemoveFile(multiple ? index : undefined)}
          />
        ))}
      </div>
    )}
  </div>
);
