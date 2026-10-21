import { auth } from '@/auth';
import { REQUEST_PATH_HEADER, signInUrl } from '@/lib/sign-in-redirect';
import { getCurrentUserInfoApiUsersMeGet, UserRole } from '@/lib/generated-api';
import { serverApiUrl } from '@/lib/server-api-url';
import { headers } from 'next/headers';
import { redirect } from 'next/navigation';

async function AdminLayout({ children }: { children: React.ReactNode }) {
  const session = await auth();

  if (!session || !session.user || !session.accessToken) {
    redirect(signInUrl((await headers()).get(REQUEST_PATH_HEADER)));
  }

  const user = await getCurrentUserInfoApiUsersMeGet({ baseUrl: serverApiUrl, auth: session.accessToken });

  if (!user || user.role !== UserRole.Admin) {
    redirect('/');
  }

  return children;
}

export default AdminLayout;
