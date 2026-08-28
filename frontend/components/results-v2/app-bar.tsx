'use client';

import { ProfileDropdown } from '@/components/layout/profile-dropdown';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';
import { LogInIcon, Moon, Plus, Sun } from 'lucide-react';
import { useSession } from 'next-auth/react';
import { useTheme } from 'next-themes';
import Link from 'next/link';
import { usePathname } from 'next/navigation';

const navigation = [
  { name: 'Projects', href: '/projects' },
  { name: 'About', href: '/about' },
];

/**
 * The application row for the v2 project view: where you are, how to start
 * something new, and who you are, in 44px. Replaces ApplicationShell's nav on
 * this route, which is why it carries the same links and account menu.
 */
export function AppBar() {
  const session = useSession();
  const pathname = usePathname();
  const { resolvedTheme, setTheme } = useTheme();
  const user = session.data?.user;
  const isLoadingUser = session.status === 'loading';

  return (
    <div className="flex h-11 shrink-0 items-center gap-1 border-b px-3">
      <Link href="/" className="text-primary mr-3 text-[15px] font-bold tracking-tight">
        Draft Detective
      </Link>

      <nav className="flex h-full items-center gap-1" aria-label="Main">
        {navigation.map((item) => {
          // The v2 tree mirrors the production routes one level down, so
          // /v2/projects/... still counts as being under Projects.
          const current = pathname.startsWith(item.href) || pathname.startsWith(`/v2${item.href}`);
          return (
            <Link
              key={item.name}
              href={item.href}
              aria-current={current ? 'page' : undefined}
              className={cn(
                'flex h-full items-center border-b-2 px-2 pt-0.5 text-[13px] font-medium transition-colors',
                current
                  ? 'border-primary text-foreground'
                  : 'border-transparent text-muted-foreground hover:text-foreground',
              )}
            >
              {item.name}
            </Link>
          );
        })}
      </nav>

      <Button asChild variant="outline" size="sm" className="ml-2 h-7 px-2.5 text-[12.5px]">
        <Link href="/new">
          <Plus className="size-3.5" />
          New project
        </Link>
      </Button>

      <div className="ml-auto flex items-center gap-1.5">
        {/* Dark mode sits in the bar rather than the account menu: it is a
            preference, not an account setting, and signed-out visitors want it too. */}
        <Button
          variant="ghost"
          size="icon"
          className="size-7"
          onClick={() => setTheme(resolvedTheme === 'dark' ? 'light' : 'dark')}
          aria-label="Toggle dark mode"
        >
          <Moon className="size-4 dark:hidden" />
          <Sun className="hidden size-4 dark:block" />
        </Button>

        {user ? (
          <ProfileDropdown user={user} size={26} showChevron includeThemeToggle={false} />
        ) : !isLoadingUser ? (
          <Button asChild variant="outline" size="sm" className="h-7 px-2.5 text-[12.5px]">
            <Link href="/api/auth/signin">
              <LogInIcon className="size-3.5" />
              Sign in
            </Link>
          </Button>
        ) : null}
      </div>
    </div>
  );
}
