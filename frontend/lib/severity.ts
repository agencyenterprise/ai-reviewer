import { ClaimSubstantiationResultWithClaimIndex, Severity } from './generated-api';

export const getSeverityLabel = (severity?: Severity) => {
  switch (severity) {
    case Severity.NUMBER_1:
      return 'not enough data to know for sure';
    case Severity.NUMBER_2:
      return 'may be ok';
    case Severity.NUMBER_3:
      return 'should be fixed';
    case Severity.NUMBER_4:
      return 'must be fixed';
    default:
      return 'no issue';
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
      return 'bg-gray-100 text-gray-800';
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
