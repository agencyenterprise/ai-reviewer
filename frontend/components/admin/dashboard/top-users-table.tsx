'use client';

import { Badge } from '@/components/ui/badge';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { ActiveUserItem, UserRole } from '@/lib/generated-api';
import { format } from 'date-fns';
import { toDate } from './format';

/** The people driving usage in the selected window. */
export function TopUsersTable({ users }: { users: ActiveUserItem[] }) {
  if (users.length === 0) {
    return <p className="text-sm text-muted-foreground">Nobody ran an assessment in this period.</p>;
  }

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>User</TableHead>
          <TableHead className="text-right">Assessments</TableHead>
          <TableHead className="text-right">Projects</TableHead>
          <TableHead className="text-right">Last active</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {users.map((user) => (
          <TableRow key={user.user_id}>
            <TableCell>
              <div className="flex items-center gap-2">
                <span className="font-medium">{user.name}</span>
                {user.role !== UserRole.User && <Badge variant="secondary">{user.role}</Badge>}
              </div>
              <span className="text-xs text-muted-foreground">{user.email}</span>
            </TableCell>
            <TableCell className="text-right tabular-nums">{user.workflow_runs.toLocaleString('en-US')}</TableCell>
            <TableCell className="text-right tabular-nums">{user.projects.toLocaleString('en-US')}</TableCell>
            <TableCell className="text-right text-muted-foreground">
              {format(toDate(user.last_active_at), 'MMM d, HH:mm')}
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}
