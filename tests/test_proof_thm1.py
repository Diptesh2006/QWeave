"""Tests for Theorem 1: hardware legality of routed and lowered circuits."""
import networkx as nx
from hypothesis import given, settings, strategies as st
from qiskit import QuantumCircuit
from qweave.core.validation import validate_two_qubit_legality
from qweave.metrics.hardware_costs import synthesize_directed_circuit, validate_coupling_legality
from qweave.routing.fallback_router import route_with_fallback

@settings(max_examples=10, deadline=None)
@given(
    width=st.integers(3, 6),
    seed=st.integers(0, 100)
)
def test_thm1_hardware_legality_undirected_and_directed(width, seed):
    """Theorem 1: every routed 2q op lies on an undirected edge; after lowering, on a directed coupler."""
    import numpy as np
    rng = np.random.default_rng(seed)
    
    edges = [(i, i+1) for i in range(width - 1)]
    if width > 3:
        edges.append((2, 1))
        
    directed_graph = nx.DiGraph(edges)
    undirected_graph = directed_graph.to_undirected()
    
    circuit = QuantumCircuit(width)
    for _ in range(5):
        u, v = rng.choice(width, 2, replace=False)
        circuit.cx(int(u), int(v))
        
    mapping = {i: i for i in range(width)}
    routed = route_with_fallback(circuit, undirected_graph, mapping)
    
    validate_two_qubit_legality(routed.circuit, undirected_graph)
    
    lowered = synthesize_directed_circuit(routed.circuit, directed_graph)
    validate_coupling_legality(lowered, directed_graph)
