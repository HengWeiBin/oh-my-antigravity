#!/usr/bin/env node
import fs from 'fs';
import path from 'path';

function printUsage() {
  console.log('Usage: node scaffold-plan.mjs <slug> [--clear|--unclear] [--reset] [--force]');
}

const args = process.argv.slice(2);
if (args.length === 0 || args.includes('--help') || args.includes('-h')) {
  printUsage();
  process.exit(1);
}

let slug = null;
let intent = 'unspecified';
let isReset = false;
let isForce = false;

for (const arg of args) {
  if (arg === '--clear') {
    intent = 'clear';
  } else if (arg === '--unclear') {
    intent = 'unclear';
  } else if (arg === '--reset') {
    isReset = true;
  } else if (arg === '--force') {
    isForce = true;
  } else if (!arg.startsWith('-')) {
    if (!slug) {
      slug = arg;
    }
  }
}

if (!slug) {
  console.error('Error: <slug> argument is required.');
  printUsage();
  process.exit(1);
}

// Sanitize slug
slug = slug.toLowerCase().replace(/[^a-z0-9_-]/g, '-').replace(/-+/g, '-').replace(/^-|-$/g, '');

const cwd = process.cwd();
const draftsDir = path.join(cwd, '.omo', 'drafts');
const plansDir = path.join(cwd, '.omo', 'plans');

fs.mkdirSync(draftsDir, { recursive: true });
fs.mkdirSync(plansDir, { recursive: true });

const draftPath = path.join(draftsDir, `${slug}.md`);
const planPath = path.join(plansDir, `${slug}.md`);

if (fs.existsSync(planPath) && !isReset) {
  console.log(`Plan already exists at ${planPath}. No-op (use --reset to re-scaffold).`);
  process.exit(0);
}

if (fs.existsSync(planPath) && isReset && !isForce) {
  // Check if existing plan was modified by human
  const content = fs.readFileSync(planPath, 'utf-8');
  if (!content.includes('<!-- APPEND TODOS BELOW THIS LINE -->')) {
    console.error(`Refusing to reset plan at ${planPath}: file appears to be hand-built. Use --force to override.`);
    process.exit(1);
  }
}

const now = new Date().toISOString();

const draftTemplate = `---
slug: ${slug}
intent: ${intent}
review_required: false
status: drafting
created_at: ${now}
updated_at: ${now}
---

# Draft: ${slug}

## Context & Research

## Decided Options & Tradeoffs

## Approval Gate
- Status: drafting
`;

const planTemplate = `# Plan: ${slug}

## TL;DR (For humans)
- **Goal**: <Goal summary>
- **Approach**: <Approach summary>
- **Key Decisions**: <Key decisions summary>

## User Review Required

> [!IMPORTANT]
> Critical operational choices or tradeoffs.

---

## Proposed Changes

### Architecture & Scope

### File Modifications

---

## Verification Plan

### Automated Tests

### Manual Verification

---

## Todos

<!-- APPEND TODOS BELOW THIS LINE -->
`;

fs.writeFileSync(draftPath, draftTemplate, 'utf-8');
fs.writeFileSync(planPath, planTemplate, 'utf-8');

console.log(`Successfully scaffolded plan files:`);
console.log(` - Draft: ${draftPath}`);
console.log(` - Plan:  ${planPath}`);
