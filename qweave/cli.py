"""Command-line interface for deterministic QWeave compilation."""

import argparse
import json
from pathlib import Path
import sys

import networkx as nx
from qiskit import qasm2

from qweave.core.compiler import compile_deterministic
from qweave.core.coupling import coupling_graph_from_edges
from qweave.core.validation import validate_two_qubit_legality


def _topology(name: str, logical_qubits: int, physical_qubits: int | None,
              rows: int | None, columns: int | None, edges_file: Path | None) -> nx.Graph:
    count = physical_qubits or logical_qubits
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
        return coupling_graph_from_edges([tuple(edge) for edge in payload["edges"]], count)
    raise ValueError(f"unknown topology: {name}")


def _compile(args: argparse.Namespace, parser: argparse.ArgumentParser) -> int:
    try:
        circuit = qasm2.load(str(args.circuit))
        graph = _topology(args.topology, circuit.num_qubits, args.physical_qubits,
                          args.rows, args.columns, args.edges_file)
        result = compile_deterministic(circuit, graph, method=args.method,
                                       schedule=args.schedule)
        validate_two_qubit_legality(result.circuit, graph)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("x", encoding="utf-8", newline="") as handle:
            qasm2.dump(result.circuit, handle)
    except FileExistsError:
        parser.error(f"refusing to overwrite existing output: {args.output}")
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        parser.error(str(exc))
    summary = {
        "output": str(args.output),
        "method": result.method,
        "logical_to_physical": result.initial_mapping,
        "final_mapping": result.routed.final_mapping,
        "inserted_swaps": result.routed.swap_count,
        "depth": result.circuit.depth(),
        "operations": len(result.circuit.data),
        "semantic_validation": result.semantic_validation,
        "route_replay_validation": result.stage_metrics["symbolic_route_replay"],
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
    compile_parser.add_argument("--schedule", action="store_true")
    compile_parser.add_argument("--output", type=Path, required=True)
    compile_parser.set_defaults(handler=_compile)
    args = parser.parse_args(argv)
    return args.handler(args, parser)


if __name__ == "__main__":
    sys.exit(main())

