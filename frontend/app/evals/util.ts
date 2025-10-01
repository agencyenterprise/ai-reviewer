import { flatMap, get, isArray, isPlainObject, keys } from 'lodash';
import { IncEx } from './types';

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
