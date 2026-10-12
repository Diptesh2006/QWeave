import json

import pytest
from qiskit import QuantumCircuit, qasm2

from qweave.cli import _topology, main
from qweave.learning import GraphActorCritic, PPOConfig, save_checkpoint


def _write_qasm(path):
    circuit = QuantumCircuit(3)
    circuit.h(0)
    circuit.cx(0, 2)
    qasm2.dump(circuit, str(path))


def test_module_cli_compiles_and_writes_valid_qasm(tmp_path, capsys):
    source = tmp_path / "source.qasm"
    output = tmp_path / "compiled.qasm"
    _write_qasm(source)

    status = main(["compile", "--circuit", str(source), "--topology", "line",
                   "--method", "weighted", "--schedule", "--output", str(output)])

    summary = json.loads(capsys.readouterr().out)
    compiled = qasm2.load(str(output))
    assert status == 0
    assert compiled.num_qubits == 3
    assert summary["route_replay_validation"] is True
    assert summary["semantic_validation"] is True
    assert summary["output"] == str(output)


def test_cli_refuses_to_overwrite_compiled_output(tmp_path):
    source = tmp_path / "source.qasm"
    output = tmp_path / "compiled.qasm"
    _write_qasm(source)
    output.write_text("preserve", encoding="utf-8")

    with pytest.raises(SystemExit) as error:
        main(["compile", "--circuit", str(source), "--output", str(output)])

    assert error.value.code == 2
    assert output.read_text(encoding="utf-8") == "preserve"


def test_cli_custom_topology_requires_enough_sites(tmp_path):
    source = tmp_path / "source.qasm"
    edge_file = tmp_path / "edges.json"
    output = tmp_path / "compiled.qasm"
    _write_qasm(source)
    edge_file.write_text(json.dumps({"num_qubits": 2, "edges": [[0, 1]]}), encoding="utf-8")

    with pytest.raises(SystemExit) as error:
        main(["compile", "--circuit", str(source), "--topology", "custom",
              "--edges-file", str(edge_file), "--output", str(output)])

    assert error.value.code == 2
    assert not output.exists()


def test_cli_learned_router_uses_checkpoint_and_reports_fallback(tmp_path, capsys):
    source = tmp_path / "source.qasm"
    checkpoint = tmp_path / "policy.pt"
    output = tmp_path / "learned.qasm"
    _write_qasm(source)
    config = PPOConfig(hidden=16, message_passing_steps=1)
    model = GraphActorCritic(hidden=config.hidden,
                             message_passing_steps=config.message_passing_steps)
    save_checkpoint(str(checkpoint), model, config, {"test": True})

    status = main(["compile", "--circuit", str(source), "--topology", "line",
                   "--router", "learned", "--checkpoint", str(checkpoint),
                   "--seed", "19", "--output", str(output)])

    summary = json.loads(capsys.readouterr().out)
    assert status == 0
    assert summary["router"] == "learned"
    assert summary["route_replay_validation"] is True
    assert summary["semantic_validation"] is True
    assert qasm2.load(str(output)).num_qubits == 3


@pytest.mark.parametrize(
    ("name", "physical", "rows", "columns", "edge_count"),
    [("line", 4, None, None, 3), ("ring", 4, None, None, 4),
     ("grid", 4, 2, 2, 4)],
)
def test_cli_topology_constructors(name, physical, rows, columns, edge_count):
    graph = _topology(name, 3, physical, rows, columns, None)
    assert set(graph.nodes) == set(range(physical))
    assert graph.number_of_edges() == edge_count


def test_cli_rejects_invalid_topology_dimensions_and_labels(tmp_path):
    edge_file = tmp_path / "edges.json"
    edge_file.write_text(json.dumps({"num_qubits": 3, "edges": [[0, 3]]}), encoding="utf-8")
    with pytest.raises(ValueError, match=r"rows \* columns"):
        _topology("grid", 4, 4, 1, 3, None)
    with pytest.raises(ValueError, match="labels"):
        _topology("custom", 2, None, None, None, edge_file)


def test_cli_validate_accepts_legal_compiled_circuit(tmp_path, capsys):
    compiled = tmp_path / "legal.qasm"
    circuit = QuantumCircuit(3)
    circuit.cx(0, 1)
    qasm2.dump(circuit, str(compiled))

    status = main(["validate", "--circuit", str(compiled), "--topology", "line"])

    report = json.loads(capsys.readouterr().out)
    assert status == 0
    assert report["status"] == "valid"
    assert report["hardware_legality"] is True
    assert report["semantic_equivalence"] is None


def test_cli_validate_rejects_illegal_compiled_interaction(tmp_path):
    compiled = tmp_path / "illegal.qasm"
    circuit = QuantumCircuit(3)
    circuit.cx(0, 2)
    qasm2.dump(circuit, str(compiled))

    with pytest.raises(SystemExit) as error:
        main(["validate", "--circuit", str(compiled), "--topology", "line"])

    assert error.value.code == 2

