# QWeave Implementation Roadmap

This roadmap tracks the repository audit baseline from 2026-10-12 and the local integration work since then. Work should be split into small commits, preserve existing interfaces, and retain independent owners' boundaries. No performance or novelty claim should be added without new reviewed evidence. Local changes have not been pushed.

## Stage 1: Make the current package easy to run

1. **Implemented locally:** `python -m qweave` / installed `qweave` provide `compile`, `validate`, and help; QASM2 deterministic and checkpoint-based learned routes; exclusive output; topology constructors; optional scheduling; validation summary.
2. **Implemented locally:** checked-in QASM example and documented CLI commands; tests cover compile, validate, learned route, topology errors, malformed input, and output preservation.
3. **Implemented locally:** FastAPI/Uvicorn `web` extra and API tests cover health, circuit/layout catalogs, served UI, topology validation, compile failures, and portable exports. Clean extra-install and browser verification remain to be completed.
4. **In progress:** README commands/extras are reconciled; refresh final test counts only after the full suite passes. Keep historical release/reproduction counts explicitly dated.

Acceptance: a clean Python 3.11+ install can run `python -m qweave --help`, compile an example, validate its output, run pytest, and optionally launch the web extra. The deterministic compiler remains usable without installing Torch. Still pending clean-install and complete-suite verification.

## Stage 2: Reconcile correctness documentation and interfaces

1. Update `docs/PROOF_TEST_MATRIX.md` to reflect `test_scheduler_verification.py`, corrupted-schedule rejection, and the direct makespan-bound checks; distinguish code tests from mathematical proof scope.
2. Re-review `docs/CORRECTNESS_REVIEW.md`: it is labeled as an open-issue list but includes findings that may have been resolved or superseded. Verify each issue against current tests before retaining it.
3. Add `RESEARCH_METHOD.md` with implemented objectives, mapping/routing contract, scheduler scope, current RL state/reward, training configuration, benchmark protocol, and limitations.
4. Add `RESULTS.md` by summarizing only tracked reviewed records. Explicitly state the v2 null paired depth result against weighted routing/SABRE and the synthetic hardware-cost boundary.

Acceptance: a reader can map each public claim to code, a test, or a versioned raw record; unresolved claims are labeled unverified or out of scope.

## Stage 3: Decide and specify critical-path routing

1. Decide whether the research contribution requires routing over a ready-operation frontier/DAG or whether the current sequential source-operation environment is the intended baseline.
2. If DAG routing is required, define a versioned environment observation/action contract covering ready gates, dependencies, mapping, hardware edges, and depth state. Keep the existing environment API stable or add a separately named version.
3. Specify the reward mathematically, including normalization and coefficients. Compare incremental depth, terminal depth, and potential-based distance terms without double-counting.
4. Add deterministic scripted policies and tests before changing PPO: readiness, dependency preservation, parallel execution, action masks, resource limits, and fallback layout validation.
5. Only then train a controlled policy and add a preregistered ablation. Current v2 results are a baseline and do not show learned depth gains.

Acceptance: environment transitions preserve dependencies and semantics; the reward matches the documented objective; route success/fallback rates and depth are reported per frozen case.

## Stage 4: Improve training reproducibility

1. Extend checkpoint payloads with optimizer state, global step, configuration, and Python/NumPy/Torch RNG state if training resume is required.
2. Add interrupted-versus-uninterrupted deterministic training tests for a tiny fixed fixture.
3. Keep curriculum changes, validation selection, and test-set access explicit in run metadata.
4. Preserve raw failure/timeout records and checkpoints in unique run directories.

Acceptance: a resumed run continues from a recorded state and its configuration/provenance can be audited; no test case leaks into training or selection.

## Stage 5: Evaluate optional SABRE imitation

1. Keep this optional and outside the deterministic core.
2. Define whether expert actions are obtained from instrumented SABRE internals or a clearly named approximation. Do not infer hidden decisions from a transpiled circuit without evidence.
3. Store expert state/action schema, source circuit hash, topology, Qiskit version, seeds, and trajectory validity.
4. Compare scratch PPO and imitation-initialized PPO under the same frozen train/validation/test protocol.

Acceptance: trajectory labels are reproducible and legal; imitation is reported as an ablation and does not block compiler use.

## Stage 6: Broaden experimental evidence

1. Retain benchmark v1/v2 unchanged. Introduce any external MQT Bench/QASMBench or device-derived suite as a new version with frozen hashes and splits.
2. Run held-out topologies/families and enough independent circuit instances for the intended statistical claims.
3. Keep native gate basis, direction lowering, scheduling stage, and time measurement comparable across methods; record algorithm-specific configuration.
4. Re-run from a clean environment and compare all non-runtime outputs before editing manuscript claims.
5. Report counterexamples, failures, fallbacks, uncertainty, and exact reproduction commands alongside aggregate metrics.

Acceptance: results are produced from immutable inputs, validated per method, independently reproducible, and phrased no more broadly than the test population supports.

## Priority summary

| Priority | Work | Reason |
|---|---|---|
| P0 | Verify package CLI, examples, web extra/tests | Functionality and focused coverage now exist; clean supported-version installation and full-suite verification remain. |
| P0 | Correct stale correctness/status documentation | Existing proof matrix and open-issue review do not match the expanded tests/current interfaces. |
| P1 | DAG/frontier critical-path environment specification | The central hypothesis is not represented explicitly by the current sequential-operation environment. |
| P1 | Resumable PPO state | Existing model checkpoint save/load supports inference, not continuing an interrupted optimizer run. |
| P2 | SABRE imitation | Optional and absent; requires an honest trajectory source. |
| P2 | New external/device-derived benchmarks | Current benchmark evidence is synthetic, finite, and reports no learned depth advantage. |

## Out of scope until separately justified

- Replacing the working deterministic router or current benchmark datasets.
- Claiming optimal routing from the CP-SAT initial-mapping oracle.
- Claiming calibrated fidelity from synthetic duration/error profiles.
- Claiming learned, GNN, critical-path, or state-of-the-art superiority from the current benchmark.
- Changing shared interfaces without a versioned contract and migration tests.

