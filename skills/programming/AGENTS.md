# programming

## OVERVIEW
Rigid language-specific checkers (check-no-excuse-rules.py, etc.) and coding guidelines across >40 reference files.

## STRUCTURE
- `references/`: Per-language guideline files and stacks
  - `go/`: Go-specific development patterns and library defaults
  - `python/`: Python-specific guidelines, FastAPI/AnyIO recipes
  - `rust/`: Rust strict cargo rules, Tokio, zero-cost safety
  - `rust-ub/`: Rust undefined behavior, Miri and sanitizers guide
  - `typescript/`: TypeScript tsconfig and Hono backend stack
- `scripts/`: AST linting and rigid validation tools
  - `go/`, `python/`, `rust/`, `typescript/`: Language-specific rule verification scripts

## WHERE TO LOOK
| Path | Purpose |
|------|---------|
| [SKILL.md](file:///c:/Users/K20879/.gemini/config/plugins/oh-my-antigravity/skills/programming/SKILL.md) | Core programming conventions, TDD discipline, and verification hooks |
| [references/code-smells.md](file:///c:/Users/K20879/.gemini/config/plugins/oh-my-antigravity/skills/programming/references/code-smells.md) | Common code smell definitions (file lengths, argument counts, etc.) |
| [references/logging.md](file:///c:/Users/K20879/.gemini/config/plugins/oh-my-antigravity/skills/programming/references/logging.md) | Logging guidelines and consumer-based levels |
| [references/python/README.md](file:///c:/Users/K20879/.gemini/config/plugins/oh-my-antigravity/skills/programming/references/python/README.md) | Python strict typing, toolchains, and FastAPI stack rules |
| [references/rust/README.md](file:///c:/Users/K20879/.gemini/config/plugins/oh-my-antigravity/skills/programming/references/rust/README.md) | Rust development practices, cargo configuration, and safety guidelines |
| [references/typescript/README.md](file:///c:/Users/K20879/.gemini/config/plugins/oh-my-antigravity/skills/programming/references/typescript/README.md) | TypeScript biome, tsconfig, and data modeling conventions |
| [references/go/README.md](file:///c:/Users/K20879/.gemini/config/plugins/oh-my-antigravity/skills/programming/references/go/README.md) | Go context, golangci-lint, and testing configurations |
| [scripts/python/check-no-excuse-rules.py](file:///c:/Users/K20879/.gemini/config/plugins/oh-my-antigravity/skills/programming/scripts/python/check-no-excuse-rules.py) | Python AST checker verifying 250 LOC limit and strict typing rules |
| [scripts/typescript/check-no-excuse-rules.ts](file:///c:/Users/K20879/.gemini/config/plugins/oh-my-antigravity/skills/programming/scripts/typescript/check-no-excuse-rules.ts) | TypeScript AST checker enforcing Biome/tsc conventions and file size |
| [scripts/rust/check-no-excuse-rules.py](file:///c:/Users/K20879/.gemini/config/plugins/oh-my-antigravity/skills/programming/scripts/rust/check-no-excuse-rules.py) | Python AST-based checker adapted for Rust structural rules |

## CONVENTIONS
- **Strict Size Caps**: Files are capped at 250 pure LOC (enforced by `check-no-excuse-rules`) and functions at 3 parameters.
- **TDD Mandatory**: All code logic changes must start with a failing test (Red-Green-Refactor).
- **Platform/Toolchain Rules**: Dictates PEP 723 for Python, Bun for TS, cargo nextest/clippy/miri for Rust, and golangci-lint v2/nilaway for Go.

## ANTI-PATTERNS
- **Non-Exhaustive Matching**: Matching variants/discriminated unions using `if`/`elif`/`else` instead of exhaustive `match`/`switch`.
- **One-off Helpers**: Creating abstract helper functions for single-use cases without multiple callers.
- **Post-Action Checks**: Verifying actions (delete, write, setter) immediately after execution via extra database/filesystem queries.
