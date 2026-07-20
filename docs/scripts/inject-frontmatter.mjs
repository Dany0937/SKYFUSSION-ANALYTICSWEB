import { readFileSync, writeFileSync, readdirSync, statSync } from 'fs';
import { join, relative, sep } from 'path';
import { fileURLToPath } from 'url';

const DOCS_DIR = join(fileURLToPath(new URL('..', import.meta.url)), 'src', 'content', 'docs');

function collectMarkdownFiles(dir) {
  const entries = readdirSync(dir, { withFileTypes: true });
  const files = [];
  for (const entry of entries) {
    const full = join(dir, entry.name);
    if (entry.isDirectory()) {
      if (entry.name.startsWith('.')) continue;
      files.push(...collectMarkdownFiles(full));
    } else if (entry.name.endsWith('.md') || entry.name.endsWith('.mdx')) {
      files.push(full);
    }
  }
  return files.sort();
}

function extractTitle(content) {
  const match = content.match(/^#\s+(.+)/m);
  return match ? match[1].trim() : '';
}

function extractDescription(content) {
  const lines = content.split('\n');
  let found = false;
  const after = [];
  for (const line of lines) {
    if (line.startsWith('# ')) { found = true; continue; }
    if (found) {
      if (line.trim() === '') continue;
      if (line.startsWith('#')) break;
      const clean = line.replace(/^[>\s]*/, '').trim();
      if (clean) return clean.slice(0, 200);
    }
  }
  return '';
}

function parseFrontmatter(content) {
  const match = content.match(/^---\s*\n([\s\S]*?)\n---\s*\n/);
  if (!match) return null;
  const raw = match[1];
  const fields = {};
  for (const line of raw.split('\n')) {
    const kv = line.match(/^\s*(\w+)\s*:\s*(.*)/);
    if (kv) fields[kv[1]] = kv[2].trim();
  }
  return { raw, fields, match: match[0] };
}

function computeOrder(filePath, sectionFiles) {
  const idx = sectionFiles.indexOf(filePath);
  return idx >= 0 ? idx + 1 : 1;
}

function getSectionKey(filePath) {
  const rel = relative(DOCS_DIR, filePath);
  const parts = rel.split(sep);
  return parts.length > 1 ? parts[0] : '';
}

function buildFrontmatter(title, description, order) {
  let fm = '---\n';
  fm += `title: ${title}\n`;
  fm += `description: ${description}\n`;
  if (order) fm += `order: ${order}\n`;
  fm += '---\n\n';
  return fm;
}

function injectOrFix(content, title, description, order) {
  const parsed = parseFrontmatter(content);
  const body = parsed ? content.slice(parsed.match.length) : content.trimStart();
  const existingFields = parsed ? { ...parsed.fields } : {};

  const finalTitle = existingFields.title || title;
  const finalDescription = (existingFields.description || existingFields.decription || description);
  const finalOrder = order;

  return buildFrontmatter(finalTitle, finalDescription, finalOrder) + body;
}

function main() {
  const files = collectMarkdownFiles(DOCS_DIR);

  const sections = {};
  for (const f of files) {
    const key = getSectionKey(f);
    if (!sections[key]) sections[key] = [];
    sections[key].push(f);
  }

  let changed = 0;
  for (const f of files) {
    const content = readFileSync(f, 'utf8');
    const key = getSectionKey(f);
    const sectionFiles = sections[key] || [];
    const order = computeOrder(f, sectionFiles);

    const rel = relative(DOCS_DIR, f);
    let title = extractTitle(content);
    if (!title) title = rel.replace(/\.(md|mdx)$/, '').split(sep).pop().replace(/^\d+-/, '').replace(/[-_]/g, ' ');

    let description = extractDescription(content);
    if (!description) description = `${title} — Documentación de Skyfussion Analytics`;

    const newContent = injectOrFix(content, title, description, order);

    if (newContent !== content) {
      writeFileSync(f, newContent, 'utf8');
      console.log(`[inject] ${rel} → title="${title}"`);
      changed++;
    } else {
      console.log(`[ok]     ${rel}`);
    }
  }

  console.log(`\nDone. ${changed} file(s) updated.`);
}

main();
