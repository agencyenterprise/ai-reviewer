'use client';

import { Button } from '@/components/ui/button';
import { ArrowRight, Eye, X } from 'lucide-react';
import Link from 'next/link';
import { useState } from 'react';

interface OwnerSharedBannerProps {
  projectId: string;
}

/**
 * The strip an owner sees on their own share link: this is the public version,
 * and here is the way back to the editable one. Sits in the project chrome with
 * the other notices, so it reads as a fact about the view rather than the page.
 */
export function OwnerSharedBanner({ projectId }: OwnerSharedBannerProps) {
  const [isDismissed, setIsDismissed] = useState(false);

  if (isDismissed) {
    return null;
  }

  return (
    <div className="flex shrink-0 flex-wrap items-center gap-x-3 gap-y-2 border-b bg-blue-50 px-3 py-2 dark:bg-blue-950/30">
      <div className="flex min-w-0 grow basis-96 items-start gap-2">
        <Eye className="mt-0.5 size-4 shrink-0 text-blue-700 dark:text-blue-400" />
        <p className="min-w-0 text-sm">
          <strong className="font-medium">You&apos;re viewing the shared version</strong>
          <span className="text-muted-foreground"> of your project. Readers with the link see exactly this.</span>
        </p>
      </div>

      <div className="ml-auto flex shrink-0 items-center gap-2">
        <Button size="xs" className="h-6" asChild>
          <Link href={`/projects/${projectId}`}>
            Edit project
            <ArrowRight className="size-3" />
          </Link>
        </Button>
        <Button
          variant="ghost"
          size="icon"
          className="size-6 text-muted-foreground"
          onClick={() => setIsDismissed(true)}
          aria-label="Dismiss banner"
        >
          <X className="size-3.5" />
        </Button>
      </div>
    </div>
  );
}
