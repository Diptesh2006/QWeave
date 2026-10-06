"""Tests for Theorem 2: semantic equivalence under layout permutations."""
import networkx as nx
from hypothesis import given, settings, strategies as st
from qiskit import QuantumCircuit
from qweave.core.validation import validate_small_unitary_equivalence
from qweave.routing.fallback_router import route_with_fallback
import copy

@settings(max_examples=10, deadline=None)
@given(
    width=st.integers(3, 5),
    seed=st.integers(0, 100),
    idle_sites=st.integers(0, 2)
)
def test_thm2_equivalence_up_to_layout_permutations(width, seed, idle_sites):
    """Theorem 2: routed output equals source up to layout permutations on small random circuits (including idle physical sites and source SWAPs); deliberately corrupted layouts are rejected."""
    import numpy as np
    rng = np.random.default_rng(seed)
    
    physical_width = width + idle_sites
    graph = nx.cycle_graph(physical_width)
    
    circuit = QuantumCircuit(width)
    for _ in range(6):
        gate_type = rng.choice(["cx", "swap", "h"])
        if gate_type == "h":
            circuit.h(int(rng.choice(width)))
        elif gate_type == "cx":
            u, v = rng.choice(width, 2, replace=False)
            circuit.cx(int(u), int(v))
        else:
            u, v = rng.choice(width, 2, replace=False)
            circuit.swap(int(u), int(v))
            
    physical_qubits = rng.choice(physical_width, width, replace=False)
    mapping = {logical: int(physical) for logical, physical in enumerate(physical_qubits)}
    
    routed = route_with_fallback(circuit, graph, mapping)
    
    assert validate_small_unitary_equivalence(circuit, routed, mapping, max_qubits=6) is True
    
    if width > 1:
        corrupted = copy.deepcopy(routed)
        k1, k2 = list(corrupted.final_mapping.keys())[:2]
        corrupted.final_mapping[k1], corrupted.final_mapping[k2] = corrupted.final_mapping[k2], corrupted.final_mapping[k1]
        assert validate_small_unitary_equivalence(circuit, corrupted, mapping, max_qubits=6) is False
