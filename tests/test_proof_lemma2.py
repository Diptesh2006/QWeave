"""Tests for Lemma 2: masked softmax constraints."""
import networkx as nx
import numpy as np
import torch
from hypothesis import given, settings, strategies as st
from qiskit import QuantumCircuit
from qweave.learning import GraphActorCritic, QubitRoutingEnv, edge_index_from_env

@settings(max_examples=10, deadline=None)
@given(seed=st.integers(0, 100))
def test_lemma2_masked_softmax_zero_illegal(seed):
    """Lemma 2: real policy module's masked distribution gives exactly 0 to illegal actions and sums to 1."""
    circuit = QuantumCircuit(3)
    circuit.cx(0, 2)
    graph = nx.path_graph(3)
    env = QubitRoutingEnv(circuit, graph, {0: 0, 1: 1, 2: 2})
    observation, _ = env.reset(seed=seed)
    
    model = GraphActorCritic(hidden=16)
    distribution, _ = model.distribution(observation, edge_index_from_env(env))
    
    probs = distribution.probs.detach().numpy()
    mask = observation["action_mask"]
    
    illegal_indices = np.where(mask == 0)[0]
    assert np.all(probs[illegal_indices] == 0.0)
    assert np.isclose(np.sum(probs), 1.0, atol=1e-5)
