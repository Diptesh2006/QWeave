# Claim Audit

## Abstract
- "Every tested output passed its applicable numerical semantic check..." -> MEASURED (`REPORT.md`, Semantic column). **MATCH**.
- "...and every direction-lowered cost circuit passed ordered-coupler legality." -> MEASURED (`REPORT.md`, Directed column). **MATCH**.
- "The paired GNN--PPO minus weighted depth difference was 0 gates with a 95% bootstrap interval of [0,0]." -> MEASURED (`REPORT.md`, Paired comparisons). **MATCH**.
- "GNN--PPO and no-message-passing PPO also had paired median depth and SWAP differences of 0 with intervals [0,0]." -> MEASURED (`REPORT.md`, Paired comparisons). **MATCH**.
- "Training strongly improved on the untrained policy..." -> INTERPRETATION.
- "...but the study does not show a message-passing or learned-routing advantage over the deterministic references." -> INTERPRETATION.

## Section 2 & 3
- "This guard ensures termination and legality on connected undirected hardware with contiguous labels, but may hide a weak policy behind fallback" -> PROOF (Theorem 1, Theorem 4).
- "The theoretical guarantees underpinning both the deterministic architecture and the learned routing policy are formalized in Section \ref{sec:formal_guarantees}." -> INTERPRETATION.

## Section 4
- "The structural validator checks mapping completeness, injectivity, source gate replay, inserted SWAP consistency, global phase, and undirected edge legality for every two-qubit emitted operation." -> PROOF (Theorem 1, Lemma 1).
- "Edge legality alone cannot establish that the logical unitary was preserved." -> INTERPRETATION.
- "For equal-width small unitary circuits, the test oracle constructs the permutations induced by initial and final layouts and checks $U_{\mathrm{routed}} P_{\mathrm{initial}} = P_{\mathrm{final}} U_C$." -> PROOF (Theorem 2).
- "The exact check covers equal-width circuits of at most six qubits." -> PROOF (A10).
- "Benchmark version 2.0 freezes 180 cases at four, six, and eight logical qubits..." -> MEASURED (`summary.json` records). **MATCH**.
- "We report family quartiles, validity, fallbacks, runtime distributions, counterexamples, and deterministic 95% bootstrap intervals from 5,000 resamples with seed 20260921." -> MEASURED (`summary.json` bootstrap config). **MATCH**.

## Section 5
- "A fresh local run passed 69 tests under Python 3.11.15 and Qiskit 2.5.2." -> MEASURED (Local pytest run). **MISMATCH** (Current local test count is 80 tests).
- "The aggressive validation candidate scored 19.5; conservative and standard each scored 24.0." -> MEASURED (`REPORT.md`). **MATCH**.
- "Table \ref{tab:test-results} reports the 36-case held-out test aggregate." -> MEASURED (`REPORT.md`). **MATCH**.
- "All 792 outputs passed their applicable numerical semantic check." -> MEASURED (`REPORT.md`). **MATCH**.
- "Every unit-duration scheduling delta was zero." -> MEASURED (`REPORT.md`). **MATCH**.
- "The paired GNN--PPO minus weighted depth difference was 0 gates with interval [0,0]; versus SABRE it was 0 with interval [0,5]." -> MEASURED (`REPORT.md`). **MATCH**.
- "Its paired SWAP difference versus weighted routing was 0 with interval [0,5]." -> MEASURED (`REPORT.md`). **MATCH**.
- "GNN--PPO and no-message PPO had paired median depth and SWAP differences of 0 with intervals [0,0]" -> MEASURED (`REPORT.md`). **MATCH**.
- "the paired GNN--PPO depth difference was -162.5 with interval [-184,-106], and the SWAP difference was -175 with interval [-223,-148]." -> MEASURED (`REPORT.md`). **MATCH**.
- "On hardware-efficient circuits, weighted, GNN--PPO, and no-message PPO all had median depth 27 and no SWAPs." -> MEASURED (`REPORT.md`). **MATCH**.
- "On QFT, weighted routing had median depth 71.5 and 16.5 SWAPs, GNN--PPO had 83.5 and 41, and no-message PPO had 90 and 31.5." -> MEASURED (`REPORT.md`). **MATCH**.
- "GNN--PPO improved by eight depth layers on qft_i1_6q_chorded_ring, but regressed by 89 layers and 130 SWAPs on qft_i1_8q_grid2." -> MEASURED (`REPORT.md`). **MATCH**.
- "The GNN policy invoked 4,543 test fallbacks, compared with 742 for no-message PPO and zero for deterministic methods." -> MEASURED (`REPORT.md`). **MATCH**.
- "Seed 29 was unstable, ending with 212 training fallbacks and a recent mean return near -103." -> MEASURED (`REPORT.md`). **MATCH**.
- "After reverse-CNOT and SWAP synthesis, all 792 cost circuits passed ordered-arc legality." -> MEASURED (`REPORT.md`). **MATCH**.
- "Median added depth was 32 for weighted routing, 34 for SABRE, 37.5 for GNN--PPO, 28.5 for no-message PPO, 57 for Basic, and 441 for the untrained GNN." -> MEASURED (`summary.json` / `REPORT.md`). **MATCH**.
- "The corrected paired GNN--PPO minus weighted makespan difference was 0 ns with interval [0,1113]." -> MEASURED (`REPORT.md`). **MATCH**.
- "These proxy costs therefore do not provide a learned advantage." -> INTERPRETATION.

## Section 6
- "The finite synthetic suite does not establish optimal routing, calibrated fidelity, production readiness, or state-of-the-art performance." -> LIMITATION / INTERPRETATION.
- "Further work should target policy stability, reduce fallback dependence, and preregister larger device-derived circuit and calibration suites before making a superiority claim." -> FUTURE WORK.

## Overclaim Analysis
Currently, there are no unmitigated overclaims remaining in the manuscript due to the prior addition of rigorous theoretical boundaries in Section 5 limitations.
