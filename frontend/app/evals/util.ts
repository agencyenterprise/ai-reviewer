import { flatMap, get, isArray, isPlainObject, keys } from 'lodash';
import { IncEx, TestCase } from './types';

/**
 * Format duration in seconds to display string (e.g., "1.23s")
 */
export function formatDuration(duration: number): string {
  return `${duration.toFixed(2)}s`;
}

// Helper function to format IncEx for display
export function formatIncEx(incEx: IncEx): string {
  if (Array.isArray(incEx)) {
    return incEx.join(', ');
  }

  if (typeof incEx === 'object' && incEx !== null) {
    return JSON.stringify(incEx, null, 2);
  }

  return String(incEx);
}

export function getFlattenedObjectValue(obj: Record<string, unknown>, key: string): unknown {
  return get(obj, key);
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
export function getFlattenedObjectKeys(obj: any, parentKey = ''): string[] {
  let result: string[] = [];

  if (isArray(obj)) {
    let idx = 0;
    result = flatMap(obj, function (obj) {
      return getFlattenedObjectKeys(obj, (parentKey || '') + '[' + idx++ + ']');
    });
  } else if (isPlainObject(obj)) {
    result = flatMap(keys(obj), function (key) {
      const currentKey = parentKey ? parentKey + '.' + key : key;
      const value = obj[key];

      // If the value is a primitive (not object/array), it's a leaf
      if (!isArray(value) && !isPlainObject(value)) {
        return [currentKey];
      }

      // Otherwise, recursively get keys from nested objects/arrays
      return getFlattenedObjectKeys(value, currentKey);
    });
  } else {
    // This is a primitive value, so if we have a parentKey, it's a leaf
    if (parentKey) {
      result = [parentKey];
    }
  }

  return result;
}

export interface FieldInsight {
  field: string;
  passed: number;
  total: number;
  accuracy: number;
  failedTests: string[];
}

/**
 * Aggregate field-level statistics across multiple test cases.
 * Returns insights about which fields are most problematic.
 */
export function aggregateFieldInsights(testCases: TestCase[]): FieldInsight[] {
  const fieldMap = new Map<string, { passed: number; total: number; failedTests: Set<string> }>();

  testCases.forEach((tc) => {
    // Skip test cases that don't have the expected structure
    if (!tc.agent_test_case?.evaluation_result) {
      return;
    }

    const comparisons = tc.agent_test_case.evaluation_result?.field_comparisons || [];
    comparisons.forEach((comp) => {
      if (!fieldMap.has(comp.field_path)) {
        fieldMap.set(comp.field_path, { passed: 0, total: 0, failedTests: new Set() });
      }
      const stats = fieldMap.get(comp.field_path)!;
      stats.passed += comp.passed_instances;
      stats.total += comp.total_instances;

      // Track which tests had failures for this field
      if (!comp.passed) {
        stats.failedTests.add(tc.agent_test_case.name);
      }
    });
  });

  return Array.from(fieldMap.entries())
    .map(([field, stats]) => ({
      field,
      passed: stats.passed,
      total: stats.total,
      accuracy: Math.round((stats.passed / stats.total) * 100),
      failedTests: Array.from(stats.failedTests),
    }))
    .sort((a, b) => a.accuracy - b.accuracy); // Sort by accuracy ascending (worst first)
}
