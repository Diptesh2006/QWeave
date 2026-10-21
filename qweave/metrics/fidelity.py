"""Quantum circuit fidelity and measurement probability distribution metrics.

Includes:
1. Analytical gate-fidelity estimation across all circuit scales without exponential simulation.
2. Statevector quantum state fidelity between source and routed circuits with layout permutation.
3. Measurement outcome probability distribution with physical-to-logical layout mapping.
"""

from __future__ import annotations

import math
from typing import Mapping

import numpy as np
from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector, state_fidelity

from qweave.core.qiskit_adapter import source_operations
from qweave.metrics.hardware_costs import HardwareCostProfile


def _circuit_without_measurements(circuit: QuantumCircuit) -> QuantumCircuit | None:
    """Return a unitary circuit with terminal measurements removed, or None if reset exists."""
    clean = QuantumCircuit(circuit.num_qubits)
    for item in source_operations(circuit):
        name = item.operation.name
        if name == "reset":
            return None
        if name in {"measure", "barrier"}:
            continue
        clean.append(item.operation, list(item.qubits))
    return clean


def estimate_circuit_fidelity(
    circuit: QuantumCircuit,
    profile: HardwareCostProfile | None = None,
) -> dict[str, float | int | str]:
    """Calculate analytical average gate fidelity product across all operations.

    Scales linearly with circuit size (O(N) operations) without statevector simulation.
    Uses the hardware error profile: F_gate = 1 - error_rate.
    """
    profile = profile or HardwareCostProfile()
    log_fidelity = 0.0
    log_2q_fidelity = 0.0
    log_1q_fidelity = 0.0
    log_meas_fidelity = 0.0
    log_swap_fidelity = 0.0

    two_qubit_count = 0
    one_qubit_count = 0
    meas_count = 0
    swap_count = 0

    try:
        ops = source_operations(circuit)
    except Exception:
        return {
            "estimated_circuit_fidelity": 0.0,
            "two_qubit_fidelity": 0.0,
            "one_qubit_fidelity": 0.0,
            "swap_fidelity_impact": 0.0,
            "two_qubit_gates": 0,
            "one_qubit_gates": 0,
            "swaps_count": 0,
            "profile_name": profile.name,
        }

    for item in ops:

        name = item.operation.name
        if name == "measure":
            err = profile.measurement_error
            log_f = math.log1p(-err)
            log_fidelity += log_f
            log_meas_fidelity += log_f
            meas_count += 1
        elif name == "reset":
            err = profile.reset_error
            log_f = math.log1p(-err)
            log_fidelity += log_f
        elif len(item.qubits) == 1:
            err = profile.one_qubit_error
            log_f = math.log1p(-err)
            log_fidelity += log_f
            log_1q_fidelity += log_f
            one_qubit_count += 1
        else:
            left, right = item.qubits
            err = profile.directed_edge_errors.get(
                (left, right),
                profile.directed_edge_errors.get((right, left), profile.two_qubit_error),
            )
            if name == "swap":
                # SWAP is 3 CNOT equivalent
                swap_f = 3 * math.log1p(-err)
                log_fidelity += swap_f
                log_2q_fidelity += swap_f
                log_swap_fidelity += swap_f
                swap_count += 1
                two_qubit_count += 3
            else:
                cnot_f = math.log1p(-err)
                log_fidelity += cnot_f
                log_2q_fidelity += cnot_f
                two_qubit_count += 1

    return {
        "estimated_circuit_fidelity": max(0.0, min(1.0, round(math.exp(log_fidelity), 4))),
        "two_qubit_fidelity": max(0.0, min(1.0, round(math.exp(log_2q_fidelity), 4))),
        "one_qubit_fidelity": max(0.0, min(1.0, round(math.exp(log_1q_fidelity), 4))),
        "swap_fidelity_impact": max(0.0, min(1.0, round(math.exp(log_swap_fidelity), 4))),
        "two_qubit_gates": two_qubit_count,
        "one_qubit_gates": one_qubit_count,
        "swaps_count": swap_count,
        "profile_name": profile.name,
    }


def compute_state_fidelity(
    source: QuantumCircuit,
    routed: QuantumCircuit,
    initial_mapping: Mapping[int, int] | dict[int, int],
    final_mapping: Mapping[int, int] | dict[int, int],
    max_qubits: int = 12,
) -> float | None:
    """Calculate quantum state fidelity F = |<psi_expected|psi_actual>|^2.

    Returns None if:
    - Circuit has more than max_qubits physical qubits.
    - Circuit contains non-unitary operations (resets).
    """
    clean_source = _circuit_without_measurements(source)
    clean_routed = _circuit_without_measurements(routed)
    if clean_source is None or clean_routed is None:
        return None

    num_physical = routed.num_qubits
    num_logical = source.num_qubits
    if num_physical > max_qubits or num_logical > num_physical:
        return None

    try:
        sv_source = Statevector(clean_source)
        sv_routed = Statevector(clean_routed)

        def embed(vector: np.ndarray, mapping: Mapping[int, int] | dict[int, int]) -> np.ndarray:
            output = np.zeros(1 << num_physical, dtype=complex)
            for logical_basis, amplitude in enumerate(vector):
                physical_basis = 0
                for logical_qubit in range(num_logical):
                    if logical_basis & (1 << logical_qubit):
                        physical_basis |= 1 << mapping[logical_qubit]
                output[physical_basis] = amplitude
            return output

        expected_vec = embed(sv_source.data, final_mapping)
        expected_sv = Statevector(expected_vec)
        fidelity = float(state_fidelity(expected_sv, sv_routed))
        return max(0.0, min(1.0, round(fidelity, 6)))
    except Exception:
        return None


def compute_measurement_probabilities(
    circuit: QuantumCircuit,
    mapping: Mapping[int, int] | dict[int, int] | None = None,
    num_logical: int | None = None,
    max_qubits: int = 12,
    top_k: int = 32,
    threshold: float = 1e-4,
) -> dict[str, float] | None:
    """Compute measurement outcome probability distribution over discrete basis states.

    If mapping is provided (mapping[logical] = physical), physical basis states are mapped
    back to the logical qubit register so that source and routed distributions are
    directly comparable on identical basis bitstrings.
    """
    clean = _circuit_without_measurements(circuit)
    if clean is None or clean.num_qubits > max_qubits:
        return None

    try:
        sv = Statevector(clean)
        probs = sv.probabilities()

        if mapping is not None:
            # Physical to logical mapping
            logical_qubits_count = num_logical or len(mapping)
            logical_probs: dict[str, float] = {}
            for p_idx, prob in enumerate(probs):
                if prob < threshold:
                    continue
                l_idx = 0
                for l in range(logical_qubits_count):
                    phys_q = mapping[l]
                    bit = (p_idx >> phys_q) & 1
                    l_idx |= (bit << l)
                l_str = f"{l_idx:0{logical_qubits_count}b}"
                logical_probs[l_str] = logical_probs.get(l_str, 0.0) + float(prob)
            raw_dict = logical_probs
        else:
            # Standard circuit probabilities
            n = circuit.num_qubits
            raw_dict = {}
            for idx, prob in enumerate(probs):
                if prob < threshold:
                    continue
                b_str = f"{idx:0{n}b}"
                raw_dict[b_str] = float(prob)

        # Sort and limit to top_k
        sorted_items = sorted(raw_dict.items(), key=lambda kv: (-kv[1], kv[0]))[:top_k]
        return {k: round(v, 4) for k, v in sorted_items}
    except Exception:
        return None
