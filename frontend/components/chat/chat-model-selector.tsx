'use client';

import { OpenAILogo } from '@/components/assistant-ui/logos';
import { ModelSelector, type ModelOption } from '@/components/assistant-ui/model-selector';
import { CHAT_MODELS, DEFAULT_MODEL_ID } from '@/lib/chat-models';
import type { FC } from 'react';

// Options for the assistant-ui Model Selector. The selected model id is
// registered into assistant-ui's ModelContext and reaches the /chat adapter as
// `context.config.modelName`.
const MODEL_OPTIONS: ModelOption[] = CHAT_MODELS.map((model) => ({
  id: model.id,
  name: model.name,
  icon: <OpenAILogo className="size-4" />,
}));

export const ChatModelSelector: FC = () => {
  return <ModelSelector models={MODEL_OPTIONS} defaultValue={DEFAULT_MODEL_ID} variant="ghost" align="start" />;
};
