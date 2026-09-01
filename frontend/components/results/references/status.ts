import { ReferenceReviewStatus } from '@/components/results/references/types';

/**
 * The one place the two states are named. "Provided" rather than "available",
 * because whether we hold the file is the result of someone supplying it — by
 * uploading, or by letting us fetch it.
 */
export const STATUS: Record<ReferenceReviewStatus, { label: string; short: string; text: string }> = {
  matched: {
    label: 'Source file provided',
    short: 'Provided',
    text: 'text-green-700 dark:text-green-400',
  },
  unmatched: {
    // Amber, the app's colour for "waiting on you": these are the rows the
    // reader is here to act on, and they have to be findable down a list of
    // fifty that otherwise all look alike.
    label: 'Source file not provided',
    short: 'Not provided',
    text: 'text-amber-700 dark:text-amber-400',
  },
  fetching: {
    label: 'Looking for a source file',
    short: 'Fetching',
    text: 'text-blue-700 dark:text-blue-400',
  },
};
