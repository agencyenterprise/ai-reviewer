import { describe, expect, it } from 'vitest';
import { addinId, addinManifest, manifestVersion } from './manifest';

const SETTINGS = {
  frontendUrl: 'https://dd.example.com/some/path',
  clientId: '11111111-2222-3333-4444-555555555555',
  version: '2.0.13',
};

function parsed(xml: string): Document {
  const document = new DOMParser().parseFromString(xml, 'application/xml');
  expect(document.getElementsByTagName('parsererror')).toHaveLength(0);
  return document;
}

function text(document: Document, tag: string): string[] {
  return [...document.getElementsByTagName(tag)].map((node) => node.textContent ?? '');
}

describe('addinManifest', () => {
  it('points the pane, the icons and single sign-on at this deployment', () => {
    const document = parsed(addinManifest(SETTINGS));

    expect(text(document, 'AppDomain')).toEqual(['https://dd.example.com']);
    expect(document.getElementsByTagName('SourceLocation')[0].getAttribute('DefaultValue')).toBe(
      'https://dd.example.com/addin',
    );
    expect(text(document, 'Resource')).toEqual(['api://dd.example.com/11111111-2222-3333-4444-555555555555']);
    expect(text(document, 'Version')).toEqual(['2.0.13.0']);
  });

  it('defines every resource it refers to', () => {
    const document = parsed(addinManifest(SETTINGS));
    const defined = new Set([...document.querySelectorAll('Resources [id]')].map((node) => node.getAttribute('id')));
    const referred = [...document.querySelectorAll('[resid]')].map((node) => node.getAttribute('resid'));

    expect(referred.filter((id) => !defined.has(id))).toEqual([]);
  });
});

describe('addinId', () => {
  it('is the same for a host every time, and differs between hosts', () => {
    const dev = addinId('dd-dev.example.com');

    expect(addinId('DD-dev.example.com')).toBe(dev);
    expect(addinId('dd.example.com')).not.toBe(dev);
    expect(dev).toMatch(/^[0-9a-f]{8}-[0-9a-f]{4}-5[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/);
  });
});

describe('manifestVersion', () => {
  it('pads the app version to the four numbers Office requires', () => {
    expect(manifestVersion('2.0.13')).toBe('2.0.13.0');
    expect(manifestVersion('3')).toBe('3.0.0.0');
  });
});
