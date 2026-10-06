# Equivalence Strategy

This document describes QWeave's strategy for validating the semantic equivalence of routed circuits.

*   **Exact Unitary Check ($\le 6$ qubits)**: For small, equal-width quantum circuits up to 6 qubits without mid-circuit measurements or resets, the compiler builds exact unitary permutations. It directly asserts {\mathrm{routed}} P_{\mathrm{initial}} = P_{\mathrm{final}} U_C$ up to a very small tolerance.
*   **Statevector Probes ($\le 12$ qubits)**: For wider circuits (up to 12 qubits) or circuits on hardware with idle physical sites, QWeave uses reproducible deterministic statevector probes to verify correctness numerically without needing full unitary matrices.
*   **Structural Replay**: For circuits containing resets and terminal measurements, numerical simulation is bypassed in favor of structural replay validation, verifying correct order and target propagation.
*   **Not Covered**: Dynamic control flow, classically conditioned gates, and active mid-circuit measurement branching are unsupported and not covered by these equivalence checks.
