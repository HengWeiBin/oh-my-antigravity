---
name: git-master
description: "MUST USE for ANY git operations. Concise, high-precision git expert covering 4 core modes: Commit (atomic, style-detected), Rebase (interactive, squash, sync), History (log -S, blame, bisect), and Status (working tree and branch inspection). Triggers: 'commit', 'rebase', 'squash', 'who wrote', 'when was X added', 'find the commit that', 'git status'."
---

# Git Master

Concise, high-precision Git specialist for autonomous agents. Focuses strictly on four core operational modes: **Commit**, **Rebase**, **History**, and **Status**.

## Shell & Environment Invariants (PowerShell / Windows)
- Always quote git references containing `@` symbols (e.g. `'@{u}'`, `'@{upstream}'`, `'HEAD@{1}'`) to prevent PowerShell hash table parsing syntax errors.
- Use `;` instead of `&&` as a command separator in PowerShell environments.
- Always check repository status before mutating operations.

---

## Mode Detection (First Action)

Inspect the user or caller prompt and select the active mode:

| Mode | Triggers | Core Objective |
|---|---|---|
| **`COMMIT`** | "commit", "save changes", "checkpoint" | Atomic, style-detected, verified commits. |
| **`REBASE`** | "rebase", "squash", "sync with main" | History rewriting, autosquash, conflict resolution. |
| **`HISTORY`** | "who wrote", "when was X added", "blame", "bisect", "find commit" | Code archaeology via pickaxe, blame, and bisect. |
| **`STATUS`** | "status", "what changed", "diff", "branch status" | Inspection of dirty working tree, staged diffs, and divergence. |

---

## 1. COMMIT Mode (Atomic & Verified)

### Core Rule: Multiple Atomic Commits by Default
Single bulk commits across multiple concerns are forbidden. Split changes logically:
- **By Concern**: Separate refactoring, feature logic, documentation, and tests into distinct commits.
- **By Directory / Module**: Separate changes in frontend vs backend or distinct plugins/modules.
- **Revertibility**: Every commit must be independently revertible without breaking unrelated subsystems.

### Pre-Commit Gate
1. **Status & Diff Review**: Inspect `git status -s` and `git diff --stat`.
2. **Build / Test Verification**: Run project test commands (e.g. `uv run pytest`, `cargo test`, `npm test`) before creating any commit. NEVER commit broken code.
3. **Repository Style Detection**:
   Inspect the last 20 commit messages via `git log -20 --oneline` and match the repository convention:
   - **Semantic / Conventional**: `feat(scope): ...`, `fix(scope): ...`, `refactor: ...`, `docs: ...`
   - **Plain / Imperative**: `Add login verification`, `Update hook dependencies`
   - **Short**: `format`, `update readme`

### Commit Execution Pattern
Stage files selectively per atomic unit, never use blind `git add .`:
```powershell
# 1. Stage specific files for unit 1
git add path/to/module.py tests/test_module.py
git commit -m "feat(module): implement scoped capability"

# 2. Stage specific files for unit 2
git add docs/module.md
git commit -m "docs(module): document capability usage"
```

---

## 2. REBASE Mode (Squash & History Sync)

### Upstream Synchronization
Rebase current feature branch onto latest upstream trunk:
```powershell
# Fetch latest upstream trunk
git fetch origin main

# Rebase onto origin/main
git rebase origin/main
```

### Squashing & History Rewriting
When squashing fixup commits before PR or merging:
```powershell
# Autosquash or interactive rebase for the last N commits
git rebase -i HEAD~N
# Or auto-squash fixup commits
git rebase -i --autosquash origin/main
```

### Conflict Resolution Protocol
1. On conflict pause, run `git status` to locate unmerged paths.
2. Read conflicting files, understand both sides of the diff, and surgically resolve markers (`<<<<<<<`, `=======`, `>>>>>>>`).
3. Stage resolved files: `git add <resolved_file>`.
4. Continue rebase: `git rebase --continue`.
5. NEVER run `git commit` during an active rebase.
6. If rebase state becomes unrecoverable: `git rebase --abort`.

---

## 3. HISTORY Mode (Code Archaeology)

### Pickaxe Search (`git log -S` / `-G`)
Find the exact commit that added or removed a specific identifier, variable, or error string:
```powershell
# Search for exact string addition/removal across entire commit history
git log -S "symbol_name" --oneline

# Search with regex pattern
git log -G "def\s+process_payload" --oneline --patch
```

### Line & File History (`git blame` / `git log -L`)
Trace who modified specific lines and why:
```powershell
# Blame specific line range with commit hashes and timestamps
git blame -L 120,145 path/to/file.py

# Trace the full evolution of a specific function or line range
git log -L 120,145:path/to/file.py
```

### Regression Hunting (`git bisect`)
Automate finding the regression commit between a known good commit and bad HEAD:
```powershell
git bisect start
git bisect bad HEAD
git bisect good <known_good_commit_or_tag>

# Run automated test script on each step
git bisect run pytest path/to/test.py

# When finished
git bisect reset
```

---

## 4. STATUS Mode (Inspection & Divergence)

### Working Tree & Staged Analysis
Check branch name, upstream status, and dirty files concisely:
```powershell
# Compact status with branch & tracking info
git status -sb

# Review summary of staged changes
git diff --cached --stat

# Review summary of unstaged changes
git diff --stat
```

### Branch Divergence & Tracking
Inspect commits ahead / behind upstream:
```powershell
# Count ahead / behind relative to tracked upstream
git rev-list --left-right --count 'HEAD...@{u}'

# List commits on local branch not yet pushed to upstream
git log '@{u}..HEAD' --oneline
```

---

## Anti-Patterns & Hard Limits

- ❌ NEVER use `git commit -a` or `git add .` blindly without checking what files are dirty.
- ❌ NEVER commit credentials, `.env` files, temporary artifacts, or cache files (`__pycache__`, `.venv`).
- ❌ NEVER force-push (`git push -f`) to shared public branches (`main`, `master`, `develop`).
- ❌ NEVER execute a commit if the build or test suite is failing.
- ❌ NEVER use unquoted `@` references in PowerShell (`'@{u}'` required).
