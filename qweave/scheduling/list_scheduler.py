"""Critical-path list scheduling after mapping and routing are fixed."""

from dataclasses import dataclass
import math

import networkx as nx
from qiskit import QuantumCircuit

from qweave.core.qiskit_adapter import physical_output_circuit, source_operations, validate_hardware_graph
from qweave.core.types import Mapping, RoutingResult
from qweave.core.validation import validate_routing_result, validate_two_qubit_legality


@dataclass
class ScheduleResult:
    circuit: QuantumCircuit
    timing: list[dict]
    layers: list[list[int]]
    makespan: float
    depth_before: int
    depth_after: int
    depth_delta: int


def verify_schedule(circuit: QuantumCircuit, schedule: ScheduleResult, durations: dict[str, float] | None = None) -> tuple[bool, str | None]:
    """Verify independent schedule properties."""
    durations = durations or {}
    source_ops = source_operations(circuit)
    sched_ops = source_operations(schedule.circuit)
    
    if circuit.global_phase != schedule.circuit.global_phase:
        return False, "Global phase changed"
        
    def op_tuple(item):
        return (item.operation.name, tuple(item.qubits), tuple(item.clbits))
        
    if sorted(map(op_tuple, source_ops)) != sorted(map(op_tuple, sched_ops)):
        return False, "Operation multiset changed"
        
    timing = sorted(schedule.timing, key=lambda x: x["start"])
    if sorted([t["gate_index"] for t in timing]) != list(range(len(source_ops))):
        return False, "Schedule timing does not cover exactly all source gates"
        
    # Check durations and overlaps
    qubit_events = {q: [] for q in range(circuit.num_qubits)}
    for t in timing:
        idx = t["gate_index"]
        op = source_ops[idx]
        expected_dur = float(durations.get(op.operation.name, 1.0))
        if not math.isclose(t["finish"] - t["start"], expected_dur, abs_tol=1e-9):
            return False, f"Gate {idx} duration mismatch"
        for q in op.qubits:
            qubit_events[q].append(t)
            
    # Check overlap and order
    for q, events in qubit_events.items():
        # sorted by start time
        for i in range(len(events) - 1):
            if events[i]["finish"] > events[i+1]["start"] + 1e-9:
                return False, f"Overlap on qubit {q} between gate {events[i]['gate_index']} and {events[i+1]['gate_index']}"
                
    # Check source order preserved
    source_qubit_order = {q: [] for q in range(circuit.num_qubits)}
    for i, op in enumerate(source_ops):
        for q in op.qubits:
            source_qubit_order[q].append(i)
            
    for q, events in qubit_events.items():
        sched_order = [e["gate_index"] for e in events]
        if sched_order != source_qubit_order[q]:
            return False, f"Gate order not preserved on qubit {q}"
            
    # Check predecessors
    # Predecessor finish <= Start is guaranteed by overlap check + order check
    
    return True, None


def makespan_lower_bound(circuit: QuantumCircuit, durations: dict[str, float] | None = None) -> float:
    durations = durations or {}
    ops = source_operations(circuit)
    
    # 1. Critical path
    finish_times = [0.0] * circuit.num_qubits
    for op in ops:
        dur = float(durations.get(op.operation.name, 1.0))
        start = max((finish_times[q] for q in op.qubits), default=0.0)
        for q in op.qubits:
            finish_times[q] = start + dur
    critical_path = max(finish_times, default=0.0)
    
    # 2. Max per-qubit sum
    per_qubit_sum = [0.0] * circuit.num_qubits
    for op in ops:
        dur = float(durations.get(op.operation.name, 1.0))
        for q in op.qubits:
            per_qubit_sum[q] += dur
    max_load = max(per_qubit_sum, default=0.0)
    
    return max(critical_path, max_load)

def makespan_ratio(makespan: float, bound: float) -> float:
    return makespan / bound if bound > 0 else 1.0


def schedule_routed_circuit(circuit: QuantumCircuit, coupling_graph: nx.Graph,
                            gate_durations: dict[str, float] | None = None) -> ScheduleResult:
    """Pack legal gates at earliest resource-ready times.

    Dependency edges preserve every physical wire's operation order. The
    priority is remaining weighted critical-path length; ties use source
    order. No gate is removed, commuted across a shared wire, or rerouted.
    With unit durations, Qiskit's existing circuit depth usually already
    equals this dependency depth, so a zero depth delta is expected.
    """

    operations = source_operations(circuit)
    validate_hardware_graph(coupling_graph, circuit.num_qubits)
    validate_two_qubit_legality(circuit, coupling_graph)
    durations = dict(gate_durations or {})
    if any(not isinstance(value, (int, float)) or isinstance(value, bool)
           or not math.isfinite(value) or value <= 0 for value in durations.values()):
        raise ValueError("gate durations must be finite positive numbers")
    weights = [float(durations.get(item.operation.name, 1.0)) for item in operations]
    count = len(operations)
    predecessors: list[set[int]] = [set() for _ in operations]
    successors: list[set[int]] = [set() for _ in operations]
    last_on_wire: dict[int, int] = {}
    for index, item in enumerate(operations):
        for qubit in item.qubits:
            previous = last_on_wire.get(qubit)
            if previous is not None:
                predecessors[index].add(previous)
                successors[previous].add(index)
            last_on_wire[qubit] = index
    ranks = [0.0] * count
    for index in range(count - 1, -1, -1):
        ranks[index] = weights[index] + max((ranks[next_gate] for next_gate in successors[index]), default=0.0)
    ready = {index for index in range(count) if not predecessors[index]}
    scheduled: set[int] = set()
    start_times = [0.0] * count
    finish_times = [0.0] * count
    while ready:
        index = min(ready, key=lambda item: (-ranks[item], item))
        ready.remove(index)
        start_times[index] = max((finish_times[previous] for previous in predecessors[index]), default=0.0)
        finish_times[index] = start_times[index] + weights[index]
        scheduled.add(index)
        for next_gate in successors[index]:
            if predecessors[next_gate] <= scheduled:
                ready.add(next_gate)
    if len(scheduled) != count:
        raise RuntimeError("gate dependency graph contains a cycle")
    order = sorted(range(count), key=lambda index: (start_times[index], -ranks[index], index))
    output = physical_output_circuit(circuit, circuit.num_qubits)
    for index in order:
        item = operations[index]
        output.append(item.operation, list(item.qubits),
                      [output.clbits[clbit] for clbit in item.clbits])
    validate_two_qubit_legality(output, coupling_graph)
    # Positive durations guarantee that shared-wire predecessors start first.
    if any(start_times[previous] >= start_times[index]
           for index in range(count) for previous in predecessors[index]):
        raise RuntimeError("scheduler reversed a physical-wire dependency")
    layers_by_start: dict[float, list[int]] = {}
    for index in order:
        layers_by_start.setdefault(start_times[index], []).append(index)
    timing = [{"gate_index": index, "operation": operations[index].operation.name,
               "physical_qubits": list(operations[index].qubits),
               "start": start_times[index], "finish": finish_times[index],
               "critical_path": ranks[index]} for index in order]
    before, after = circuit.depth(), output.depth()
    return ScheduleResult(output, timing, list(layers_by_start.values()),
                          max(finish_times, default=0.0), before, after, after - before)


def schedule_routing_result(source: QuantumCircuit, routed: RoutingResult,
                            initial_mapping: Mapping, coupling_graph: nx.Graph,
                            gate_durations: dict[str, float] | None = None) -> ScheduleResult:
    """Check a fixed route before measuring only the scheduling stage."""

    validate_routing_result(source, routed, initial_mapping, coupling_graph)
    return schedule_routed_circuit(routed.circuit, coupling_graph, gate_durations)
