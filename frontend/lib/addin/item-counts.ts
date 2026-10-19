const plural = (count: number, one: string, many: string) => `${count} ${count === 1 ? one : many}`;

/** "2 comments and 1 tracked change", leaving out a kind there are none of. */
export function describeItems(comments: number, edits: number): string {
  const parts = [
    comments > 0 && plural(comments, 'comment', 'comments'),
    edits > 0 && plural(edits, 'tracked change', 'tracked changes'),
  ].filter(Boolean);
  return parts.length ? parts.join(' and ') : 'nothing';
}
