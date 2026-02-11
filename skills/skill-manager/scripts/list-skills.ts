#!/usr/bin/env node

import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

function parseArgs() {
  const args = process.argv.slice(2);
  let skillsDir = '';

  for (let i = 0; i < args.length; i++) {
    const arg = args[i];
    if (arg === '--skills-dir') {
      skillsDir = args[i + 1] || '';
      i++;
    }
  }

  if (!skillsDir) {
    skillsDir = path.resolve(__dirname, '..', '..');
  }

  return { skillsDir };
}

function readDescription(filePath: string) {
  try {
    const content = fs.readFileSync(filePath, 'utf8');
    const match = content.match(/^description:\s*(.*)$/m);
    if (!match || !match[1]) return '';
    return match[1].replace(/^"|"$/g, '').trim();
  } catch {
    return '';
  }
}

function main() {
  const { skillsDir } = parseArgs();
  const entries = fs.existsSync(skillsDir) ? fs.readdirSync(skillsDir, { withFileTypes: true }) : [];

  console.log('| skill名称 | 简短描述 |');
  console.log('| :--- | :--- |');

  for (const entry of entries) {
    if (!entry.isDirectory()) continue;
    const skillName = entry.name;
    const skillFile = path.join(skillsDir, skillName, 'SKILL.md');
    if (!fs.existsSync(skillFile)) continue;

    const desc = readDescription(skillFile);
    if (!desc) {
      console.log(`| [${skillName}] | ❌ 缺失描述 |`);
    } else {
      console.log(`| [${skillName}] | ${desc} |`);
    }
  }
}

main();
