'use client';

import { useWorkflowTypes } from '@/lib/hooks/use-workflow-types';
import { Globe } from 'lucide-react';
import { useMemo } from 'react';

/**
 * The assessments as the questions they are.
 *
 * Most of their descriptions already open with one — "Are your references
 * accurate?", "Does your reasoning hold up?" — because that is what an
 * assessment is: a question put to a draft. So the catalogue is split at the
 * question mark and the question is given the line, with the rest as the answer
 * to "how would you even check that".
 *
 * Read from the API rather than written here, so the page cannot promise a
 * check that no longer exists, or miss one that was added this week.
 */
export function QuestionWall() {
  const { categories, workflowTypes } = useWorkflowTypes();

  const groups = useMemo(() => {
    const byType = new Map(workflowTypes.map((type) => [type.type, type]));
    return categories
      .map((category) => ({
        label: category.label,
        items: category.workflows
          .map((type) => byType.get(type))
          .filter((type) => !!type && !type.is_internal && !type.is_experimental)
          .map((type) => type!),
      }))
      .filter((group) => group.items.length > 0);
  }, [categories, workflowTypes]);

  if (groups.length === 0) return null;

  return (
    <div className="space-y-10">
      {groups.map((group) => (
        <section key={group.label}>
          <h3 className="mb-3 font-mono text-[11px] tracking-[0.12em] text-muted-foreground uppercase">
            {group.label}
          </h3>

          <ul className="divide-y border-y">
            {group.items.map((type) => {
              const { headline, body } = readEntry(type.name, type.description);

              return (
                <li key={type.type} className="py-4">
                  <p className="text-base leading-snug font-medium text-balance sm:text-lg">{headline}</p>
                  <p className="mt-1 flex flex-wrap items-center gap-x-2 gap-y-1">
                    <span className="font-mono text-[11px] tracking-wide text-muted-foreground uppercase">
                      {type.name}
                    </span>
                    {type.needs_web_search && (
                      <span className="inline-flex items-center gap-1 rounded-sm bg-blue-50 px-1.5 py-0.5 font-mono text-[10px] tracking-wide text-blue-700 uppercase dark:bg-blue-950/50 dark:text-blue-300">
                        <Globe className="size-2.5" aria-hidden />
                        Searches the web
                      </span>
                    )}
                  </p>
                  {body && <p className="mt-1.5 text-sm leading-relaxed text-muted-foreground">{body}</p>}
                </li>
              );
            })}
          </ul>
        </section>
      ))}
    </div>
  );
}

/**
 * Most descriptions open with the question the assessment puts to a draft, and
 * that question is what earns the line. The few that open with a statement get
 * their name on the line instead — promoting a long sentence to headline size
 * reads worse than the name does, and this section claims to be questions.
 */
function readEntry(name: string, description: string): { headline: string; body: string } {
  const match = description.match(/^([\s\S]+?\?)\s*([\s\S]*)$/);
  if (!match) return { headline: name, body: description };
  return { headline: match[1], body: match[2] };
}
