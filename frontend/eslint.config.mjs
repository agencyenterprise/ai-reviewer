import { dirname } from 'path';
import { fileURLToPath } from 'url';
import { FlatCompat } from '@eslint/eslintrc';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const compat = new FlatCompat({
  baseDirectory: __dirname,
});

const eslintConfig = [
  ...compat.extends('next/core-web-vitals', 'next/typescript', 'prettier'),
  {
    ignores: [
      'node_modules/**',
      '.next/**',
      'out/**',
      'build/**',
      'next-env.d.ts',
      'lib/generated-api/**',
      // Copied from the assistant-ui registry and kept as upstream ships it. Its code targets
      // newer react-hooks rules than ours, so it is type-checked but not linted.
      'components/assistant-ui/elements/**',
      'components/assistant-ui/utils/**',
      'hooks/use-attachment-src.ts',
      'hooks/use-copy-to-clipboard.ts',
    ],
  },
];

export default eslintConfig;
