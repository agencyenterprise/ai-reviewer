'use client';

import { Badge } from '@/components/ui/badge';
import { DocumentChunkOutput } from '@/lib/generated-api';
import { Loader2, CheckCircle2, Clock } from 'lucide-react';
import * as React from 'react';

const COMPLETE_BADGE_FADE_START_MS = 4000;
const COMPLETE_BADGE_REMOVE_MS = 5000;

type ChunkStatus = 'queued' | 'analyzing' | 'complete';

export function getChunkStatus(chunk: DocumentChunkOutput): ChunkStatus {
  const hasClaims = !!chunk.claims;
  const hasClaimsData = (chunk.claims?.claims?.length || 0) > 0;
  const hasCommonKnowledgeResults = (chunk.claimCommonKnowledgeResults?.length || 0) > 0;

  if (!hasClaims) return 'queued';
  if (!hasClaimsData || !hasCommonKnowledgeResults) return 'analyzing';
  return 'complete';
}

interface ChunkStatusBadgeProps {
  chunk: DocumentChunkOutput;
  isWorkflowRunning: boolean;
}

export function ChunkStatusBadge({ chunk, isWorkflowRunning }: ChunkStatusBadgeProps) {
  const status = getChunkStatus(chunk);
  const [showCompleteBadge, setShowCompleteBadge] = React.useState(false);
  const [fadeOut, setFadeOut] = React.useState(false);
  const wasRunningRef = React.useRef(isWorkflowRunning);

  React.useEffect(() => {
    if (status === 'complete' && isWorkflowRunning) {
      setShowCompleteBadge(true);
      setFadeOut(false);

      const fadeTimer = setTimeout(() => setFadeOut(true), COMPLETE_BADGE_FADE_START_MS);
      const removeTimer = setTimeout(() => setShowCompleteBadge(false), COMPLETE_BADGE_REMOVE_MS);

      return () => {
        clearTimeout(fadeTimer);
        clearTimeout(removeTimer);
      };
    }
  }, [status, isWorkflowRunning]);

  React.useEffect(() => {
    if (!isWorkflowRunning && wasRunningRef.current && status === 'complete') {
      setShowCompleteBadge(true);
      setFadeOut(false);

      const fadeTimer = setTimeout(() => setFadeOut(true), COMPLETE_BADGE_FADE_START_MS);
      const removeTimer = setTimeout(() => setShowCompleteBadge(false), COMPLETE_BADGE_REMOVE_MS);

      return () => {
        clearTimeout(fadeTimer);
        clearTimeout(removeTimer);
      };
    }
    wasRunningRef.current = isWorkflowRunning;
  }, [isWorkflowRunning, status]);

  if (!wasRunningRef.current && !isWorkflowRunning) {
    return null;
  }

  if (!isWorkflowRunning && !showCompleteBadge) {
    return null;
  }

  if (showCompleteBadge && status === 'complete') {
    return (
      <Badge
        variant="secondary"
        className={`gap-1 transition-all duration-1000 ease-out ${
          fadeOut ? 'opacity-0 scale-95' : 'opacity-100 scale-100'
        }`}
      >
        <CheckCircle2 className="h-3 w-3" />
        Complete
      </Badge>
    );
  }

  if (!isWorkflowRunning) {
    return null;
  }

  switch (status) {
    case 'queued':
      return (
        <Badge variant="outline" className="gap-1">
          <Clock className="h-3 w-3" />
          Queued
        </Badge>
      );
    case 'analyzing':
      return (
        <Badge variant="outline" className="gap-1 border-primary/50 text-primary">
          <Loader2 className="h-3 w-3 animate-spin" />
          Analyzing
        </Badge>
      );
    default:
      return null;
  }
}
