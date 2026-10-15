import { auth } from '@/auth';
import { REQUEST_PATH_HEADER, signInUrl } from '@/lib/sign-in-redirect';
import { headers } from 'next/headers';
import { redirect } from 'next/navigation';

async function AuthenticatedLayout({ children }: { children: React.ReactNode }) {
  const session = await auth();

  if (!session || !session.user) {
    redirect(signInUrl((await headers()).get(REQUEST_PATH_HEADER)));
  }

  return children;
}

export default AuthenticatedLayout;
