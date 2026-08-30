/**
 * How a rail marks the item you are on.
 *
 * One definition because every rail in the view needs it — filters, lenses,
 * steps, assessments, help topics — and because the first attempt was too
 * quiet: selected was `bg-accent` against a `bg-accent/60` hover, two shades of
 * the same token, so the selection read as a hover that had got stuck.
 *
 * The foreground at low alpha rather than the accent token: `--accent` is
 * oklch(0.97) in light mode, near enough to white that a row wearing it barely
 * separates from one that is not. Layering the foreground instead darkens the
 * row on a light theme and lightens it on a dark one, so selection gains
 * contrast either way. Hover keeps the accent, well below it.
 */
export const RAIL_ITEM_ACTIVE = 'bg-foreground/8 text-foreground';

export const RAIL_ITEM_IDLE = 'hover:bg-accent/40';
