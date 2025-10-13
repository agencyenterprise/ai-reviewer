import { ClaimSubstantiationResultWithClaimIndex, Severity } from './generated-api';

export const getSeverityLabel = (severity?: Severity) => {
  switch (severity) {
    case Severity.NUMBER_0:
      return 'No issue';
    case Severity.NUMBER_1:
      return 'Not enough data to know for sure';
    case Severity.NUMBER_2:
      return 'Low severity';
    case Severity.NUMBER_3:
      return 'Medium severity';
    case Severity.NUMBER_4:
      return 'High severity';
    default:
      return 'Unknown';
  }
};

export const getSeverityClasses = (severity?: Severity) => {
  switch (severity) {
    case Severity.NUMBER_4:
      return 'bg-red-100 text-red-800';
    case Severity.NUMBER_3:
      return 'bg-orange-100 text-orange-800';
    case Severity.NUMBER_2:
      return 'bg-yellow-100 text-yellow-800';
    case Severity.NUMBER_1:
      return 'bg-yellow-100 text-yellow-800';
    default:
      return 'bg-green-100 text-green-800';
  }
};

export const getMaxSeverity = (substantiations: ClaimSubstantiationResultWithClaimIndex[]): Severity => {
  return substantiations.reduce((max, s) => {
    if (!s.isSubstantiated && typeof s.severity === 'number') {
      return Math.max(max, s.severity) as Severity;
    }
    return max as Severity;
  }, Severity.NUMBER_0 as Severity);
};
