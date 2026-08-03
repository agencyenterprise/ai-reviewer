/**
 * Model registry for the /chat page.
 *
 * This module is intentionally free of any AI SDK / component imports so it can
 * be shared between the client (model selector) and the server (`/api/chat`
 * route). The list mirrors the OpenAI models the backend exposes in
 * `lib/config/llm_models.py`.
 */

export interface ChatModel {
  id: string;
  name: string;
}

export const CHAT_MODELS: ChatModel[] = [
  { id: 'gpt-5.5', name: 'GPT-5.5' },
  { id: 'gpt-5.4', name: 'GPT-5.4' },
  { id: 'gpt-5.4-mini', name: 'GPT-5.4 Mini' },
  { id: 'gpt-4.1', name: 'GPT-4.1' },
];

export const DEFAULT_MODEL_ID = 'gpt-5.5';

export function getChatModel(id: string): ChatModel | undefined {
  return CHAT_MODELS.find((model) => model.id === id);
}
