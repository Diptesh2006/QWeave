"""Command-line interface for deterministic QWeave compilation."""

import argparse
import json
from pathlib import Path
import sys

import networkx as nx
from qiskit import qasm2, transpile

from qweave.core.compiler import compile_deterministic
from qweave.core.coupling import coupling_graph_from_edges
from qweave.core.qiskit_adapter import source_operations
from qweave.core.types import RoutingResult
from qweave.core.validation import (
    validate_routing_result,
    validate_small_unitary_equivalence,
    validate_statevector_probes,
    validate_two_qubit_legality,
)
from qweave.mapper.initial_mapper import initial_mapping
from qweave.mapper.local_search import refine_mapping
from qweave.baselines.basic import identity_mapping
from qweave.scheduling import schedule_routing_result


def _topology(name: str, logical_qubits: int, physical_qubits: int | None,
              rows: int | None, columns: int | None, edges_file: Path | None) -> nx.Graph:
    count = logical_qubits if physical_qubits is None else physical_qubits
    if count < 1:
        raise ValueError("physical qubit count must be positive")
    if count < logical_qubits:
        raise ValueError("physical qubit count must be at least the circuit width")
    if name == "line":
        return coupling_graph_from_edges([(i, i + 1) for i in range(count - 1)], count)
    if name == "ring":
        edges = [(i, i + 1) for i in range(count - 1)]
        if count > 2:
            edges.append((count - 1, 0))
        return coupling_graph_from_edges(edges, count)
    if name == "grid":
        if rows is None or columns is None or rows < 1 or columns < 1:
            raise ValueError("grid topology requires positive --rows and --columns")
        if rows * columns != count:
            raise ValueError("grid rows * columns must equal the physical qubit count")
        edges = []
        for row in range(rows):
            for column in range(columns):
                node = row * columns + column
                if column + 1 < columns:
                    edges.append((node, node + 1))
                if row + 1 < rows:
                    edges.append((node, node + columns))
        return coupling_graph_from_edges(edges, count)
    if name == "custom":
        if edges_file is None:
            raise ValueError("custom topology requires --edges-file with num_qubits and edges")
        payload = json.loads(edges_file.read_text(encoding="utf-8"))
        count = int(payload["num_qubits"])
        if physical_qubits is not None and physical_qubits != count:
            raise ValueError("--physical-qubits must match num_qubits in the custom edge file")
        graph = coupling_graph_from_edges([tuple(edge) for edge in payload["edges"]], count)
        if set(graph.nodes) != set(range(count)):
            raise ValueError("custom edges must use labels within 0..num_qubits-1")
        return graph
    raise ValueError(f"unknown topology: {name}")


def _compile(args: argparse.Namespace, parser: argparse.ArgumentParser) -> int:
    try:
        circuit = qasm2.load(str(args.circuit))
        graph = _topology(args.topology, circuit.num_qubits, args.physical_qubits,
                          args.rows, args.columns, args.edges_file)
        if args.router == "deterministic":
            result = compile_deterministic(circuit, graph, method=args.method,
                                           schedule=args.schedule)
            routed = result.routed
            mapping = result.initial_mapping
            output_circuit = result.circuit
            semantic = result.semantic_validation
            stage_metrics = result.stage_metrics
        else:
            if args.checkpoint is None:
                raise ValueError("learned router requires --checkpoint")
            if args.seed < 0:
                raise ValueError("seed must be non-negative")
            if args.method == "basic":
                mapping = identity_mapping(circuit, graph)
            else:
                seed_mapping = initial_mapping(circuit, graph)
                mapping = refine_mapping(circuit, seed_mapping.mapping, graph).mapping
            from qweave.learning import QubitRoutingEnv, edge_index_from_env, load_checkpoint

            model, _, _ = load_checkpoint(str(args.checkpoint))
            env = QubitRoutingEnv(circuit, graph, mapping)
            observation, _ = env.reset(seed=args.seed)
            terminated = truncated = False
            while not (terminated or truncated):
                action, _, _ = model.act(observation, edge_index_from_env(env), deterministic=True)
                observation, _, terminated, truncated, _ = env.step(action)
            routed = env.routing_result()
            validate_routing_result(circuit, routed, mapping, graph)
            validate_two_qubit_legality(routed.circuit, graph)
            operations = env.operations
            semantic = None
            if all(item.operation.name not in {"measure", "reset"} for item in operations):
                semantic = validate_small_unitary_equivalence(circuit, routed, mapping)
                if semantic is None:
                    semantic = validate_statevector_probes(circuit, routed, mapping)
            scheduled = (schedule_routing_result(circuit, routed, mapping, graph)
                         if args.schedule else None)
            output_circuit = scheduled.circuit if scheduled else routed.circuit
            stage_metrics = {"symbolic_route_replay": True,
                             "semantic_validation": semantic,
                             "scheduled_depth": scheduled.depth_after if scheduled else None}
        # OpenQASM 2.0's default parser does not include every Qiskit gate such
        # as SWAP. Emit a portable standard basis while preserving edge locality.
        export_circuit = transpile(output_circuit, basis_gates=["u3", "cx"],
                                   optimization_level=0)
        validate_two_qubit_legality(export_circuit, graph)
        if all(item.operation.name not in {"measure", "reset"}
               for item in source_operations(circuit)):
            exported_route = RoutingResult(export_circuit, routed.final_mapping,
                                           routed.trace, routed.swap_count)
            semantic = validate_small_unitary_equivalence(circuit, exported_route, mapping)
            if semantic is None:
                semantic = validate_statevector_probes(circuit, exported_route, mapping)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("x", encoding="utf-8", newline="") as handle:
            qasm2.dump(export_circuit, handle)
    except FileExistsError:
        parser.error(f"refusing to overwrite existing output: {args.output}")
    except (OSError, ImportError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        parser.error(str(exc))
    summary = {
        "output": str(args.output),
        "method": args.method,
        "router": args.router,
        "logical_to_physical": mapping,
        "final_mapping": routed.final_mapping,
        "inserted_swaps": routed.swap_count,
        "depth": export_circuit.depth(),
        "operations": len(export_circuit.data),
        "semantic_validation": semantic,
        "route_replay_validation": stage_metrics["symbolic_route_replay"],
        "fallback_count": getattr(locals().get("env"), "fallback_count", 0),
    }
    print(json.dumps(summary, indent=2))
    return 0


def main(argv: list[str] | None = None) -> int:
    """Run QWeave CLI and return a process-style status code."""

    parser = argparse.ArgumentParser(prog="qweave")
    subparsers = parser.add_subparsers(dest="command", required=True)
    compile_parser = subparsers.add_parser("compile", help="compile a QASM2 circuit")
    compile_parser.add_argument("--circuit", type=Path, required=True)
    compile_parser.add_argument("--topology", choices=("line", "ring", "grid", "custom"), default="line")
    compile_parser.add_argument("--physical-qubits", type=int)
    compile_parser.add_argument("--rows", type=int)
    compile_parser.add_argument("--columns", type=int)
    compile_parser.add_argument("--edges-file", type=Path)
    compile_parser.add_argument("--method", choices=("basic", "weighted"), default="weighted")
    compile_parser.add_argument("--router", choices=("deterministic", "learned"), default="deterministic")
    compile_parser.add_argument("--checkpoint", type=Path)
    compile_parser.add_argument("--seed", type=int, default=7)
    compile_parser.add_argument("--schedule", action="store_true")
    compile_parser.add_argument("--output", type=Path, required=True)
    compile_parser.set_defaults(handler=_compile)
    args = parser.parse_args(argv)
    return args.handler(args, parser)


if __name__ == "__main__":
    sys.exit(main())

