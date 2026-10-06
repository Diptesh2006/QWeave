# QWeave Formal Model

## Definitions

*   **Logical circuit and dependency DAG**: Let $C$ be an ordered circuit on logical qubits $L=\{0,\ldots,n-1\}$. The dependencies can be represented as a directed acyclic graph.
*   **Interaction graph $G_C$**: An undirected graph where nodes are logical qubits and an edge $(i,j)$ has weight $w_{ij}$ equal to its two-qubit interaction count (or with decay weight $\delta^t$).
*   **Hardware graph $G_H$**: An undirected hardware graph $H=(P,E_H)$ used for routing. For the lowering stage, costs are evaluated on declared directed couplers (ordered arcs).
*   **Mapping $\pi: L ightarrow P$**: An initial injective mapping $m: L ightarrow P$ uses the convention $m(	ext{logical}) = 	ext{physical}$, meaning `mapping[logical] = physical`.
*   **Mapping cost**: The static surrogate objective is $J(m) = \sum_{(i,j) \in E_C} w_{ij} \, d_H(m(i), m(j))$, where $d_H$ is shortest-path distance.
*   **SWAP update**: A SWAP between physical sites exchanges the mapping of the assigned logical qubits, updating both the forward and inverse layout.
*   **Frontier / ready set**: The set of operations ready to execute next based on dependency constraints.
*   **Routed circuit**: The physical circuit after SWAP insertion, which must be legally executable on $H$.
*   **Final layout**: The layout of logical to physical qubits at the end of the routed circuit.
*   **Duration function $	au$**: A function assigning a positive duration $d_i$ to operation $i$.
*   **Schedule start times $s(v)$**: Earliest start time for operation $i$: $s_i = \max_{j \in \mathrm{pred}(i)} (s_j + d_j)$.
*   **Makespan**: The completion time of the scheduled circuit. Remaining critical-path rank is $r_i = d_i + \max_{j \in \mathrm{succ}(i)} r_j$.
