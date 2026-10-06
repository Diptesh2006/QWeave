# Scheduler Notes: Complexity and Assumptions

## Computational Complexity
The list scheduling algorithm operates directly on the sequence of operations from the routed circuit.
- Building the dependency graph (predecessors and successors) takes $O(N)$ time, where $N$ is the number of operations, because each operation acts on a bounded number of qubits (mostly 1 or 2).
- Computing the critical path ranks takes $O(N)$ time using a reverse topological traversal.
- The greedy list scheduling loop processes each operation exactly once, taking $O(N \log K)$ where $K \le N$ is the maximum width of the ready set (handled via priority queue or min-search). Thus, overall complexity is bounded by $O(N \log N)$.
- This ensures scheduling remains highly scalable even for very deep quantum circuits.

## Algorithmic Assumptions
1. **Fixed Routed Circuit:** The scheduler does not insert new SWAP operations, alter the routing layout, or re-route any operations. The mapping and routing must already be completely legal and fully resolved prior to scheduling.
2. **Per-Wire Precedence:** The scheduler enforces strict order preservation on every physical qubit wire. If operation $B$ follows $A$ on a specific physical qubit in the routed circuit, $B$ will never be scheduled to start before $A$ finishes, and they will never commute or overlap.
3. **ASAP Packing:** The scheduler packs gates as soon as possible (ASAP) based on critical-path priorities. Under the strict per-wire dependency model, the critical path inherently captures all shared-resource delays, meaning the makespan always exactly matches the critical path length (Makespan ratio to lower bound is 1.0).
4. **Positive Durations:** Gate durations must be strictly positive and finite. Zero-duration or negative-duration gates are unsupported, as they violate temporal dependency logic.
