/** Shared frontend utilities */

const AEM_SKILL_KEYWORDS = [
  'aem', 'eds', 'adobe experience', 'sling', 'osgi', 'htl', 'sightly',
  'cq5', 'dispatcher', 'edge delivery', 'franklin',
];

export function isAEMSkill(skill: string): boolean {
  const lower = skill.toLowerCase();
  return AEM_SKILL_KEYWORDS.some((kw) => lower.includes(kw));
}

const FAKE_URL_HOSTS = [
  'example.com', 'example.org', 'example.net',
  'placeholder.com', 'test.com', 'sample.com',
  'fake.com', 'dummy.com', 'yourdomain.com',
  'yourcompany.com', 'localhost',
];

/** Validate job apply URLs — rejects placeholders and private hosts */
export function isGenuineUrl(url: string | null | undefined): boolean {
  if (!url) return false;
  try {
    const parsed = new URL(url);
    const host = parsed.hostname.toLowerCase();
    if (!['http:', 'https:'].includes(parsed.protocol)) return false;
    for (const fake of FAKE_URL_HOSTS) {
      if (host === fake || host.endsWith('.' + fake)) return false;
    }
    if (/^127\.|^10\.|^192\.168\./.test(host)) return false;
    if (/^\d+\.\d+\.\d+\.\d+$/.test(host)) return false;
    const parts = host.split('.');
    if (parts.length < 2) return false;
    const tld = parts[parts.length - 1];
    return tld.length >= 2 && /^[a-z]+$/.test(tld);
  } catch {
    return false;
  }
}

export function formatNoticePeriod(value: string): string {
  return value.replace(/_/g, ' ');
}

export function dedupeSearchChips<T extends { query: string }>(chips: T[]): T[] {
  const seen = new Set<string>();
  return chips.filter((c) => {
    const key = c.query?.toLowerCase();
    if (!key || seen.has(key)) return false;
    seen.add(key);
    return true;
  });
}
