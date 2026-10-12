# QWeave Research Method

This document describes the implementation at the audited `main` checkout. It separates implemented mechanisms from the broader critical-path-aware routing hypothesis.

## Problem and representation

Input circuits are Qiskit `QuantumCircuit` objects. The adapter converts instructions into source-indexed operations with logical qubit and classical bit indices. Supported operations are unconditioned one- and two-qubit gates, one-qubit reset, and terminal measurements. Dynamic control flow, conditioned operations, barriers, and operations on three or more qubits are rejected.

Hardware connectivity for mapping and routing is an undirected simple NetworkX graph with non-negative contiguous physical labels for the learning environment. Directed target legality is represented separately and applied in the cost-lowering stage. Mapping is always `mapping[logical] = physical`.

## Deterministic mapping and routing

The interaction graph has one node per logical qubit. Each two-qubit operation increments the undirected edge weight; optional positional decay contributes `decay ** instruction_index`.

The initial mapper orders hardware sites by closeness centrality, then degree and stable node label. It places the highest weighted-degree logical qubit first. Each remaining logical qubit is selected by interaction weight to already placed qubits, then weighted degree and index. Its physical site minimizes weighted shortest-path distance to mapped interaction partners. Tie breaks are deterministic.

The refinement objective is

`J(m) = sum_(i,j) w(i,j) * d_H(m(i), m(j))`.

The local search tries all pairs of mapped logical qubits, chooses the best strict decrease with logical-pair tie breaking, and stops at a local minimum or iteration cap. Its termination follows from strict descent over a finite set of injective assignments.

The deterministic router processes the validated source operation order. For a nonadjacent two-qubit interaction it inserts edge-local SWAPs along a deterministic shortest path, updates forward and inverse layouts, then emits the source operation. Its trace is replayed against source operations and final layout. This is a sequential correctness-first router, not a global depth optimizer.

## Scheduling and hardware costs

The list scheduler is applied after a route is fixed. It builds per-physical-wire dependencies, prioritizes ready operations by remaining duration-weighted critical path, and schedules at earliest legal resource-ready times. Optional gate durations produce makespan estimates. Unit-duration depth is normally equal to Qiskit's preexisting dependency depth.

For directed cost evaluation, reverse CNOTs are synthesized with Hadamard conjugation and SWAPs are decomposed to three CNOTs before ordered-coupler checks and proxy-cost calculation. Duration and error profiles are declared synthetic values unless an explicitly calibrated profile is supplied; the published v2 profile is not device calibration.

## Learned path as implemented

The Gymnasium environment exposes `EXECUTE` and one SWAP action per hardware edge. A binary mask removes invalid actions from the PPO categorical distribution. The environment processes a source-operation pointer with a finite lookahead potential; it does not expose a general dependency-DAG ready frontier or dynamically schedule independent source gates in parallel.

`GraphActorCritic` is a small custom PyTorch message-passing actor-critic. PPO uses a clipped policy objective, generalized advantage estimates, value and entropy terms, gradient clipping, and explicit seeds. The environment invokes the deterministic fallback after bounded non-progress or episode limits and validates the completed route.

This implemented reward and state do not yet establish a distinct critical-path-aware routing formulation. The current benchmark-v2 results show no paired median depth improvement over weighted deterministic routing. SABRE-guided behavioral cloning and expert trajectory extraction are not implemented.

## Exact reference and baselines

The CP-SAT model minimizes the same weighted shortest-path initial-mapping objective and is capped at eight logical qubits. It returns solver status, objective, runtime, and gap/bound information. It is not an exact route optimizer.

Comparisons include identity mapping plus deterministic routing, weighted mapping plus local search and deterministic routing, Qiskit SABRE, learned GNN-PPO, no-message PPO, and untrained GNN controls. The benchmark protocols pin cases, splits, seeds, and stage-specific metrics.

## Validation

The route replay checks source gate order and parameters, physical/classical targets, SWAP edges and mapping updates, final mapping, width, global phase, and hardware legality. Equal-width unitary circuits up to six qubits receive an exact layout-aware operator comparison. Wider and idle-site circuits up to twelve physical qubits can receive deterministic statevector probes. Probes are finite tests rather than a proof for every input state. Reset and terminal-measurement circuits are structurally replayed; dynamic control is rejected.

## Evaluation protocol and limitations

Benchmark v2 freezes 180 generated cases, with 36 held-out test cases from held-out circuit families and topologies. It compares deterministic methods, SABRE, GNN-PPO, no-message PPO, and an untrained graph policy. Seeds are collapsed per case before paired analysis; the report includes family summaries, bootstrap intervals, runtime distributions, fallbacks, and counterexamples.

The study is synthetic and finite. It reports equal paired median depth for GNN-PPO and weighted deterministic routing, and equal paired median depth between GNN-PPO and no-message PPO. It therefore does not establish a learned routing advantage, a message-passing contribution, calibrated hardware fidelity, optimal routing, or state-of-the-art performance. A DAG/frontier environment, a specified critical-path reward ablation, broader external circuits, and optional SABRE imitation remain future work.

