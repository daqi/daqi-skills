#!/usr/bin/env bun

import fs from 'node:fs';
import path from 'node:path';

type Args = {
  mdFile: string;
  out: string;
  bodyOnly: boolean;
};

function parseArgs(): Args {
  const argv = process.argv.slice(2);
  let mdFile = '';
  let out = 'xhs-img';
  let bodyOnly = false;

  for (let i = 0; i < argv.length; i++) {
    const arg = argv[i];
    if (arg === '--out') out = argv[++i] || out;
    else if (arg === '--body-only') bodyOnly = true;
    else if (!mdFile) mdFile = arg;
  }

  if (!mdFile) {
    console.error('Usage: md2text.ts <markdown-file> [options]');
    console.error('Options:');
    console.error('  --out <path>       输出文件路径或输出目录（默认: xhs-img）');
    console.error('  --body-only        仅抽取“正文内容”段（## 正文内容 → ## 标签）');
    process.exit(1);
  }

  return { mdFile, out, bodyOnly };
}

function extractBodySection(markdown: string): string {
  const startMatch = markdown.match(/^##\s+正文内容\s*$/m);
  if (!startMatch || startMatch.index == null) return markdown;

  const startIdx = startMatch.index + startMatch[0].length;
  const rest = markdown.slice(startIdx);

  const endMatch = rest.match(/^##\s+标签\s*$/m);
  const endIdx = endMatch && endMatch.index != null ? endMatch.index : rest.length;

  return rest.slice(0, endIdx).replace(/^\s+\n/, '').trim() + '\n';
}

function stripMarkdown(markdown: string): string {
  let text = markdown.replace(/\r\n/g, '\n');

  // Remove horizontal rules
  text = text.replace(/^\s*([-*_])\1\1+\s*$/gm, '');

  // Fenced code blocks: keep content, drop fences
  text = text.replace(/```[\s\S]*?```/g, (block) => {
    const lines = block.split('\n');
    // drop first/last fence lines
    const inner = lines.slice(1, Math.max(1, lines.length - 1)).join('\n');
    return inner.trim() ? `\n${inner}\n` : '\n';
  });

  // Blockquotes
  text = text.replace(/^>\s?/gm, '');

  // Headings (# + space) — won’t touch hashtags like #程序员
  text = text.replace(/^#{1,6}\s+/gm, '');

  // Lists
  text = text.replace(/^\s*[*+-]\s+/gm, '- ');
  text = text.replace(/^\s*\d+\.\s+/gm, '- ');

  // Images: ![alt](url) -> alt or url
  text = text.replace(/!\[([^\]]*)\]\(([^)]+)\)/g, (_m, alt, url) => {
    const a = String(alt || '').trim();
    const u = String(url || '').trim();
    return a || u;
  });

  // Links: [text](url) -> text（url）
  text = text.replace(/\[([^\]]+)\]\(([^)]+)\)/g, (_m, label, url) => {
    const l = String(label || '').trim();
    const u = String(url || '').trim();
    if (!l) return u;
    if (!u) return l;
    return `${l}（${u}）`;
  });

  // Inline code
  text = text.replace(/`([^`]+)`/g, '$1');

  // Bold/italic/strikethrough markers
  text = text.replace(/\*\*(.+?)\*\*/g, '$1');
  text = text.replace(/__(.+?)__/g, '$1');
  text = text.replace(/~~(.+?)~~/g, '$1');
  text = text.replace(/(^|\s)\*(\S[^*]*?)\*(?=\s|$)/g, '$1$2');
  text = text.replace(/(^|\s)_(\S[^_]*?)_(?=\s|$)/g, '$1$2');

  // Clean up common Markdown escapes
  text = text.replace(/\\([\\`*_{}\[\]()#+\-.!>])/g, '$1');

  // Trim trailing spaces on each line
  text = text.replace(/[ \t]+$/gm, '');

  // Collapse excessive blank lines
  text = text.replace(/\n{3,}/g, '\n\n');

  return text.trim() + '\n';
}

function resolveOutPath(outArg: string, mdFile: string): string {
  const outIsFile = /\.txt$/i.test(outArg);
  if (outIsFile) return outArg;

  const dir = outArg || 'xhs-img';
  const base = path.basename(mdFile, path.extname(mdFile));
  return path.join(dir, `${base}.txt`);
}

async function main() {
  const { mdFile, out, bodyOnly } = parseArgs();

  if (!fs.existsSync(mdFile)) {
    console.error(`文件不存在: ${mdFile}`);
    process.exit(1);
  }

  const raw = fs.readFileSync(mdFile, 'utf-8');
  const section = bodyOnly ? extractBodySection(raw) : raw;
  const plain = stripMarkdown(section);

  const outPath = resolveOutPath(out, mdFile);
  const outDir = path.dirname(outPath);
  fs.mkdirSync(outDir, { recursive: true });
  fs.writeFileSync(outPath, plain, 'utf-8');

  console.log(`✅ 已生成纯文本: ${path.resolve(outPath)}`);
}

main().catch((err) => {
  console.error('错误:', err);
  process.exit(1);
});
