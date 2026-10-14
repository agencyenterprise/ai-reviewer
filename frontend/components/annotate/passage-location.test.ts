import { describe, expect, it } from 'vitest';
import { blockCoversLine, passageUrlTransform } from './passage-location';

describe('passageUrlTransform', () => {
  it('keeps a figure the document carries inline', () => {
    const png = 'data:image/png;base64,iVBORw0KGgo=';
    expect(passageUrlTransform(png)).toBe(png);
  });

  it('still strips data URIs that are not images', () => {
    expect(passageUrlTransform('data:text/html;base64,PHA+aGk8L3A+')).toBe('');
  });

  it('leaves ordinary links as they are', () => {
    expect(passageUrlTransform('https://example.org/report')).toBe('https://example.org/report');
  });
});

describe('blockCoversLine', () => {
  it('finds the source line inside a block that spans several lines', () => {
    expect(blockCoversLine({ lineStart: '3', lineEnd: '5' }, 4)).toBe(true);
    expect(blockCoversLine({ lineStart: '3', lineEnd: '5' }, 5)).toBe(true);
    expect(blockCoversLine({ lineStart: '3', lineEnd: '5' }, 6)).toBe(false);
  });

  it('treats a block without an end as its first line only', () => {
    expect(blockCoversLine({ lineStart: '3' }, 3)).toBe(true);
    expect(blockCoversLine({ lineStart: '3' }, 4)).toBe(false);
  });
});
