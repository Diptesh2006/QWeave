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

## Section 3: Re-audit of Previously Reported Issues

The following items were recorded during earlier development. They are not current confirmed implementation bugs under the present API; they were rechecked against current validators and tests on 2026-10-12.

1. **Exact unitary validator returns `None` for idle physical sites.**
   - **Current status**: Intentional scope boundary. `validate_small_unitary_equivalence` is defined for equal-width permutations. Idle-site cases use `validate_statevector_probes`, which embeds the logical state into the physical layout. `tests/test_qiskit_adapter_and_route.py::test_statevector_probes_cover_wider_circuit_and_idle_physical_sites` exercises this path.
   - **Remaining limit**: Statevector probes are finite and probabilistic; `None` means the exact oracle is inapplicable, not that equivalence passed.

2. **Exact unitary validator raises `ValueError` for a mismatched unitary.**
   - **Current status**: Intentional fail-closed validation behavior. A semantic mismatch is rejected as an exception rather than returned as a successful boolean. `tests/test_qiskit_adapter_and_route.py::test_sabre_small_layout_oracle_detects_a_changed_output` checks that a modified output is rejected.

3. **`fallback_used` is false on a step that did not invoke fallback, even if fallback occurred earlier.**
   - **Current status**: The field is step-local. The cumulative episode count is `info["fallback_count"]`; the benchmark records this cumulative count. This is an API naming/documentation concern rather than a routing correctness failure. Consumers computing episode totals must use the count.

No other open runtime bug is asserted by this review. The scheduler coverage row in `docs/PROOF_TEST_MATRIX.md` was stale and is now tied to `tests/test_scheduler_verification.py`. The current audit and roadmap record remaining product/research gaps separately from correctness defects.
