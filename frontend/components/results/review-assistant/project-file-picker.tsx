'use client';

import { GROUP, FileGroup, fileGroup, revisionLabel, sortFiles } from '@/components/results/files/role';
import { FileTypeIcon } from '@/components/shared/file-type-icon';
import { Checkbox } from '@/components/ui/checkbox';
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible';
import { FileListItem, FileRole } from '@/lib/generated-api';
import { ChevronRight } from 'lucide-react';

/** Sources are often dozens of cited papers, so they start folded away. */
const ORDER: { group: FileGroup; folded: boolean }[] = [
  { group: 'main', folded: false },
  { group: 'review', folded: false },
  { group: 'memo', folded: false },
  { group: 'response', folded: false },
  { group: 'source', folded: true },
];

interface ProjectFilePickerProps {
  files: FileListItem[];
  currentRevision: number;
  selected: ReadonlySet<string>;
  onToggle: (fileId: string) => void;
  disabled?: boolean;
}

/** The project's documents as a checklist, grouped the way the Files tab groups them. */
export function ProjectFilePicker({ files, currentRevision, selected, onToggle, disabled }: ProjectFilePickerProps) {
  const readable = sortFiles(files.filter((file) => file.role !== FileRole.SupportingCandidate));
  if (readable.length === 0) {
    return <p className="text-xs text-muted-foreground">This project has no documents yet.</p>;
  }

  return (
    <div className="space-y-3">
      {ORDER.map(({ group, folded }) => {
        const inGroup = readable.filter((file) => fileGroup(file.role) === group);
        if (inGroup.length === 0) return null;
        const pickedHere = inGroup.filter((file) => selected.has(file.id)).length;
        return (
          <Collapsible key={group} defaultOpen={!folded || pickedHere > 0}>
            <CollapsibleTrigger className="group flex w-full cursor-pointer items-center gap-1.5 text-left">
              <ChevronRight className="size-3 text-muted-foreground transition-transform group-data-[state=open]:rotate-90" />
              <span className="text-[11px] font-medium tracking-wide text-muted-foreground uppercase">
                {GROUP[group].plural}
              </span>
              <span className="font-mono text-[11px] text-muted-foreground tabular-nums">
                {pickedHere > 0 ? `${pickedHere}/${inGroup.length}` : inGroup.length}
              </span>
            </CollapsibleTrigger>
            <CollapsibleContent>
              <ul className="mt-1.5 space-y-px">
                {inGroup.map((file) => (
                  <li key={file.id}>
                    <label className="flex cursor-pointer items-center gap-2.5 rounded-md px-2 py-1.5 hover:bg-accent/40">
                      <Checkbox
                        checked={selected.has(file.id)}
                        onCheckedChange={() => onToggle(file.id)}
                        disabled={disabled}
                        aria-label={`Use ${file.file_name}`}
                      />
                      <FileTypeIcon fileType={file.file_type} />
                      <span className="min-w-0 flex-1 truncate text-[13px]">{file.file_name}</span>
                      {revisionLabel(file, currentRevision) && (
                        <span className="shrink-0 text-[11px] text-muted-foreground">
                          {revisionLabel(file, currentRevision)}
                        </span>
                      )}
                    </label>
                  </li>
                ))}
              </ul>
            </CollapsibleContent>
          </Collapsible>
        );
      })}
    </div>
  );
}
