'use client';

import { AddinPane } from '@/components/addin/addin-pane';
import { AddinSignIn } from '@/components/addin/addin-sign-in';
import { installFakeApi } from '@/lib/addin/preview/fake-api';
import { installFakeOffice } from '@/lib/addin/preview/fake-office';
import { PreviewScenario, scenarioFrom, scenarioQuery } from '@/lib/addin/preview/scenario';
import { officeReady } from '@/lib/addin/use-office-init';
import { useQuery } from '@tanstack/react-query';
import { useSearchParams } from 'next/navigation';

/**
 * The real Word pane outside Word, for working on it in a browser: the same sign-in and
 * pane components as `/addin`, with Office and the add-in's API answered in the page
 * (`lib/addin/preview/`). Each scenario is a link, so any state can be shared or reloaded.
 */
export function PanePreview() {
  const scenario = scenarioFrom(useSearchParams());
  const query = scenarioQuery(scenario);
  // Installed once per scenario, before the pane mounts: it asks for its data at once.
  const ready = useQuery({
    queryKey: ['addin-preview', query],
    queryFn: async () => {
      installFakeApi(scenario);
      await officeReady().catch(() => null);
      installFakeOffice();
      return true;
    },
    staleTime: Infinity,
    gcTime: 0,
  });

  return (
    <div className="flex min-h-screen gap-8 bg-muted p-6">
      <Controls scenario={scenario} />
      <div className="flex flex-col gap-2">
        <p className="text-xs text-muted-foreground">
          Pane at {scenario.width}px, as Word shows it. Reload to start the scenario over.
        </p>
        <div
          className="flex h-[min(720px,calc(100vh-5rem))] flex-col overflow-hidden border bg-card shadow"
          style={{ width: scenario.width }}
        >
          {ready.data && (
            <AddinSignIn key={query} prompt="Sign in to chat with Draft Detective about this document.">
              {(session) => <AddinPane session={session} />}
            </AddinSignIn>
          )}
        </div>
      </div>
    </div>
  );
}

const CHOICES: {
  label: string;
  field: keyof PreviewScenario;
  options: [string, PreviewScenario[keyof PreviewScenario]][];
}[] = [
  {
    label: 'Teams bot',
    field: 'teams',
    options: [
      ['Runs', true],
      ['Not set up', false],
    ],
  },
  {
    label: 'Waiting from Teams',
    field: 'waiting',
    options: [
      ['Nothing', 'none'],
      ['This document', 'here'],
      ['Other documents', 'elsewhere'],
      ['Both', 'both'],
    ],
  },
  {
    label: 'Conversation',
    field: 'chat',
    options: [
      ['New', 'empty'],
      ['An answer', 'conversation'],
      ['Waiting on a card', 'card'],
    ],
  },
  {
    label: 'OpenAI key',
    field: 'key',
    options: [
      ['Set', true],
      ['Missing', false],
    ],
  },
  {
    label: 'Width',
    field: 'width',
    options: [
      ['320', 320],
      ['340', 340],
      ['400', 400],
    ],
  },
];

function Controls({ scenario }: { scenario: PreviewScenario }) {
  return (
    <aside className="flex w-64 shrink-0 flex-col gap-4 text-sm">
      <div>
        <h1 className="font-semibold">Word pane preview</h1>
        <p className="mt-1 text-xs text-muted-foreground">
          The real pane, with Word and the API stood in for. Messages are answered from canned replies; asking for
          comments or changes offers a card. Apply cannot write without Word.
        </p>
      </div>
      {CHOICES.map(({ label, field, options }) => (
        <div key={field}>
          <p className="mb-1 text-xs font-medium text-muted-foreground">{label}</p>
          <div className="flex flex-wrap gap-1">
            {options.map(([name, value]) => {
              const active = scenario[field] === value;
              return (
                // A full page load, not a client navigation: each scenario starts from nothing.
                <a
                  key={name}
                  href={`/addin/preview${scenarioQuery({ ...scenario, [field]: value })}`}
                  className={`rounded-md border px-2 py-1 text-xs ${active ? 'border-primary bg-primary text-primary-foreground' : 'bg-card hover:bg-accent'}`}
                >
                  {name}
                </a>
              );
            })}
          </div>
        </div>
      ))}
      <a href="/addin/preview" className="text-xs text-muted-foreground underline">
        Back to the defaults
      </a>
    </aside>
  );
}
