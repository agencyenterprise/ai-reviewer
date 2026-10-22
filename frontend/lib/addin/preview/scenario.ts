/**
 * What the pane preview (`/addin/preview`) pretends: which deployment, which account
 * state and which conversation the real pane runs against. Read from the page's query
 * string, so every state has a link of its own.
 */
export type PreviewScenario = {
  /** Whether the deployment runs the Teams bot. */
  teams: boolean;
  /** What waits from Teams: nothing, on this document, on others, or both. */
  waiting: 'none' | 'here' | 'elsewhere' | 'both';
  /** The conversation the pane opens on. */
  chat: 'empty' | 'conversation' | 'card';
  /** Whether there is an OpenAI key to answer with. */
  key: boolean;
  /** The pane's width, in pixels: Word's is about 320–400. */
  width: number;
};

export const DEFAULT_SCENARIO: PreviewScenario = {
  teams: true,
  waiting: 'none',
  chat: 'empty',
  key: true,
  width: 340,
};

const WAITING = ['none', 'here', 'elsewhere', 'both'] as const;
const CHAT = ['empty', 'conversation', 'card'] as const;

function oneOf<T extends string>(value: string | null, options: readonly T[], fallback: T): T {
  return options.includes(value as T) ? (value as T) : fallback;
}

export function scenarioFrom(params: URLSearchParams): PreviewScenario {
  const width = Number(params.get('width'));
  return {
    teams: params.get('teams') !== 'off',
    waiting: oneOf(params.get('waiting'), WAITING, DEFAULT_SCENARIO.waiting),
    chat: oneOf(params.get('chat'), CHAT, DEFAULT_SCENARIO.chat),
    key: params.get('key') !== 'missing',
    width: width >= 280 && width <= 600 ? width : DEFAULT_SCENARIO.width,
  };
}

/** The query string for a scenario, leaving out what is the default. */
export function scenarioQuery(scenario: PreviewScenario): string {
  const params = new URLSearchParams();
  if (!scenario.teams) params.set('teams', 'off');
  if (scenario.waiting !== DEFAULT_SCENARIO.waiting) params.set('waiting', scenario.waiting);
  if (scenario.chat !== DEFAULT_SCENARIO.chat) params.set('chat', scenario.chat);
  if (!scenario.key) params.set('key', 'missing');
  if (scenario.width !== DEFAULT_SCENARIO.width) params.set('width', String(scenario.width));
  const query = params.toString();
  return query ? `?${query}` : '';
}
