"""Tests for Proposition 1: local search termination and strict descent."""
import networkx as nx
from hypothesis import given, settings, strategies as st
from qiskit import QuantumCircuit
from qweave.mapper.local_search import refine_mapping

@settings(max_examples=15, deadline=None)
@given(
    width=st.integers(3, 8),
    seed=st.integers(0, 100)
)
def test_prop1_local_search_strict_descent_and_termination(width, seed):
    """Proposition 1: objective strictly decreases at every accepted move; terminates."""
    import numpy as np
    circuit = QuantumCircuit(width)
    rng = np.random.default_rng(seed)
    
    for _ in range(10):
        u, v = rng.choice(width, 2, replace=False)
        circuit.cx(int(u), int(v))
        
    graph = nx.path_graph(width)
    initial_mapping = {i: i for i in range(width)}
    
    result = refine_mapping(circuit, initial_mapping, graph)
    
    for move in result.accepted_moves:
        assert move["objective_after"] < move["objective_before"]
        
    if result.accepted_moves:
        assert result.final_objective < result.initial_objective
    else:
        assert result.final_objective == result.initial_objective
