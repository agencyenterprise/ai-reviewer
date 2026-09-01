'use client';

import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip';
import { listProjectsEndpointApiProjectsGet } from '@/lib/generated-api';
import { useQuery } from '@tanstack/react-query';
import { FolderOpen, Loader2, Plus, Search } from 'lucide-react';
import Link from 'next/link';
import { ReactNode, useMemo, useState } from 'react';
import { ProjectRow } from './project-row';

/**
 * Every project you have. No rail: a project is either the one you came for or
 * it is not, and the row already says what each is doing — a column of filters
 * beside a searchable list would be furniture rather than help.
 */
export function ProjectsView() {
  const [search, setSearch] = useState('');

  const {
    data: projects,
    isLoading,
    error,
  } = useQuery({
    queryKey: ['projects'],
    refetchInterval: 3000,
    queryFn: () => listProjectsEndpointApiProjectsGet(),
  });

  const items = useMemo(() => projects ?? [], [projects]);

  const shown = useMemo(() => {
    const query = search.trim().toLowerCase();
    return (
      items
        .filter((item) => !query || item.project.title.toLowerCase().includes(query))
        // new Date() is load-bearing despite the generated type saying Date: the
        // date transformers hey-api generates are never wired into the SDK, so
        // what actually arrives is an ISO string, and .getTime() on one is NaN.
        .sort((a, b) => new Date(b.project.last_updated_at).getTime() - new Date(a.project.last_updated_at).getTime())
    );
  }, [items, search]);

  const filtered = search.trim() !== '';

  return (
    <main className="flex min-h-0 min-w-0 flex-1 flex-col">
      {/* The bar spans the window so its rule does; its contents line up with
          the list on the same centred column. */}
      <div className="flex h-10 shrink-0 items-center border-b px-4">
        <div className="mx-auto flex w-full max-w-5xl items-center gap-2">
          <span className="shrink-0 truncate text-xs text-muted-foreground">
            {filtered ? `${shown.length} of ${items.length} projects` : `${items.length} projects`}
          </span>

          <div className="relative ml-2 hidden max-w-64 min-w-0 flex-1 sm:block">
            <Search className="absolute top-1/2 left-2 size-3.5 -translate-y-1/2 text-muted-foreground" />
            <Input
              type="search"
              value={search}
              onChange={(event) => setSearch(event.target.value)}
              placeholder="Search projects"
              className="h-7 pl-7 text-xs"
            />
          </div>

          <div className="ml-auto flex shrink-0 items-center gap-1.5">
            <Tooltip>
              <TooltipTrigger asChild>
                <Button size="xs" asChild aria-label="New project">
                  <Link href="/new">
                    <Plus className="size-3" />
                    <span className="hidden sm:inline">New project</span>
                  </Link>
                </Button>
              </TooltipTrigger>
              <TooltipContent>Upload a draft and start a project</TooltipContent>
            </Tooltip>
          </div>
        </div>
      </div>

      <div className="min-h-0 flex-1 overflow-y-auto">
        {isLoading ? (
          <Centred>
            <Loader2 className="mx-auto size-5 animate-spin text-muted-foreground" />
            <p className="mt-2 text-xs text-muted-foreground">Loading your projects…</p>
          </Centred>
        ) : error ? (
          <Centred>
            <p className="text-sm text-destructive">{error.message}</p>
          </Centred>
        ) : items.length === 0 ? (
          <Centred>
            <FolderOpen className="mx-auto size-7 text-muted-foreground" />
            <p className="mt-2 text-sm font-medium">No projects yet</p>
            <p className="mt-1 text-xs leading-relaxed text-muted-foreground">
              A project is one draft and everything found in it. Upload a document to start the first.
            </p>
            <Button size="sm" className="mt-3" asChild>
              <Link href="/new">
                <Plus className="size-3.5" />
                New project
              </Link>
            </Button>
          </Centred>
        ) : shown.length === 0 ? (
          <div className="space-y-1 py-12 text-center text-sm text-muted-foreground">
            <p>No projects match that search.</p>
            <Button variant="link" size="sm" className="text-xs" onClick={() => setSearch('')}>
              Clear search
            </Button>
          </div>
        ) : (
          <div className="mx-auto max-w-5xl">
            {shown.map((item) => (
              <ProjectRow key={item.project.id} item={item} />
            ))}
          </div>
        )}
      </div>
    </main>
  );
}

function Centred({ children }: { children: ReactNode }) {
  return (
    <div className="flex h-full items-center justify-center p-8">
      <div className="max-w-xs text-center">{children}</div>
    </div>
  );
}
