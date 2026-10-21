'use client';

import { SeverityEnum } from '@/lib/generated-api';
import { severityStyle, SeverityStyle } from '@/lib/severity-style';
import { createContext, useCallback, useContext } from 'react';

const GroupBySeverityContext = createContext(true);

/**
 * The project's `group_by_severity` setting, provided by the project shell (the
 * share view included). Outside a project, issues group by severity as before.
 */
export const GroupBySeverityProvider = GroupBySeverityContext.Provider;

export function useGroupBySeverity(): boolean {
  return useContext(GroupBySeverityContext);
}

/** The palette entry for a severity as this project shows it; see {@link severityStyle}. */
export function useSeverityStyle(): (severity: SeverityEnum) => SeverityStyle {
  const grouped = useGroupBySeverity();
  return useCallback((severity: SeverityEnum) => severityStyle(severity, grouped), [grouped]);
}
