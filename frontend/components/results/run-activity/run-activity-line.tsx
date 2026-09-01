'use client';

/**
 * A hairline under the project header that sweeps while assessments run.
 *
 * The header button says what is running; this says *that* something is,
 * peripherally, without asking for a glance. Two pixels is the whole cost, and
 * unlike the toast it cannot cover anything.
 */
export function RunActivityLine({ active }: { active: boolean }) {
  if (!active) return null;

  return (
    <div className="bg-primary/15 relative h-0.5 shrink-0 overflow-hidden" aria-hidden="true">
      <div className="bg-primary run-activity-sweep absolute inset-y-0 w-1/3 rounded-full" />
    </div>
  );
}
