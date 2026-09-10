# SWE-bench Lite × 37: blind-written patches, official grading, and a frozen evidence manifest

**English (short)** — 37 real GitHub issues from SWE-bench Lite were patched *without looking at the
upstream fix or the benchmark's `test_patch`*, each with a root-cause write-up and a **self-reported
confidence label written before grading**. All 37 patches were then graded by the official
`swebench` harness: **25 resolved, 12 unresolved, 0 apply failures, 0 infrastructure failures**.
Every failure applied cleanly and failed on behaviour the benchmark's hidden tests encode.

**中文（简短）** — 对 SWE-bench Lite 中 37 个真实 issue，在不看上游修复、不看 `test_patch` 的条件下
盲写补丁，并在评分前写定自报置信度；随后全部用官方 `swebench` harness 实跑判定：
**25 条通过、12 条未通过、0 条补丁应用失败、0 条基础设施失败**。12 条失败全部是"补丁应用成功、
但未满足官方判定"。原清单、置信度原文与评测日志均按原样保留，未事后回填。

> This is a **small-N observational study plus a reproducible protocol**, not a leaderboard claim.
> Read [Scope and limitations](#scope-and-limitations) before quoting any number.

---

## What is in this repository

| Path | What it is |
|---|---|
| `runs/<instance_id>/patch.diff` | the patch, written blind (37/37) |
| `runs/<instance_id>/summary.md` | root cause + **self-reported confidence**, written before grading (37/37) |
| `runs/<instance_id>/verify.py` | author's own verification script — **only 19/37 instances have one**; not back-filled |
| `comparison.md` | **single source of truth**: 37-row table, failure sub-modes, calibration read-out, attribution rules |
| `MANIFEST_v1.json` / `MANIFEST_v1.md` | frozen evidence: SHA-256 of every artifact, dataset hash, image digests, environment versions |
| `RESULTS.md` | original production log (kept verbatim) + a dated "measured" section |
| `TECH_REPORT.md` | report skeleton: motivation, method, results, failure modes, implications |
| `logs/run_evaluation/tonight/...` | official harness output per instance (`report.json`, `test_output.txt`, `eval.sh`) |
| `V2_PLAN.md`, `runs_v2/` | the next condition (feedback-informed repair) — scaffolded, **not yet run** |
| `predictions_swebench.jsonl` | exact harness input; patch text is SHA-256-identical to `runs/*/patch.diff` |
| `tools/` | the network workarounds used to reach Docker Hub from WSL (TCP forwarder, dockerd proxy drop-in) |
| `notes/` | raw working log of the image-channel attempts and the pre-evaluation report draft |

## Headline numbers

| Metric | Value |
|---|---|
| Instances graded | 37 / 37 |
| **Resolved (FAIL_TO_PASS green, PASS_TO_PASS clean)** | **25 = 67.6%** |
| 95% Wilson interval | 51.5% – 80.4% |
| Patch failed to apply | 0 |
| Infrastructure failures (image/container/timeout) | 0 |
| Failures that applied but did not satisfy the official verdict | 12 |
| Self-reported `high` but failed | 8 |
| Self-reported `medium`/`medium-high` but passed | 2 |

Failure sub-modes of the 12 unresolved instances (mechanism only as far as the logs show):

| Sub-mode | n | Examples |
|---|---|---|
| M1 behaviour-contract details vs the target tests (message text, warning vs error level, ordering, CLI format) | 7 | `django-11630` (warning/error level inverted), `django-11283` (no warning printed), `pylint-6506` (argparse layer instead of `E0015`) |
| M2 runtime/syntax defects in the patch itself | 3 | `django-11001` (invalid SQL), `django-12308` (`TypeError`), `django-12856` (`'Q' object is not callable`) |
| M3 target test passed but a PASS_TO_PASS regression | 1 | `django-12589` |
| M4 incomplete fix | 1 | `django-11797` |

The umbrella category is deliberately **"applied but did not satisfy the official verdict"**, not
"semantically different from upstream": the harness log proves the target tests failed, it does not
prove how this implementation differs from the upstream commit. No upstream diff was consulted.

## Scope and limitations

Please quote these alongside any number above.

- **Not a leaderboard result.** 33 of the 37 instances are Django, the subset was not randomly
  sampled, and it was graded once. The 95% interval spans 51.5%–80.4%.
- **No validation gate in the loop.** The workflow had no reproduction/regression gate, so the three
  M2 failures are errors a single run would have caught. Mature scaffolds (e.g. Agentless-style
  validation) filter these, so this number is not comparable to scaffold results on the full benchmark.
- **Human in the loop.** 25 of the patches were produced in a supervised single-stream session; the
  system under measurement is "human + client model + no gate", not the model alone.
- **No variance estimate.** Single run; no re-run, so the noise floor is unknown.
- **Artifact coverage is uneven.** `verify.py` exists for 19/37 only; "every patch was self-verified"
  is **false** for this dataset. Missing files were not back-filled, to preserve the blind trajectory.
- **Contamination cannot be excluded.** Not reading the upstream fix guarantees the author did not look;
  it does not prove the model never saw these issues in training.
- **Attribution is bounded by the logs.** Mechanisms are read off failing test names, assertion text and
  exception types; expectations inferred from `test_patch` failures are post-hoc information and are
  labelled as such in `TECH_REPORT.md`.

## Reproduce

```bash
# 1) dataset (not committed here on purpose)
#    SWE-bench/SWE-bench_Lite, split=test   (MIT licensed)
#    local parquet sha256: see MANIFEST_v1.json -> dataset.sha256

# 2) predictions (already provided, hash-verified against runs/*/patch.diff)
#    predictions_swebench.jsonl  == predictions.jsonl with key `patch` -> `model_patch`

# 3) grading (WSL2 + Docker; ~68 min, zero LLM tokens)
HF_ENDPOINT=https://hf-mirror.com python3 -m swebench.harness.run_evaluation \
  -d SWE-bench/SWE-bench_Lite -s test \
  -p predictions_swebench.jsonl -id tonight --max_workers 4

# 4) rebuild the comparison table and the manifest
python analyze_results.py
python make_manifest.py      # re-prints a self-check: delta mismatches / image digests / verify coverage
```

Integrity check: `MANIFEST_v1.json` records, per instance, the SHA-256 of `patch.diff`, `summary.md`,
`verify.py`, the harness `report.json` / `test_output.txt`, plus dataset hash, image `RepoDigests` and
tool versions. Any edit to a graded artifact will show up as a hash mismatch.

Run the bundled verifier to recompute all of them instead of taking that on trust:

```bash
python verify_manifest.py          # exit 0 = every recorded hash matches
# expected: 170 hashes checked, 18 absent by design (verify.py exists for 19/37)
```

**About the helper scripts.** They were written against one machine and published with local paths
redacted: an absolute path shows up as `<EXP_ROOT>` (or `<HOME>` / `<EXP_ROOT_POSIX>`) inside
`*.py`, `*.sh` and the reports. Replace those placeholders with your own checkout path before running
them — or just read them as documentation of the exact commands that were used. The evidence files
(`patch.diff`, `summary.md`, `report.json`, `test_output.txt`, `predictions*.jsonl`) were **not**
rewritten, so their recorded hashes still hold.

## Why this might be interesting

1. **Confidence was verbalised before grading**, per instance, by the same agent that wrote the patch —
   and every label can be traced to the specific assertion that failed. `high` went 23/31,
   `medium-high` 2/4, `medium` 0/2.
2. **The failure split is actionable.** 7 of 12 failures are contract details a local self-test cannot
   see; 3 are defects a single run would have caught. Those two need different fixes.
3. **The protocol is auditable.** Blind-write discipline, frozen manifest, and an explicit separation
   between the blind condition (v1) and the feedback-informed condition (v2, not yet run).

## Not yet done

- `v2-repair` (the 12 failures, with an output-contract checklist) and `v1-blind-repeat` (variance floor).
- Per-instance upstream diff comparison — until then, no claim about "how this differs from upstream".

## Licence and attribution

Original content (patches, write-ups, scripts, reports) is released under the MIT licence — see
`LICENSE`. Third-party material and its terms are listed in `NOTICE`; the SWE-bench dataset itself is
**not** redistributed here.

*AI-assisted development: the patches and write-ups in this repository are AI-generated content
(GLM-family model, human-reviewed) — 本仓库含人工智能生成合成内容 — non-commercial research use only.
Provider terms, per-file licences and the full disclosure are in [NOTICE](NOTICE).*
