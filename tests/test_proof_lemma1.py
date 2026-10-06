"""Tests for Lemma 1: SWAP sequences preserve mapping injectivity."""
import networkx as nx
from hypothesis import given, settings, strategies as st
from qiskit import QuantumCircuit
from qweave.core.validation import validate_mapping
from qweave.routing.fallback_router import route_with_fallback

@settings(max_examples=15, deadline=None)
@given(
    graph_type=st.sampled_from(["path", "cycle", "grid"]),
    num_nodes=st.integers(4, 8),
    seed=st.integers(0, 100)
)
def test_lemma1_swaps_preserve_injectivity(graph_type, num_nodes, seed):
    """Lemma 1: random legal SWAP sequences on path/grid/ring keep injectivity."""
    import numpy as np
    if graph_type == "path":
        graph = nx.path_graph(num_nodes)
    elif graph_type == "cycle":
        graph = nx.cycle_graph(num_nodes)
    elif graph_type == "grid":
        side = int(np.ceil(np.sqrt(num_nodes)))
        graph = nx.convert_node_labels_to_integers(nx.grid_2d_graph(side, side))
        graph.remove_nodes_from(list(graph.nodes)[num_nodes:])
        if not nx.is_connected(graph):
            return

    mapping = {i: i for i in range(num_nodes)}
    circuit = QuantumCircuit(num_nodes)
    rng = np.random.default_rng(seed)
    
    # Random circuit to force SWAPs in the router
    for _ in range(5):
        u, v = rng.choice(num_nodes, 2, replace=False)
        circuit.cx(int(u), int(v))
        
    routed = route_with_fallback(circuit, graph, mapping)
    validate_mapping(routed.final_mapping, num_nodes, graph)
    assert len(set(routed.final_mapping.values())) == num_nodes
