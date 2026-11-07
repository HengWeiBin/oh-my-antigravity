---
name: eval-integrity
description: "High-rigor evaluation and benchmark integrity auditing skill. Audits benchmark suites, LLM-as-a-judge setups, test holdout contamination, data leakage, and rubric hacking to ensure genuine model and prompt capabilities. Triggers: 'eval integrity', 'benchmark audit', 'contamination audit', 'rubric audit', 'eval-integrity', 'evaluation integrity', 'test leakage', 'judge gaming'."
---

# Eval Integrity — Benchmark & Evaluation Rigor Audit

Audit evaluation pipelines, test suites, benchmark datasets, and LLM-as-a-judge configurations against contamination, metric gaming, rubric leakage, and false-confidence artifacts.

## Core Mandate

An evaluation suite that can be gamed or contaminated is worse than no evaluation suite: it produces false confidence while shielding regressions. This skill conducts forensic, evidence-grounded audits of evaluation harnesses to guarantee that reported benchmarks reflect genuine capability rather than memorization, artifact leakage, or metric exploitation.

All audits must produce grounded evidence using Antigravity native inspection tools (`view_file`, `grep_search`, `run_command`, `invoke_subagent`). Never accept self-reported benchmark scores without verifying raw test cases and evaluation logs.

---

## The Four Core Audit Dimensions

Every evaluation integrity audit rigorously inspects four orthogonal dimensions:

| Dimension | Focus | Critical Vulnerabilities |
|---|---|---|
| **1. Benchmark Contamination** | Training/eval split leakage & test set memorization | Verbatim test prompts in pre-training or fine-tuning corpora, few-shot prompt contamination, leaked test questions in synthetic data pipelines. |
| **2. Metric Gaming** | Exploiting evaluator heuristics rather than semantic correctness | Length bias (longer answers favored by LLM judges), keyword-matching shims, format-compliance rewards without logical reasoning, hardcoded heuristic shortcuts. |
| **3. Rubric Ambiguity** | Vague, contradictory, or under-specified judge criteria | Non-orthogonal scoring dimensions, undefined tie-breakers, conflicting constraints between system and evaluation rubrics, high judge variance across seeds. |
| **4. Holdout Integrity** | Validation/test set contamination & cross-split bleed | Leaked evaluation seeds, cross-fold overlap in split data, train/eval shared context, repeatedly querying test holdout without correction penalties. |

---

## Tooling & Antigravity Native Adaptation

In Google Antigravity, all evaluation audits are executed directly through canonical environment tools:

- `view_file`: Direct inspection of evaluation datasets (JSONL, CSV, Parquet), judge system prompts, scoring scripts, and test configurations.
- `grep_search`: High-speed regex and string scanning for verbatim test prompts across training manifests, prompt templates, and synthetic generators.
- `run_command`: Running evaluation harnesses, calculating contamination metrics (n-gram overlap, token Jaccard similarity), executing pytest test suites, or running statistical profiling scripts.
- `invoke_subagent`: Spawning parallel, independent forensic review oracles (`TypeName: "oracle"`) to evaluate rubrics and verify that edge cases cannot bypass test assertions.

---

## Audit Workflow

### Phase 0: Scope & Inventory Discovery

1. Identify evaluation targets:
   - Benchmark test sets, question banks, or golden datasets.
   - LLM-as-a-judge prompts, rubrics, and pairwise comparison configurations.
   - Scoring code (Python scripts, custom loss/metric calculations, regex extractors).
   - Training datasets, few-shot pools, or system prompt templates.
2. Document target file paths, row counts, and scoring definitions before running any checks.

### Phase 1: Holdout & Benchmark Contamination Audit

Detect whether evaluation queries, ground-truth answers, or near-duplicates exist in prompt templates, fine-tuning data, or few-shot examples.

1. **Exact-Match & Substring Scanning**:
   Use `grep_search` to check distinctive question stems or unique entity strings from the evaluation dataset against prompt libraries and synthetic data generators.
2. **N-gram Overlap & Near-Duplicate Analysis**:
   Use `run_command` with a Python one-liner to compute 8-gram or 13-gram overlap between the evaluation holdout and training/prompt sets:
   ```powershell
   uv run python -c "import json; # check n-gram containment"
   ```
3. **Few-Shot Isolation**:
   Verify that few-shot in-context demonstrations are strictly quarantined from evaluation test cases. A test sample must NEVER appear as a few-shot demonstration.

### Phase 2: LLM-as-a-Judge & Rubric Audit

Examine judge prompts and scoring scripts for structural biases and rubric ambiguities:

1. **Position Bias**:
   In pairwise evaluations (Model A vs Model B), verify whether candidate ordering is swapped (A/B and B/A) to control for position preference. If ordering is fixed, flag as **Compromised**.
2. **Length Bias**:
   Check if the judge prompt or downstream score correlates with verbosity rather than correctness. Verify whether concise, correct answers are penalized compared to verbose, fluffed responses.
3. **Self-Enhancement / Model Bias**:
   Check if the evaluator model is identical to the target model family, potentially favoring its own stylistic quirks and token frequencies.
4. **Rubric Precision**:
   Inspect rubric definitions via `view_file`. Are score bands (1 to 5) clearly differentiated with concrete behavioral anchors? Do rubrics handle partial correctness and silent failures deterministically?

### Phase 3: Metric Gaming & Shortcut Detection

Check whether the benchmark metric can be trivially satisfied by non-solution shortcuts:

1. **Heuristic Exploitation**:
   Inspect scoring functions for keyword presence checks (`if "success" in output:`), superficial formatting gates (e.g. JSON schema presence without payload validation), or regex bypasses.
2. **Deterministic Triviality**:
   Can a dummy model outputting constant values or random guesses achieve >20% score?
3. **Adversarial Perturbation**:
   Test how small, semantically invariant alterations (typos, swapped variable names, whitespace shifts) impact the benchmark score. Extreme sensitivity indicates overfitting to exact token sequences.

### Phase 4: Independent Oracle Verification

For complex benchmarks or subtle rubric ambiguities, dispatch an independent read-only oracle subagent via Antigravity native orchestration:

```typescript
invoke_subagent({
  Subagents: [
    {
      TypeName: "oracle",
      Role: "Eval Integrity Auditor",
      Prompt: `TASK: Audit this LLM-as-a-judge rubric and dataset for contamination and gaming vulnerabilities.
DATASET PATHS: [paths to eval datasets]
JUDGE PROMPT: [verbatim rubric text]
SCORING SCRIPT: [path to scorer]
Verify whether a model could game the rubric with superficial formatting, length expansion, or keyword stuffing without genuine correctness.`
    }
  ]
})
```

### Phase 5: Synthesis & Reporting

Compile the audit findings into a standardized `EVAL_INTEGRITY_AUDIT.md` report with one of four overall integrity verdicts:

- **Pristine**: Complete separation between train/eval, robust debiasing, precise rubrics, zero evidence of leakage or shortcut gaming.
- **Minor Risk**: Clean holdouts, but rubric has minor ambiguities or length sensitivity that warrants calibration.
- **Compromised**: Evidence of partial contamination, unmitigated position/length bias in judges, or easily gameable heuristic scoring.
- **Invalid**: Evaluation set is leaked, heavily contaminated, or trivially bypassed by dummy answers; benchmark scores cannot be trusted.

---

## Output Template (`EVAL_INTEGRITY_AUDIT.md`)

```markdown
# Evaluation Integrity Audit Report

## Executive Summary
- **Overall Verdict**: [PRISTINE | MINOR RISK | COMPROMISED | INVALID]
- **Audited Target**: [eval suite / benchmark name / file paths]
- **Key Finding**: [One-sentence summary of highest-severity finding]

## Dimension Scores & Findings

| Dimension | Verdict | Evidence / Observation |
|---|---|---|
| Benchmark Contamination | PASS / RISK / FAIL | [Leakage / n-gram overlap results] |
| Metric Gaming | PASS / RISK / FAIL | [Length bias / keyword bypass findings] |
| Rubric Ambiguity | PASS / RISK / FAIL | [Score separation / position bias control] |
| Holdout Integrity | PASS / RISK / FAIL | [Split hygiene / seed isolation] |

## Located Vulnerabilities & Exploit Vectors
1. **[Dimension]** - [Issue Title]
   - **Location**: `path/to/file:line`
   - **Observed Behavior**: [Verbatim snippet or calculation]
   - **Exploit Vector**: [How a model or engineer could game this]
   - **Remediation**: [Concrete patch or redesign recommendation]

## Remediation Plan
- [ ] Action item 1
- [ ] Action item 2
```

---

## Anti-Patterns & Red Lines

- ❌ NEVER calculate benchmark scores on training or few-shot demonstration samples.
- ❌ NEVER use single-turn pairwise judge evaluation without position-swapped (A/B and B/A) runs.
- ❌ NEVER allow keyword-presence checks to substitute for AST, semantic, or unit test verification.
- ❌ NEVER ignore length-to-score correlation in LLM-as-a-judge pipelines.
- ❌ NEVER report benchmark percentages without documenting sample size, error margins, and holdout splits.
