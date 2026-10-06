"""Tests for Theorem 4: fallback termination on connected graphs."""
import networkx as nx
from hypothesis import given, settings, strategies as st
from qiskit import QuantumCircuit
from qweave.learning import QubitRoutingEnv

@settings(max_examples=10, deadline=None)
@given(
    width=st.integers(3, 7),
    seed=st.integers(0, 100)
)
def test_thm4_fallback_completes_on_random_connected_graphs(width, seed):
    """Theorem 4: fallback completes on random connected graphs."""
    import numpy as np
    rng = np.random.default_rng(seed)
    
    graph = nx.barabasi_albert_graph(width, 1, seed=seed)
    
    circuit = QuantumCircuit(width)
    for _ in range(5):
        u, v = rng.choice(width, 2, replace=False)
        circuit.cx(int(u), int(v))
        
    mapping = {i: i for i in range(width)}
    
    env = QubitRoutingEnv(circuit, graph, mapping, max_nonprogress=2)
    env.reset(seed=seed)
    
    terminated = False
    truncated = False
    while not (terminated or truncated):
        _, _, terminated, truncated, info = env.step(0)
        
    assert terminated
    assert info.get("fallback_used", False)
