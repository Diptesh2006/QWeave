"""Tests for Theorem 4: fallback termination on connected graphs."""
import networkx as nx
from hypothesis import given, settings, strategies as st
from qiskit import QuantumCircuit
from qweave.learning import QubitRoutingEnv
from qweave.core.validation import validate_routing_result

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
    
    # Guarantee at least one non-adjacent gate so fallback MUST fire
    u, v = 0, 1
    for a in range(width):
        for b in range(a + 1, width):
            if not graph.has_edge(a, b):
                u, v = a, b
                break
    circuit.cx(u, v)
    
    for _ in range(5):
        a, b = rng.choice(width, 2, replace=False)
        circuit.cx(int(a), int(b))
        
    mapping = {i: i for i in range(width)}
    
    env = QubitRoutingEnv(circuit, graph, mapping, max_nonprogress=2)
    env.reset(seed=seed)
    
    terminated = False
    truncated = False
    while not (terminated or truncated):
        _, _, terminated, truncated, info = env.step(0)
        
    assert terminated
    assert info["fallback_count"] > 0
    validate_routing_result(circuit, env.routing_result(), mapping, graph)
