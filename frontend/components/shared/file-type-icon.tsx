import { FileText } from 'lucide-react';

/** Document icon tinted by file type, so a file list scans at a glance. */
export function FileTypeIcon({ fileType, className }: { fileType?: string | null; className?: string }) {
  const normalizedType = fileType?.toLowerCase() || '';

  if (normalizedType.includes('pdf') || normalizedType === 'application/pdf') {
    return <FileText className={className ?? 'flex-shrink-0 size-4 text-red-700'} />;
  }

  if (
    normalizedType.includes('docx') ||
    normalizedType.includes('doc') ||
    normalizedType === 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' ||
    normalizedType === 'application/msword'
  ) {
    return <FileText className={className ?? 'flex-shrink-0 size-4 text-blue-700'} />;
  }

  return <FileText className={className ?? 'flex-shrink-0 size-4 text-muted-foreground'} />;
}
