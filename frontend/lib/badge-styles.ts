export function toTitleCase(s: string): string {
  return s?.replace(/_/g, ' ').replace(/\b\w/g, (m) => m.toUpperCase()) || '';
}

export function getConfidenceBadgeClasses(confidence: string): string {
  const normalized = (confidence || '').toLowerCase();
  if (normalized === 'high') return 'bg-green-100 text-green-800';
  if (normalized === 'medium') return 'bg-yellow-100 text-yellow-800';
  return 'bg-gray-100 text-gray-800';
}

export function getQualityBadgeClasses(quality: string): string {
  const normalized = (quality || '').toLowerCase();
  if (normalized === 'high_impact_publication') return 'bg-emerald-100 text-emerald-800';
  if (normalized === 'medium_impact_publication') return 'bg-teal-100 text-teal-800';
  if (normalized === 'low_impact_publication') return 'bg-slate-100 text-slate-700';
  return 'bg-neutral-100 text-neutral-800';
}

export function getReferenceTypeBadgeClasses(type: string): string {
  switch (type) {
    case 'article':
      return 'bg-blue-100 text-blue-800';
    case 'book':
      return 'bg-green-100 text-green-800';
    case 'webpage':
      return 'bg-purple-100 text-purple-800';
    default:
      return 'bg-gray-100 text-gray-800';
  }
}

export function getRecommendedActionBadgeClasses(action: string): string {
  switch (action) {
    case 'add_new_citation':
    case 'cite_existing_reference_in_new_place':
      return 'bg-green-100 text-green-800';
    case 'replace_existing_reference':
      return 'bg-yellow-100 text-yellow-800';
    case 'discuss_reference':
      return 'bg-blue-100 text-blue-800';
    case 'no_action':
      return 'bg-gray-100 text-gray-800';
    default:
      return 'bg-orange-100 text-orange-800';
  }
}
