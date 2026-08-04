#!/usr/bin/env bun
import { execSync } from 'child_process';
import fs from 'fs';
import path from 'path';

export interface CommitInfo {
  hash: string;
  author: string;
  message: string;
  type: string;
  scope?: string;
  subject: string;
}

export function parseCommitLine(line: string): CommitInfo | null {
  const parts = line.trim().split('|');
  if (parts.length < 3) return null;
  
  const hash = parts[0];
  const author = parts[1];
  const message = parts.slice(2).join('|');

  const conventionalRegex = /^(feat|fix|refactor|docs|style|test|chore|perf)(?:\(([^)]+)\))?:\s*(.*)$/i;
  const match = message.match(conventionalRegex);

  if (match) {
    return {
      hash,
      author,
      message,
      type: match[1].toLowerCase(),
      scope: match[2],
      subject: match[3]
    };
  }

  return {
    hash,
    author,
    message,
    type: 'other',
    subject: message
  };
}

export function generateChangelog(range?: string): string {
  let gitCmd = 'git log --oneline --format="%h|%an|%s"';
  try {
    const lastTag = execSync('git describe --tags --abbrev=0 2>/dev/null', { encoding: 'utf-8' }).trim();
    if (lastTag && !range) {
      gitCmd = `git log ${lastTag}..HEAD --format="%h|%an|%s"`;
    }
  } catch {
    // No tags found or git error, fallback to last 50 commits
    gitCmd = 'git log -n 50 --format="%h|%an|%s"';
  }

  let logOutput = '';
  try {
    logOutput = execSync(gitCmd, { encoding: 'utf-8' });
  } catch (err) {
    console.error('Error fetching git log:', err);
    return '## Changelog\n\nNo commits found.';
  }

  const lines = logOutput.trim().split('\n').filter(Boolean);
  const commits: CommitInfo[] = lines.map(parseCommitLine).filter((c): c is CommitInfo => c !== null);

  const categories: Record<string, CommitInfo[]> = {
    feat: [],
    fix: [],
    refactor: [],
    docs: [],
    chore: [],
    other: []
  };

  const authors = new Set<string>();

  for (const commit of commits) {
    if (commit.author) authors.add(commit.author);
    if (categories[commit.type]) {
      categories[commit.type].push(commit);
    } else {
      categories.other.push(commit);
    }
  }

  let markdown = '## 📋 Auto-Generated Changelog\n\n';

  if (categories.feat.length > 0) {
    markdown += '### 🚀 Features\n';
    for (const c of categories.feat) {
      const scopeStr = c.scope ? `**${c.scope}**: ` : '';
      markdown += `- ${scopeStr}${c.subject} (\`${c.hash}\` by ${c.author})\n`;
    }
    markdown += '\n';
  }

  if (categories.fix.length > 0) {
    markdown += '### 🐛 Bug Fixes\n';
    for (const c of categories.fix) {
      const scopeStr = c.scope ? `**${c.scope}**: ` : '';
      markdown += `- ${scopeStr}${c.subject} (\`${c.hash}\` by ${c.author})\n`;
    }
    markdown += '\n';
  }

  if (categories.refactor.length > 0) {
    markdown += '### 🛠️ Refactoring\n';
    for (const c of categories.refactor) {
      const scopeStr = c.scope ? `**${c.scope}**: ` : '';
      markdown += `- ${scopeStr}${c.subject} (\`${c.hash}\` by ${c.author})\n`;
    }
    markdown += '\n';
  }

  if (categories.docs.length > 0) {
    markdown += '### 📚 Documentation\n';
    for (const c of categories.docs) {
      markdown += `- ${c.subject} (\`${c.hash}\` by ${c.author})\n`;
    }
    markdown += '\n';
  }

  if (categories.chore.length > 0 || categories.other.length > 0) {
    markdown += '### 🔧 Maintenance & Other Changes\n';
    for (const c of [...categories.chore, ...categories.other]) {
      markdown += `- ${c.subject} (\`${c.hash}\` by ${c.author})\n`;
    }
    markdown += '\n';
  }

  if (authors.size > 0) {
    markdown += '### ❤️ Contributors\n';
    markdown += `Thank you to all contributors who worked on this release: ${Array.from(authors).join(', ')}\n`;
  }

  return markdown;
}

if (import.meta.main || process.argv[1]?.endsWith('generate-changelog.ts')) {
  const changelog = generateChangelog();
  console.log(changelog);
}
