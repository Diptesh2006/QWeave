# QWeave

QWeave studies hardware-aware qubit allocation, deterministic and learned routing, and depth minimisation for NISQ quantum compilation. The correctness-first deterministic core, dependency-preserving scheduler, and guarded GNN--PPO research path are implemented as separate modules.

## Problem

Logical circuits often require interactions between qubits that are not adjacent on hardware. Mapping and routing choose a physical layout and insert SWAPs while preserving the circuit's behaviour. The primary mapping convention is `mapping[logical_qubit] = physical_qubit`.

## Architecture

```text
Qiskit circuit -> interaction graph -> weighted initial mapper -> strict local search
       |                                                        |
       +-> basic identity baseline / SABRE baseline             v
                                                deterministic fallback router
                                                           |
                                    route replay + legality validation + metrics
                                                           |
                                          depth-aware list scheduling (separate)
                                                           |
                                                JSON/CSV experiment results

weighted initial mapping -> guarded Gymnasium router -> masked GNN actor-critic
                                                   -> PPO / no-GNN / untrained controls
```

## Installation and quick start

Requires Python 3.11 or newer.

```bash
python -m pip install -r requirements.txt
python -m pip install -e ".[test,learning]"
pytest -q
python -m qweave --help

# Deterministic QASM2 compilation
python -m qweave compile --circuit examples/sample.qasm --topology line --router deterministic --output run_artifacts/sample-compiled.qasm
python -m qweave validate --circuit run_artifacts/sample-compiled.qasm --topology line

# Learned routing with a compatible checkpoint
python -m qweave compile --circuit examples/sample.qasm --topology line --router learned --checkpoint checkpoints/best.pt --output run_artifacts/sample-learned.qasm

# Install the optional web dependencies before launching the studio
python -m pip install -e ".[web]"

# Run the interactive Web UI Studio
python -m uvicorn web.server:app --host 127.0.0.1 --port 8000 --reload

# Run batch experiments and benchmarks
python scripts/run_smoke.py
python scripts/run_baselines.py
python scripts/run_scheduler_check.py
python scripts/build_benchmark_manifest.py
python scripts/run_learned_benchmark.py
python scripts/run_study_v2.py
```

The scripts create timestamped JSON and CSV files in `results/` and never overwrite an existing result. No IBM Quantum credentials or hardware are required.

## Interactive compilation studio (Web UI)

QWeave includes an interactive browser-based compilation and visualization studio located in `web/`.

### Launching the Studio
```bash
python -m uvicorn web.server:app --host 127.0.0.1 --port 8000 --reload
```
Navigate to `http://127.0.0.1:8000` in any modern web browser.

### Features
- **Circuit selection and upload**: Select from built-in algorithmic presets (GHZ, Bernstein–Vazirani, QAOA MaxCut, QFT, Star graph, CNOT chains, HEA), drag-and-drop `.qasm` circuit files, or enter code in the integrated OpenQASM 2.0 editor.
- **Hardware architecture explorer**: Choose standard topologies (linear paths, cycles, 2D grids, chorded rings, star, IBM Manila T-shape) or supply custom coupling edge lists.
- **Routing method selection & comparison**: Compile circuits via QWeave Weighted (interaction degree seeding + strict local search + fallback router), QWeave Basic (identity mapping), Qiskit SABRE, or run all three simultaneously for side-by-side comparative evaluation.
- **Metrics and validation**: Inspect inserted SWAPs, source vs. routed depth, depth overhead, gate counts, two-qubit execution counts, and automated legality/unitary verification status.
- **Circuit diagram & code export**: View monospace routed circuit diagrams, structured gate layers, and copy or download the generated physical OpenQASM 2.0 file.
- **Step-by-step route replay**: Interactive trace scrubber and canvas animator allowing users to step or play through every routed operation and watch logical qubits swap across physical hardware couplers.


## Implemented algorithms

`build_interaction_graph` counts two-qubit interactions, optionally using `decay ** gate_index`. The weighted mapper seeds the highest interaction-degree logical qubit on a high-centrality hardware node, then greedily minimises weighted distance to assigned neighbours. Ties are deterministic. Local search evaluates all pairwise exchanges and accepts only strict objective decreases, so it terminates after finite descent or the configured iteration limit.

The fallback router processes operations in order, advances one logical qubit along a deterministic shortest path with hardware-edge SWAPs, and updates the layout after every inserted SWAP. It preserves source global phase and returns a trace with one event per emitted operation; validation replays that trace against the source gates, classical destinations, and final layout before edge-legality checks. The Qiskit adapter accepts unconditioned one- and two-qubit gates, one-qubit resets, and a terminal measurement suffix. It rejects barriers, three-plus-qubit gates, dynamic control flow, classically conditioned gates, directed/multigraph routing inputs, and invalid physical labels. This is a declared gate-family limit, not a general semantic proof.

The Basic baseline uses identity mapping plus this router. The SABRE adapter delegates to Qiskit with a fixed seed, symmetric coupling edges for the same undirected routing interpretation, and validates physical edge legality. Equal-width unitary circuits of at most six qubits use an exact layout-aware unitary check. Wider circuits and outputs with idle physical sites use deterministic layout-aware statevector probes up to 12 physical qubits. Resets and terminal measurements remain structurally replayed rather than numerically simulated. Dynamic classical control is still unsupported.

Directed hardware is evaluated as a separate lowering stage. Reverse CNOTs are synthesized by Hadamard conjugation around an available forward CNOT, and SWAPs are decomposed into three direction-lowered CNOTs. Declared durations and synthetic edge-error costs are computed only after the lowered circuit passes ordered-coupler legality.

The list scheduler operates only after a legal route is fixed. It builds dependencies from each physical qubit's gate order, ranks ready gates by remaining critical path, and records earliest start/finish times and layers. Optional positive gate durations produce a timed makespan. It never reroutes or swaps gates across a shared wire. Its `depth_delta` is `scheduled_depth - routed_depth` for the same circuit; under unit durations this is normally zero because Qiskit already computes parallel dependency depth.

`qweave.core.compiler.compile_deterministic(circuit, graph, method="basic" | "weighted", schedule=False)` is the integrated reference entry point. It returns the routing result, initial layout, small-unitary status (or `None` outside scope), and separate source/routed/scheduled stage metrics. SABRE and CP-SAT remain separate comparison methods; the latter is never a routing result.

## Formal guarantees

The core correctness constraints and compiler algorithms are backed by formal mathematical proofs documenting routing termination, layout legality, semantic equivalence, and post-routing makespan lower bounds.
- **[Assumption Register](docs/ASSUMPTION_REGISTER.md)**: Documents the explicit scope of compilation (e.g. injective mapping, unconditioned operations).
- **[Proof-Test Matrix](docs/PROOF_TEST_MATRIX.md)**: Links each formalized lemma and theorem to its deterministic property-based test.
- **[Mathematical Foundations](paper/theory.tex)**: Contains the LaTeX theorems, notations, and theoretical proofs underpinning the routing architectures.
- **[Correctness Review](docs/CORRECTNESS_REVIEW.md)**: Audits alignment between the implemented architecture and the theoretical proofs, resolving discrepancies and open issues.
- **[Scheduler Note](docs/SCHEDULER_NOTE.md)**: Confirms the fixed-route scheduling algorithm and ratio metric constraints.

## Objective and metrics

For interaction edge `(i, j)`, the mapping objective is `weight(i,j) * shortest_path_distance(mapping[i], mapping[j])`, summed over all interaction edges. Metrics include depth, total operations, two-qubit operations, SWAPs, runtime, absolute depth overhead, and zero-safe relative overhead.

## CP-SAT oracle scope

The CP-SAT implementation is an exact initial-mapping oracle for small instances (limited to eight logical qubits). It does not claim to solve optimal routing and is intentionally unsuitable for production-scale compilation.

## Testing and reproducibility

The committed v0.2.0 verification record reports 69 tests on its documented clean-clone environment. A later local run on the current checkout passed 80 tests under Python 3.13.7, Qiskit 2.5.2, NetworkX 3.5, NumPy 2.3.3, pandas 2.3.2, and OR-Tools 9.15.6755 after installing the test and learning dependencies. The suite covers graph weights and decay, mapping and strict descent, route replay and layout consistency, semantic checks, directed lowering, scheduling verification, guarded Gymnasium behavior, action masking, PPO, benchmark manifests, SABRE, paired statistics, and the mapping oracle. See `RESULTS.md` for local run context and `PROJECT_AUDIT.md` for scope and gaps.

`scripts/run_scheduler_check.py` writes a new immutable JSON record for three four-qubit smoke circuits on a four-site line. It reports Basic, weighted, and SABRE routed versus scheduled depth on each *fixed* compiled circuit. CP-SAT contributes only its small initial-mapping objective/status. This check is not a frozen benchmark or evidence of general improvement.

For the comparative study, see [the experiment protocol](docs/EXPERIMENT_PROTOCOL.md), [learned-routing scope](docs/LEARNED_ROUTING.md), [validation scope](docs/VALIDATION_SCOPE.md), and [local baseline audit](docs/BASELINE_AUDIT.md). The [manuscript source](paper/manuscript.tex) is updated only from reviewed raw records.

The frozen benchmark-v1 run produced 64 test records: every output passed the
small-unitary check and every fixed-route unit-duration scheduling delta was
zero. GNN--PPO, no-GNN PPO, and the untrained graph control had the same
aggregate depth and SWAP medians, so the run does not isolate a learning
benefit. See the [reviewed report](results/BENCHMARK_V1_REPORT.md) and
[machine-readable summary](results/benchmark_v1_summary.json).

The pushed baseline was independently reproduced from a clean clone; see the
[reproduction audit](docs/REPRODUCTION_AUDIT_2026-09-21.md). Benchmark v2 is
frozen before evaluation in the [v2 protocol](docs/BENCHMARK_V2_PROTOCOL.md)
and [immutable manifest](benchmarks/benchmark_v2_manifest.json).

Benchmark v2 contains 180 frozen cases and 36 untouched test cases. The full
study produced 792 method/seed/case records, ten endpoint checkpoints, and
five-seed learning curves. Every tested output passed its applicable numerical
semantic check, and every direction-lowered cost circuit passed directed
legality. The paired GNN--PPO minus weighted depth difference was 0 gates with
a 95% bootstrap interval of [0, 0]; GNN--PPO and no-message PPO also had paired
median depth and SWAP differences of 0 [0, 0]. Training greatly improved over
the untrained graph control, but this study does not show a message-passing or
learned-routing advantage over the deterministic references. See the
[reviewed v2 report](results/benchmark_v2/REPORT.md),
[machine-readable summary](results/benchmark_v2/summary.json), and retained
[raw record](results/benchmark_v2/raw.json).

The [benchmark-v2 academic audit](docs/ACADEMIC_AUDIT_2026-09-21.md) records
the primary-source citation check, successful GitHub Actions run, locked clean
clone, 69-test result, artifact hashes, and exact full-study reproduction. The
machine-readable rerun comparison reports zero non-runtime record mismatches
and zero training-summary mismatches. See the [v0.2.0 release
notes](RELEASE_NOTES_v0.2.0.md) for the packaged scope and claim boundary.

## Current implementation status

Implemented: weighted interaction graph, initial mapping, local search, deterministic fallback routing, Basic and SABRE baselines, route replay, exact and probe-based semantic checks, reset and terminal-measurement preservation, directed-coupler lowering, depth-aware list scheduling, declared duration/error proxies, metrics, an interactive web compilation studio (`web/`), a CP-SAT mapping oracle, a guarded Gymnasium routing environment, masked graph actor-critic, PPO training, ablation controls, a frozen benchmark-v2 harness, checkpoints, and paired bootstrap analysis. Dynamic classical control and a full exact-routing formulation remain outside the current scope; the CP-SAT component remains an initial-mapping oracle only.

The current learned environment advances through a sequential source-operation pointer and bounded lookahead. It does not implement a ready-operation dependency-DAG policy or demonstrate a critical-path-aware learning advantage. No package-level `python -m qweave compile` CLI or SABRE imitation trajectory pipeline is currently provided. The README's web launch also requires FastAPI/Uvicorn, which are not yet declared as a project extra. See [the project audit](PROJECT_AUDIT.md) and [implementation roadmap](IMPLEMENTATION_ROADMAP.md) for the verified status and ordered work.

The objectives, implemented algorithms, and experimental limitations are summarized in [RESEARCH_METHOD.md](RESEARCH_METHOD.md) and [RESULTS.md](RESULTS.md).

Team roles are documented in `AGENTS.md`: Atharva Sheersh Pandey owns integration and Qiskit adapters; Shrivardhini N owns formal model and scheduler; Diptesh Das owns deterministic optimisation, routing, baselines, and oracle; Haridasu Sreedhar owns RL/GNN/PPO work.

## Research disclaimer

This is research code. Validate compiled circuits and inspect raw results before drawing conclusions. The deterministic fallback is a correctness/reference implementation, not a claim of superiority over SABRE.


