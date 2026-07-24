# ultimate-browsing

## OVERVIEW
A resilient browser template engine and custom WAF loader comprising over 25 files to bypass anti-bot and scrape challenge screens.

## STRUCTURE
c:/Users/K20879/.gemini/config/plugins/oh-my-antigravity/skills/ultimate-browsing/
├── engine/                 # Core Python generic fetch chain engine
│   ├── templates/          # Playwright JS stealth templates
│   └── tests/              # Unit and integration test suites
├── references/             # MD references (insane-search, agent-reach, chrome-stealth)
│   ├── agent-reach/        # Chinese/Social API CLI integrations
│   └── insane-search/      # Tier-1 deep-dives (TLS, WAF, Naver, etc.)
└── scripts/                # Standalone decryption/cookie extract helpers
    └── tests/              # Cookie extraction unit test suites

## WHERE TO LOOK
| Path | Purpose |
| :--- | :--- |
| [engine/fetch_chain.py](file:///c:/Users/K20879/.gemini/config/plugins/oh-my-antigravity/skills/ultimate-browsing/engine/fetch_chain.py) | Tier-1 generic fetch entrypoint (`fetch()`) managing the probe-validate-detect-execute sequence. |
| [engine/waf_detector.py](file:///c:/Users/K20879/.gemini/config/plugins/oh-my-antigravity/skills/ultimate-browsing/engine/waf_detector.py) | Live WAF detection engine utilizing headers, cookies, and body strings (site-agnostic). |
| [engine/waf_profiles.yaml](file:///c:/Users/K20879/.gemini/config/plugins/oh-my-antigravity/skills/ultimate-browsing/engine/waf_profiles.yaml) | Declarative profiles mapping signatures to WAF mitigation behaviors (TLS config, fallbacks). |
| [engine/bias_check.py](file:///c:/Users/K20879/.gemini/config/plugins/oh-my-antigravity/skills/ultimate-browsing/engine/bias_check.py) | CI verification linter enforcing the NO-SITE-NAME rule across codebase and profiles. |
| [engine/templates/playwright_real_chrome.js](file:///c:/Users/K20879/.gemini/config/plugins/oh-my-antigravity/skills/ultimate-browsing/engine/templates/playwright_real_chrome.js) | Playwright persistent Chrome execution template implementing the root Warmup Hop pattern. |
| [scripts/extract_cookies.py](file:///c:/Users/K20879/.gemini/config/plugins/oh-my-antigravity/skills/ultimate-browsing/scripts/extract_cookies.py) | CLI tool decrypting local Chrome/Firefox profile cookies and injecting them into a CDP session. |

## CONVENTIONS
- **NO-SITE-NAME Rule**: All files under `engine/**` and `waf_profiles.yaml` must remain site-agnostic. No domain names or brand selectors can be hardcoded unless marked with `# NOTE-BIAS-OK` or `# EXAMPLE-ONLY`.
- **Warmup Hop Pattern**: Visit the target site's root (`protocol://host/`) first with `domcontentloaded` and wait 3.5s to let sensor JS resolve challenge cookies before deep landing.
- **Ranked WAF Verdicts**: Return list of `(profile_id, confidence)` candidates instead of a single verdict, enabling the engine to fallback iteratively.

## ANTI-PATTERNS
- **Deep Landing First**: Direct navigation to deep target queries in templates without performing a root Warmup Hop.
- **NetworkIdle Wait**: Using `networkidle` for page loads, causing hangs on persistent analytics connections.
- **Domain Hardcoding**: Writing raw brand names/selectors in `engine` files without explicit comment bypass tokens.
