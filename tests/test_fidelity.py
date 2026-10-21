"""Unit tests for circuit fidelity and measurement probability distribution metrics."""

import math
import pytest
from qiskit import QuantumCircuit
import networkx as nx

from qweave.core.compiler import compile_deterministic
from qweave.metrics import (
    compute_measurement_probabilities,
    compute_state_fidelity,
    estimate_circuit_fidelity,
    HardwareCostProfile,
)


def test_analytical_circuit_fidelity_components():
    profile = HardwareCostProfile(one_qubit_error=0.01, two_qubit_error=0.05)
    qc = QuantumCircuit(2)
    qc.h(0)
    qc.x(1)
    qc.cx(0, 1)

    result = estimate_circuit_fidelity(qc, profile=profile)
    assert result["one_qubit_gates"] == 2
    assert result["two_qubit_gates"] == 1
    assert result["swaps_count"] == 0

    expected_1q = (1 - 0.01) ** 2
    expected_2q = 1 - 0.05
    expected_total = expected_1q * expected_2q

    assert math.isclose(result["one_qubit_fidelity"], expected_1q, rel_tol=1e-3)
    assert math.isclose(result["two_qubit_fidelity"], expected_2q, rel_tol=1e-3)
    assert math.isclose(result["estimated_circuit_fidelity"], expected_total, rel_tol=1e-3)


def test_analytical_swap_fidelity_penalty():
    profile = HardwareCostProfile(two_qubit_error=0.02)
    qc = QuantumCircuit(2)
    qc.swap(0, 1)

    result = estimate_circuit_fidelity(qc, profile=profile)
    assert result["swaps_count"] == 1
    assert result["two_qubit_gates"] == 3  # SWAP = 3 CNOT equivalent
    expected_swap_f = (1 - 0.02) ** 3
    assert math.isclose(result["swap_fidelity_impact"], expected_swap_f, rel_tol=1e-3)


def test_state_fidelity_on_compiled_bell_circuit():
    # Source Bell state: 2 qubits
    source = QuantumCircuit(2)
    source.h(0)
    source.cx(0, 1)

    # 3-qubit line graph: 0 - 1 - 2
    coupling = nx.path_graph(3)
    compiled = compile_deterministic(source, coupling, method="weighted")

    # State fidelity should be 1.0 (ideal unitary equivalence)
    fidelity = compute_state_fidelity(
        source,
        compiled.routed.circuit,
        compiled.initial_mapping,
        compiled.routed.final_mapping,
    )
    assert fidelity is not None
    assert fidelity >= 0.999999


def test_state_fidelity_drops_on_corrupted_layout():
    source = QuantumCircuit(2)
    source.h(0)
    source.cx(0, 1)

    coupling = nx.path_graph(3)
    compiled = compile_deterministic(source, coupling, method="weighted")

    # Deliberately corrupt final mapping
    corrupted_final = dict(compiled.routed.final_mapping)
    keys = list(corrupted_final.keys())
    if len(keys) >= 2:
        corrupted_final[keys[0]], corrupted_final[keys[1]] = (
            corrupted_final[keys[1]],
            corrupted_final[keys[0]],
        )

    fidelity = compute_state_fidelity(
        source,
        compiled.routed.circuit,
        compiled.initial_mapping,
        corrupted_final,
    )
    # Bell state is symmetric under swap of logical qubits, so let's test asymmetric state
    asym_source = QuantumCircuit(2)
    asym_source.x(0)  # state |01>

    asym_compiled = compile_deterministic(asym_source, coupling, method="weighted")
    inverted_final = {0: asym_compiled.routed.final_mapping[1], 1: asym_compiled.routed.final_mapping[0]}
    bad_fidelity = compute_state_fidelity(
        asym_source,
        asym_compiled.routed.circuit,
        asym_compiled.initial_mapping,
        inverted_final,
    )
    assert bad_fidelity is not None
    assert bad_fidelity < 0.001


def test_measurement_probabilities_layout_mapping():
    # Source GHZ state on 3 qubits
    source = QuantumCircuit(3)
    source.h(0)
    source.cx(0, 1)
    source.cx(1, 2)

    source_probs = compute_measurement_probabilities(source)
    assert source_probs is not None
    assert "000" in source_probs
    assert "111" in source_probs
    assert math.isclose(source_probs["000"], 0.5, abs_tol=1e-2)
    assert math.isclose(source_probs["111"], 0.5, abs_tol=1e-2)

    # Compile onto 4-qubit line
    coupling = nx.path_graph(4)
    compiled = compile_deterministic(source, coupling, method="weighted")

    routed_probs = compute_measurement_probabilities(
        compiled.routed.circuit,
        mapping=compiled.routed.final_mapping,
        num_logical=3,
    )
    assert routed_probs is not None
    assert "000" in routed_probs
    assert "111" in routed_probs
    assert math.isclose(routed_probs["000"], 0.5, abs_tol=1e-2)
    assert math.isclose(routed_probs["111"], 0.5, abs_tol=1e-2)


def test_fidelity_qubit_bound_safeguard():
    # Large circuit exceeding max_qubits
    big_qc = QuantumCircuit(15)
    result = compute_state_fidelity(big_qc, big_qc, {}, {}, max_qubits=12)
    assert result is None

    probs = compute_measurement_probabilities(big_qc, max_qubits=12)
    assert probs is None

    # Analytical fidelity should still compute in milliseconds for 15+ qubits!
    analytical = estimate_circuit_fidelity(big_qc)
    assert analytical["estimated_circuit_fidelity"] == 1.0


def test_state_fidelity_rejects_resets():
    qc_reset = QuantumCircuit(2)
    qc_reset.reset(0)
    result = compute_state_fidelity(qc_reset, qc_reset, {0: 0, 1: 1}, {0: 0, 1: 1})
    assert result is None
