/** Number, duration and date formatting shared by the dashboard cards. */

const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

/** 1,284 · 12.9K · 4.2M — keeps large values readable inside a stat tile. */
export function formatCompact(value: number): string {
  if (Math.abs(value) < 10_000) return value.toLocaleString('en-US');
  if (Math.abs(value) < 1_000_000) return `${(value / 1_000).toFixed(1).replace(/\.0$/, '')}K`;
  return `${(value / 1_000_000).toFixed(1).replace(/\.0$/, '')}M`;
}

/** 0.9s · 23s · 4m 12s · 1h 5m */
export function formatDuration(seconds: number | null | undefined): string {
  if (seconds === null || seconds === undefined) return '—';
  if (seconds < 10) return `${seconds.toFixed(1)}s`;
  if (seconds < 60) return `${Math.round(seconds)}s`;
  if (seconds < 3600) {
    const minutes = Math.floor(seconds / 60);
    return `${minutes}m ${Math.round(seconds - minutes * 60)}s`;
  }
  const hours = Math.floor(seconds / 3600);
  return `${hours}h ${Math.round((seconds - hours * 3600) / 60)}m`;
}

/**
 * Rounded, but never to a figure that contradicts the count beside it: a
 * handful of failures out of thousands is "<1%", not "0%", and 1,333 of 1,337
 * completing is ">99%", not "100%".
 */
export function formatPercent(ratio: number): string {
  const percent = ratio * 100;
  if (percent > 0 && percent < 0.5) return '<1%';
  if (percent < 100 && percent >= 99.5) return '>99%';
  return `${Math.round(percent)}%`;
}

/**
 * The generated types declare date fields as `Date`, but the SDK never wires up
 * hey-api's response transformers, so at runtime they arrive as ISO strings.
 * Every date the dashboard renders goes through here.
 */
export function toDate(value: Date | string): Date {
  return value instanceof Date ? value : new Date(value);
}

/**
 * Bucket labels are read from the UTC parts on purpose: the API sends a
 * calendar date, parsed as UTC midnight. Local getters would shift every label
 * a day west of Greenwich.
 */
export function formatBucketLabel(bucket: Date | string): string {
  const date = toDate(bucket);
  return `${MONTHS[date.getUTCMonth()]} ${date.getUTCDate()}`;
}

/**
 * Axis ends. Weekly buckets carry the year: a twelve-month window opens and
 * closes in the same month, and "Aug 25 → Aug 31" hides which year is which.
 */
export function formatAxisLabel(bucket: Date | string, granularity: 'day' | 'week'): string {
  const date = toDate(bucket);
  if (granularity === 'week') return `${MONTHS[date.getUTCMonth()]} ${date.getUTCFullYear()}`;
  return formatBucketLabel(date);
}

export function formatBucketFull(bucket: Date | string, granularity: 'day' | 'week'): string {
  const date = toDate(bucket);
  const label = `${MONTHS[date.getUTCMonth()]} ${date.getUTCDate()}, ${date.getUTCFullYear()}`;
  return granularity === 'week' ? `Week of ${label}` : label;
}

export interface Delta {
  /** e.g. "+18%" — absolute when there is no previous value to compare against. */
  label: string;
  direction: 'up' | 'down' | 'flat';
}

/** Change against the equal-length window that preceded the selected one. */
export function computeDelta(current: number, previous: number): Delta {
  const change = current - previous;
  if (change === 0) return { label: 'no change', direction: 'flat' };
  const sign = change > 0 ? '+' : '−';
  const magnitude = Math.abs(change);
  const label =
    previous === 0 ? `${sign}${formatCompact(magnitude)}` : `${sign}${Math.round((magnitude / previous) * 100)}%`;
  return { label, direction: change > 0 ? 'up' : 'down' };
}
