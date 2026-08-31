'use client';

import { DeleteProjectDialog } from '@/components/delete-project-dialog';
import { ProjectListItem } from '@/lib/generated-api';
import { useWorkflowTypes } from '@/lib/hooks/use-workflow-types';
import { cn } from '@/lib/utils';
import { formatDistanceToNow } from 'date-fns';
import Link from 'next/link';
import { useMemo } from 'react';
import { PROJECT_STATE, readProjectState } from './project-state';

/**
 * One project, at the density of a list you scan rather than a card you read.
 * The title carries the link; everything beside it answers the question you
 * came to the list with — is this one finished, and is it waiting on me.
 */
export function ProjectRow({ item }: { item: ProjectListItem }) {
  const { project } = item;
  const { isWorkflowTypeVisible } = useWorkflowTypes();

  const state = readProjectState(item);
  const style = PROJECT_STATE[state];

  const assessments = useMemo(() => {
    const runs = (item.workflow_runs ?? []).filter((run) => isWorkflowTypeVisible(run.type));
    return new Set(runs.map((run) => run.type)).size;
  }, [item.workflow_runs, isWorkflowTypeVisible]);

  return (
    <div className="group hover:bg-accent/40 relative flex items-center gap-3 border-b px-4 py-2.5 transition-colors">
      <span className={cn('block size-2 shrink-0 rounded-full', style.dot)} aria-hidden />

      <div className="min-w-0 flex-1">
        <Link href={`/v2/projects/${project.id}`} className="block truncate text-[13.5px] font-medium hover:underline">
          {/* Stretched over the row so the whole line is the target, while the
              controls on the right stay clickable in their own right. */}
          <span className="absolute inset-0" aria-hidden />
          {project.title}
        </Link>

        <p className="mt-0.5 flex flex-wrap items-center gap-x-2 gap-y-0.5 text-[11.5px] text-muted-foreground">
          <span className={style.text}>{style.label}</span>
          <span aria-hidden>·</span>
          <span>
            {assessments} {assessments === 1 ? 'assessment' : 'assessments'}
          </span>
          {(project.current_revision ?? 1) > 1 && (
            <>
              <span aria-hidden>·</span>
              <span>Revision {project.current_revision}</span>
            </>
          )}
          <span aria-hidden>·</span>
          <span>Created {formatDistanceToNow(project.created_at, { addSuffix: true })}</span>
        </p>
      </div>

      <span className="hidden shrink-0 text-[11.5px] text-muted-foreground sm:block">
        {/* Labelled: the row now carries two dates, and "2 days ago" beside
            "Created 9 days ago" is a riddle without it. */}
        Updated {formatDistanceToNow(project.last_updated_at, { addSuffix: true })}
      </span>

      {/* Above the stretched link, so deleting is not the same click as opening. */}
      <span className="relative z-10 opacity-0 transition-opacity group-focus-within:opacity-100 group-hover:opacity-100">
        <DeleteProjectDialog projectId={project.id} projectTitle={project.title} />
      </span>
    </div>
  );
}
