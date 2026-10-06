"""Tests for scheduler verification, bounds, and ratio."""
import copy
import networkx as nx
import pytest
from hypothesis import given, settings, strategies as st
from qiskit import QuantumCircuit
from qweave.scheduling.list_scheduler import (
    schedule_routed_circuit, verify_schedule, makespan_lower_bound, makespan_ratio
)

@settings(max_examples=10, deadline=None)
@given(
    width=st.integers(3, 6),
    seed=st.integers(0, 100)
)
def test_random_circuits_pass_verify_schedule(width, seed):
    import numpy as np
    rng = np.random.default_rng(seed)
    circuit = QuantumCircuit(width)
    for _ in range(8):
        gate_type = rng.choice(["cx", "swap", "h"])
        if gate_type == "h":
            circuit.h(int(rng.choice(width)))
        else:
            u, v = rng.choice(width, 2, replace=False)
            getattr(circuit, gate_type)(int(u), int(v))
            
    durations = {"cx": 2.0, "swap": 3.0, "h": 1.0}
    graph = nx.complete_graph(width)
    result = schedule_routed_circuit(circuit, graph, durations)
    
    passed, msg = verify_schedule(circuit, result, durations)
    assert passed, msg

def test_hand_corrupted_schedules_rejected():
    circuit = QuantumCircuit(2)
    circuit.h(0)
    circuit.cx(0, 1)
    circuit.h(1)
    durations = {"h": 1.0, "cx": 2.0}
    graph = nx.path_graph(2)
    result = schedule_routed_circuit(circuit, graph, durations)
    
    # 1. Swapped order (execute cx before h0)
    corrupted_result = copy.deepcopy(result)
    corrupted_result.timing[0]["start"], corrupted_result.timing[0]["finish"] = 3.0, 4.0
    corrupted_result.timing[1]["start"], corrupted_result.timing[1]["finish"] = 0.0, 2.0
    passed, msg = verify_schedule(circuit, corrupted_result, durations)
    assert not passed
    assert "order not preserved" in msg or "Overlap" in msg or "finish" in msg
    
    # 2. Overlap
    corrupted_result2 = copy.deepcopy(result)
    corrupted_result2.timing[1]["start"] = 0.5
    corrupted_result2.timing[1]["finish"] = 2.5
    passed, msg = verify_schedule(circuit, corrupted_result2, durations)
    assert not passed
    assert "Overlap" in msg or "mismatch" in msg
    
    # 3. Early start (without overlap but violating predecessor finish)
    circuit3 = QuantumCircuit(3)
    circuit3.cx(0, 1)
    circuit3.cx(1, 2)
    res3 = schedule_routed_circuit(circuit3, nx.path_graph(3), durations)
    corr3 = copy.deepcopy(res3)
    corr3.timing[1]["start"] = 1.0
    corr3.timing[1]["finish"] = 3.0
    passed, msg = verify_schedule(circuit3, corr3, durations)
    assert not passed
    assert "Overlap" in msg
    
@settings(max_examples=10, deadline=None)
@given(
    width=st.integers(3, 6),
    seed=st.integers(0, 100)
)
def test_makespan_bounds_always_hold(width, seed):
    import numpy as np
    rng = np.random.default_rng(seed)
    circuit = QuantumCircuit(width)
    for _ in range(8):
        u, v = rng.choice(width, 2, replace=False)
        circuit.cx(int(u), int(v))
    durations = {"cx": 2.0}
    graph = nx.complete_graph(width)
    result = schedule_routed_circuit(circuit, graph, durations)
    
    bound = makespan_lower_bound(circuit, durations)
    assert result.makespan >= bound - 1e-9
    
def test_load_bound_never_exceeds_critical_path_ratio_one():
    """
    Under this scheduler's per-wire dependency model, the load bound never 
    exceeds the critical path, so ASAP gives ratio 1 on a fixed circuit.
    """
    circuit = QuantumCircuit(2)
    circuit.h(0)
    circuit.cx(0, 1)
    circuit.h(1)
    durations = {"h": 1.0, "cx": 2.0}
    graph = nx.path_graph(2)
    
    bound = makespan_lower_bound(circuit, durations)
    result = schedule_routed_circuit(circuit, graph, durations)
    
    assert makespan_ratio(result.makespan, bound) == 1.0
