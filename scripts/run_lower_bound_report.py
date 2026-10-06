"""Generate lower bound report for the makespan."""

import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import networkx as nx
import qiskit
from qiskit import qasm2

from qweave.baselines.basic import run_basic_baseline
from qweave.mapper.initial_mapper import initial_mapping
from qweave.mapper.local_search import refine_mapping
from qweave.routing.fallback_router import route_with_fallback
from qweave.scheduling import schedule_routing_result
from qweave.scheduling.list_scheduler import makespan_lower_bound, makespan_ratio
from qweave.experiments.smoke import sample_circuits


def run_lower_bound_report(output_dir: str | Path = "results", seed: int = 7) -> Path:
    """Generate makespan vs lower bound report over smoke circuits."""
    
    # We use the smoke circuits here because evaluating the full benchmark-v2 
    # would require heavy reruns and isn't strictly necessary for demonstrating 
    # the lower-bound properties of the list scheduler.
    graph = nx.path_graph(4)
    durations = {"h": 1.0, "cx": 2.0, "swap": 3.0, "x": 1.0}
    
    records = []
    for name, source in sample_circuits().items():
        source_hash = hashlib.sha256(qasm2.dumps(source).encode("utf-8")).hexdigest()
        
        # We will test the basic routing baseline and our fallback router
        basic = run_basic_baseline(source, graph)
        basic_mapping = {logical: logical for logical in range(source.num_qubits)}
        
        first = initial_mapping(source, graph)
        refined = refine_mapping(source, first.mapping, graph)
        weighted = route_with_fallback(source, graph, refined.mapping)
        
        for method, routed, mapping in (
            ("basic", basic, basic_mapping),
            ("weighted", weighted, refined.mapping),
        ):
            scheduled = schedule_routing_result(source, routed, mapping, graph, gate_durations=durations)
            bound = makespan_lower_bound(scheduled.circuit, durations)
            ratio = makespan_ratio(scheduled.makespan, bound)
            
            records.append({
                "circuit_name": name,
                "source_sha256": source_hash,
                "method": method,
                "makespan": scheduled.makespan,
                "lower_bound": bound,
                "ratio": ratio
            })
            
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    revision = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=False)
    dirty = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True, check=False)
    run_id = f"{datetime.now(timezone.utc):%Y%m%dT%H%M%SZ}_{uuid4().hex}"
    path = output / f"lower_bound_report_{run_id}.json"
    
    payload = {
        "scope": "makespan vs lower bounds on three four-qubit smoke circuits (heavy benchmark-v2 rerun bypassed)",
        "schema_version": 1, 
        "seed": seed,
        "git_commit": revision.stdout.strip() if revision.returncode == 0 else None,
        "working_tree_dirty": bool(dirty.stdout.strip()) if dirty.returncode == 0 else None,
        "python_version": sys.version.split()[0], 
        "qiskit_version": qiskit.__version__,
        "gate_durations": durations,
        "records": records
    }
    
    with path.open("x", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)
    return path


if __name__ == "__main__":
    print(run_lower_bound_report())
