'use client';

import { Switch } from '@/components/ui/switch';
import { useTheme } from 'next-themes';
import { useSyncExternalStore } from 'react';

const subscribeNever = () => () => {};

export function ThemeToggle() {
  const { resolvedTheme, setTheme } = useTheme();
  // next-themes resolves the theme on the client, so we render a neutral
  // state on the server and during hydration to avoid an SSR/CSR mismatch.
  const mounted = useSyncExternalStore(
    subscribeNever,
    () => true,
    () => false,
  );

  return (
    <Switch
      checked={mounted ? resolvedTheme === 'dark' : false}
      onCheckedChange={(checked) => setTheme(checked ? 'dark' : 'light')}
      disabled={!mounted}
      aria-label="Toggle dark mode"
    />
  );
}
