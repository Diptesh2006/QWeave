# QWeave Results

This summary uses the checked-in v0.2.0 benchmark-v2 report and artifacts. It does not claim that this audit independently reran the 792-record study. See [the detailed report](results/benchmark_v2/REPORT.md), [raw records](results/benchmark_v2/raw.json), [summary](results/benchmark_v2/summary.json), and [protocol](docs/BENCHMARK_V2_PROTOCOL.md).

## Benchmark v2

The frozen test split has 36 generated cases from held-out QFT and hardware-efficient families at widths four, six, and eight, across grid, chorded-ring, and idle-site hardware. The packaged study contains 792 method/seed/case records.

The checked-in report records that all 792 outputs passed their applicable numerical semantic check, and all direction-lowered cost circuits passed ordered-coupler legality. QWeave routes also passed symbolic replay. These are results within the stated validator and synthetic test scope, not universal equivalence proofs for arbitrary programs.

| Comparison | Paired median depth difference | 95% bootstrap interval | Interpretation |
|---|---:|---:|---|
| GNN-PPO minus weighted | 0 gates | [0, 0] | No paired median depth improvement in this test suite. |
| GNN-PPO minus SABRE | 0 gates | [0, 5] | No demonstrated depth advantage over SABRE. |
| GNN-PPO minus no-message PPO | 0 gates | [0, 0] | No measured message-passing depth benefit in this setup. |

PPO improved over the untrained graph control in the reported suite, but learned methods had substantially more fallbacks than deterministic methods. Weighted deterministic routing had zero fallback events in the report. Results are not evidence of general superiority, optimal routing, or production performance.

## Cost and scheduling scope

The scheduler operates on each already compiled route. The report gives zero unit-duration depth delta for fixed routes. This is not a routing improvement. Direction lowering adds gates/depth to make circuits legal on one-way synthetic couplers. The cost profile and edge error values are synthetic proxies, not calibration data; the estimated success probability is not measured hardware fidelity.

## Historical smoke results

Two tracked smoke runs from the earlier v0.1 implementation are in `results/`. They cover three four-qubit CX-only circuits on one four-site line and are sanity checks, not a frozen benchmark. Historical per-method metrics and their limitations are described in `docs/BASELINE_AUDIT.md`.

## Local verification

On 2026-10-12, the latest completed local test run on the audited checkout passed **80 tests** in **45.06 seconds** after the environment was supplied `gymnasium` and `hypothesis`. The Python environment was 3.13.7 with Qiskit 2.5.2, NetworkX 3.5, NumPy 2.3.3, pandas 2.3.2, and OR-Tools 9.15.6755. A subsequent rerun was interrupted and is not counted as a test result.

## Evidence boundary

The benchmark artifacts are reproducible, versioned synthetic evidence. They do not establish the central critical-path-aware learning hypothesis, since the current environment uses sequential source-operation progress and the measured GNN-PPO did not improve paired median depth over weighted routing. A new method, benchmark protocol, and independently reviewed raw run are required before making a different claim.

