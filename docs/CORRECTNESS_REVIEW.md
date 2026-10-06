# QWeave Correctness Review

## Section 1: Architecture vs. Implementation Discrepancies

This section documents where the initial conceptual architecture blueprint diverged from the actual implemented Python codebase, and how each discrepancy was formally resolved in `paper/theory.tex`.

1. **Direction handled in EXECUTE guard vs. separate lowering stage**
   - **Blueprint**: The router's execution step directly evaluates directed physical edges and accounts for reverse-CNOT costs dynamically.
   - **Code**: `QubitRoutingEnv` routes over purely undirected edges. The directed synthesis (and associated reverse-CNOT/directed-SWAP overhead) occurs exclusively during a standalone post-routing lowering pass (`qweave.metrics.hardware_costs`).
   - **Theory Resolution**: **Theorem 1** formalizes this decoupling, proving undirected legality immediately post-routing, and directed legality exclusively post-lowering.

2. **Scheduler interleaved with routing vs. post-routing**
   - **Blueprint**: Operation scheduling (timing allocation) interleaves with routing emissions.
   - **Code**: Scheduling is a strict post-routing pass (`qweave.scheduling.list_scheduler.schedule_routed_circuit`).
   - **Theory Resolution**: **Theorem 3** models the scheduler as operating strictly on a *fixed routed circuit*, generating valid packings through a post-hoc static dependency graph.

3. **Lemma 5 stated as a global optimum vs. fixed circuit**
   - **Blueprint**: The makespan lower bound is framed as a global minimum for the given routing problem.
   - **Code**: `makespan_lower_bound` explicitly calculates the bound solely for the provided static operation sequence.
   - **Theory Resolution**: **Lemma 5** restricts its claim entirely to *fixed routed circuits*, making no assertions of optimality across alternative valid routings.

4. **Classical conditions "preserved" vs. rejected by the adapter**
   - **Blueprint**: Classical mid-circuit conditions and dynamic execution flows are preserved and routed.
   - **Code**: `qiskit_to_source_operations` strictly rejects active dynamic control flow and conditioned gates.
   - **Theory Resolution**: The supported gate family assumption (**Assumption A6**) restricts compilation to unconditioned 1q/2q unitaries, resets, and terminal measurements.

5. **Equivalence convention $U_{out} = P_{\pi_T} U_C P_{\pi_0}^\dagger$ vs. $U_{routed} P_{initial} = P_{final} U_C$**
   - **Blueprint**: Relies on conjugate transpose initial layouts.
   - **Code**: Evaluates equivalence directly matching QWeave's `mapping[logical] = physical` array tracking convention.
   - **Theory Resolution**: **Theorem 2** asserts semantic equivalence utilizing exactly the implemented convention: $U_{\mathrm{routed}} P_{\mathrm{initial}} = P_{\mathrm{final}} U_C$.

## Section 2: Proof Assumption Audit

For every assumption in `docs/ASSUMPTION_REGISTER.md`, the following table confirms code enforcement, testing presence, and formal theorem linkage.

| ID | Statement Summary | Enforced in Code? | Property/Unit Tested? | Cited by Theorem? |
|----|-------------------|-------------------|-----------------------|-------------------|
| A1 | Injective Mapping | Yes (`validate_mapping`) | Yes | Lemma 1, Theorem 2 |
| A2 | Mapping Convention | Yes (`initial_mapping`) | Yes | Theorem 2 |
| A3 | Connected Usable Component | Yes (`QubitRoutingEnv`) | Yes | Theorem 4 |
| A4 | Contiguous Labels | Yes (`QubitRoutingEnv`) | Yes | Implicit (Thm 1, 4) |
| A5 | Undirected routing then separate lowering | Yes (`validate_two_qubit_legality`) | Yes | Theorem 1 |
| A6 | Supported Gate Family | Yes (`qiskit_adapter.py`) | Yes | Theorem 2 |
| A7 | Positive Durations | Yes (`list_scheduler.py`) | Yes | Lemma 5 |
| A8 | Global Phase Preserved | Yes (`validate_routing_result`) | Yes | Theorem 3 (indirect) |
| A9 | Explicit Seeds | Yes (GNN/PPO init) | Yes | Experimental Design |
| A10 | Exact check $\le 6$, probes $\le 12$ | Yes (`validate_small_unitary_equivalence`) | Yes | Theorem 2 |

## Section 3: Open Issues and Suspected Bugs

The following behavioral oddities and bugs were uncovered during Stage 3 property testing. Module owners are assigned below to investigate.

1. **Bug: `validate_small_unitary_equivalence` returns `None` for idle sites.**
   - **Detail**: When evaluated on a circuit mapping with idle physical sites (physical width > logical width), the exact unitary validator bails out and silently returns `None`, forcing tests to explicitly fall back to `validate_statevector_probes`.
   - **Owner**: Atharva (Integration / Qiskit Interfaces)

2. **Bug: `validate_small_unitary_equivalence` raises bare `ValueError` instead of returning `False`.**
   - **Detail**: Passing a corrupted layout to the validator causes it to raise `ValueError("routed unitary disagrees with initial/final layouts")` instead of gracefully returning a `False` boolean to the caller.
   - **Owner**: Atharva (Integration / Qiskit Interfaces)

3. **Bug: Terminal-step transient `fallback_used` indicator is misleading.**
   - **Detail**: `QubitRoutingEnv.step()` drops the `fallback_used = True` flag on the final episode step if the step naturally concludes without hitting the non-progress limit. Consumers must read `info["fallback_count"] > 0` to accurately detect if fallback occurred during the episode.
   - **Owner**: Haridasu (RL Environment / GNN)
