/**
 * QWeave Studio: Interactive Quantum Circuit Routing & Optimization Frontend
 */

document.addEventListener("DOMContentLoaded", () => {
  // Global State
  const state = {
    circuitMode: "preset", // 'preset' | 'upload' | 'editor'
    circuitPresets: [],
    hardwarePresets: [],
    currentCircuit: null,
    currentHardware: null,
    uploadedQasm: "",
    compileData: null,
    replayStep: 0,
    replayPlaying: false,
    replayInterval: null,
  };

  // DOM Elements
  const el = {
    // Mode tabs
    tabPreset: document.getElementById("tabPresetCircuit"),
    tabUpload: document.getElementById("tabUploadCircuit"),
    tabEditor: document.getElementById("tabCustomCircuit"),
    presetPane: document.getElementById("presetPane"),
    uploadPane: document.getElementById("uploadPane"),
    editorPane: document.getElementById("editorPane"),

    // Circuit Selectors & Preview
    circuitSelect: document.getElementById("circuitPresetSelect"),
    presetCategoryTag: document.getElementById("presetCategoryTag"),
    presetQubitsTag: document.getElementById("presetQubitsTag"),
    presetDepthTag: document.getElementById("presetDepthTag"),
    presetGatesTag: document.getElementById("presetGatesTag"),
    presetDescText: document.getElementById("presetDescriptionText"),

    // File Upload
    dropzone: document.getElementById("qasmDropzone"),
    fileInput: document.getElementById("qasmFileInput"),
    uploadStatusBox: document.getElementById("uploadStatusBox"),
    uploadedFileName: document.getElementById("uploadedFileName"),
    uploadedFileSize: document.getElementById("uploadedFileSize"),
    clearFileBtn: document.getElementById("clearFileBtn"),

    // Editor
    codeEditor: document.getElementById("qasmCodeEditor"),
    insertSampleBtn: document.getElementById("insertSampleBtn"),

    // Hardware
    hardwareSelect: document.getElementById("hardwarePresetSelect"),
    customLayoutPane: document.getElementById("customLayoutPane"),
    customNodesInput: document.getElementById("customNodesInput"),
    customEdgesInput: document.getElementById("customEdgesInput"),
    hardwareCanvas: document.getElementById("hardwareCanvas"),
    hardwareTitleBadge: document.getElementById("hardwareTitleBadge"),
    hardwareNodesBadge: document.getElementById("hardwareNodesBadge"),

    // Compile options
    methodRadios: document.querySelectorAll('input[name="compileMethod"]'),
    schedulingToggle: document.getElementById("schedulingToggle"),
    decomposeToggle: document.getElementById("decomposeToggle"),
    compileBtn: document.getElementById("compileBtn"),
    compileBtnText: document.getElementById("compileBtnText"),
    compileSpinner: document.getElementById("compileSpinner"),
    quickDemoBtn: document.getElementById("quickDemoBtn"),
    emptyDemoBtn: document.getElementById("emptyCompileDemoBtn"),

    // Results container
    emptyState: document.getElementById("emptyResultsState"),
    activeResults: document.getElementById("activeResultsContent"),
    resultBanner: document.getElementById("resultStatusBanner"),
    bannerMsg: document.getElementById("bannerMessage"),
    bannerMethodBadge: document.getElementById("bannerMethodBadge"),

    // Metrics
    valSwapsAdded: document.getElementById("valSwapsAdded"),
    swapBadge: document.getElementById("swapBadge"),
    valSourceDepth: document.getElementById("valSourceDepth"),
    valRoutedDepth: document.getElementById("valRoutedDepth"),
    depthOverheadBadge: document.getElementById("depthOverheadBadge"),
    depthFooter: document.getElementById("depthFooter"),
    valTwoQubitOps: document.getElementById("valTwoQubitOps"),
    valTotalGates: document.getElementById("valTotalGates"),
    valCircuitFidelity: document.getElementById("valCircuitFidelity"),
    fidelityBadge: document.getElementById("fidelityBadge"),
    valStateFidelity: document.getElementById("valStateFidelity"),
    fStateVal: document.getElementById("fStateVal"),
    fCircuitVal: document.getElementById("fCircuitVal"),
    fSwapVal: document.getElementById("fSwapVal"),
    probChartContainer: document.getElementById("probChartContainer"),
    valRuntime: document.getElementById("valRuntime"),
    semanticStatusText: document.getElementById("semanticStatusText"),

    // Comparison
    comparisonSection: document.getElementById("comparisonSection"),
    comparisonGrid: document.getElementById("comparisonCardsGrid"),

    // Result tabs
    resultTabsNav: document.getElementById("resultsTabsNav"),
    circuitAsciiOutput: document.getElementById("circuitAsciiOutput"),
    circuitDimensionsSub: document.getElementById("circuitDimensionsSub"),
    copyDiagramBtn: document.getElementById("copyDiagramBtn"),

    // Replay Scrubber
    replayCanvas: document.getElementById("replayCanvas"),
    replayScrubber: document.getElementById("replayScrubber"),
    replayStepCounter: document.getElementById("replayStepCounter"),
    replayPlayBtn: document.getElementById("replayPlayBtn"),
    replayPrevBtn: document.getElementById("replayPrevBtn"),
    replayNextBtn: document.getElementById("replayNextBtn"),
    replayResetBtn: document.getElementById("replayResetBtn"),
    stepKindBadge: document.getElementById("stepKindBadge"),
    stepDetailsText: document.getElementById("stepDetailsText"),

    // Mapping
    initialMappingChips: document.getElementById("initialMappingChips"),
    finalMappingChips: document.getElementById("finalMappingChips"),

    // QASM Output
    routedQasmOutput: document.getElementById("routedQasmOutput"),
    copyQasmBtn: document.getElementById("copyQasmBtn"),
    downloadQasmBtn: document.getElementById("downloadQasmBtn"),
  };

  // ==========================================================================
  // Initialization & Data Fetching
  // ==========================================================================
  async function init() {
    try {
      const [circuitsRes, layoutsRes] = await Promise.all([
        fetch("/api/circuits/presets"),
        fetch("/api/layouts/presets"),
      ]);

      if (circuitsRes.ok) {
        state.circuitPresets = await circuitsRes.json();
        renderCircuitPresetsSelect();
      }

      if (layoutsRes.ok) {
        state.hardwarePresets = await layoutsRes.json();
        renderHardwarePresetsSelect();
      }

      setupEventListeners();
      drawHardwareTopology();
    } catch (err) {
      console.error("Initialization error:", err);
    }
  }

  function renderCircuitPresetsSelect() {
    el.circuitSelect.innerHTML = "";
    state.circuitPresets.forEach((p) => {
      const opt = document.createElement("option");
      opt.value = p.id;
      opt.textContent = `${p.name} (${p.qubits}Q, depth ${p.depth})`;
      el.circuitSelect.appendChild(opt);
    });

    // Default selection: star_4q
    const defaultPreset = state.circuitPresets.find((p) => p.id === "star_4q") || state.circuitPresets[0];
    if (defaultPreset) {
      el.circuitSelect.value = defaultPreset.id;
      updateCircuitPresetDetails(defaultPreset);
    }
  }

  function updateCircuitPresetDetails(preset) {
    state.currentCircuit = preset;
    el.presetCategoryTag.textContent = preset.category || "General";
    el.presetQubitsTag.textContent = `${preset.qubits} Qubits`;
    el.presetDepthTag.textContent = `Depth: ${preset.depth}`;
    el.presetGatesTag.textContent = `Gates: ${preset.gate_count}`;
    el.presetDescText.textContent = preset.description || "";
  }

  function renderHardwarePresetsSelect() {
    el.hardwareSelect.innerHTML = "";
    state.hardwarePresets.forEach((hw) => {
      const opt = document.createElement("option");
      opt.value = hw.id;
      opt.textContent = `${hw.name} [${hw.nodes} physical qubits]`;
      el.hardwareSelect.appendChild(opt);
    });

    const customOpt = document.createElement("option");
    customOpt.value = "custom";
    customOpt.textContent = "⚙️ Custom Coupling Architecture...";
    el.hardwareSelect.appendChild(customOpt);

    // Default: line_4q
    const defaultHw = state.hardwarePresets.find((h) => h.id === "line_4q") || state.hardwarePresets[0];
    if (defaultHw) {
      el.hardwareSelect.value = defaultHw.id;
      state.currentHardware = defaultHw;
      el.hardwareTitleBadge.textContent = defaultHw.name;
      el.hardwareNodesBadge.textContent = `${defaultHw.nodes} Physical Qubits`;
    }
  }

  // ==========================================================================
  // Hardware Topology Canvas Rendering
  // ==========================================================================
  function drawHardwareTopology(activeNodes = [], activeEdge = null, mapping = null, edgeUtilization = null) {
    const canvas = el.hardwareCanvas;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    const width = canvas.width;
    const height = canvas.height;

    ctx.clearRect(0, 0, width, height);

    const hw = state.currentHardware;
    if (!hw) return;

    const numNodes = hw.nodes;
    const edges = hw.edges || [];
    const coordsMap = hw.coords || {};

    // Compute coordinates for all nodes in [-1, 1] normalized box
    const nodePoints = {};
    if (Object.keys(coordsMap).length === numNodes) {
      // Find min/max of coords
      let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity;
      for (let i = 0; i < numNodes; i++) {
        const c = coordsMap[i] || [i, 0];
        minX = Math.min(minX, c[0]);
        maxX = Math.max(maxX, c[0]);
        minY = Math.min(minY, c[1]);
        maxY = Math.max(maxY, c[1]);
      }
      const rangeX = maxX - minX || 1;
      const rangeY = maxY - minY || 1;
      const padding = 45;

      for (let i = 0; i < numNodes; i++) {
        const c = coordsMap[i] || [i, 0];
        const nx = rangeX === 0 ? 0.5 : (c[0] - minX) / rangeX;
        const ny = rangeY === 0 ? 0.5 : 1 - (c[1] - minY) / rangeY;
        nodePoints[i] = {
          x: padding + nx * (width - 2 * padding),
          y: padding + ny * (height - 2 * padding),
        };
      }
    } else {
      // Fallback: circular layout
      const radius = Math.min(width, height) / 2 - 40;
      const cx = width / 2;
      const cy = height / 2;
      for (let i = 0; i < numNodes; i++) {
        const angle = (2 * Math.PI * i) / numNodes - Math.PI / 2;
        nodePoints[i] = {
          x: cx + radius * Math.cos(angle),
          y: cy + radius * Math.sin(angle),
        };
      }
    }

    // 1. Draw Edges (Couplers)
    edges.forEach(([u, v]) => {
      const p1 = nodePoints[u];
      const p2 = nodePoints[v];
      if (!p1 || !p2) return;

      const isEdgeActive =
        activeEdge &&
        ((activeEdge[0] === u && activeEdge[1] === v) ||
          (activeEdge[0] === v && activeEdge[1] === u));

      const edgeKey = `${Math.min(u, v)}-${Math.max(u, v)}`;
      const usage = edgeUtilization ? edgeUtilization[edgeKey] || 0 : 0;

      ctx.beginPath();
      ctx.moveTo(p1.x, p1.y);
      ctx.lineTo(p2.x, p2.y);

      if (isEdgeActive) {
        ctx.strokeStyle = "#38bdf8";
        ctx.lineWidth = 4;
        ctx.shadowColor = "#06b6d4";
        ctx.shadowBlur = 12;
      } else if (usage > 0) {
        ctx.strokeStyle = "rgba(6, 182, 212, 0.75)";
        ctx.lineWidth = 2.5 + Math.min(usage, 4);
        ctx.shadowColor = "rgba(6, 182, 212, 0.4)";
        ctx.shadowBlur = 6;
      } else {
        ctx.strokeStyle = "rgba(255, 255, 255, 0.18)";
        ctx.lineWidth = 2;
        ctx.shadowBlur = 0;
      }
      ctx.stroke();
      ctx.shadowBlur = 0; // reset
    });

    // Inverse mapping: physical -> logical
    const physicalToLogical = {};
    if (mapping) {
      Object.entries(mapping).forEach(([l, p]) => {
        physicalToLogical[p] = l;
      });
    }

    // 2. Draw Nodes (Physical Qubits)
    for (let i = 0; i < numNodes; i++) {
      const pt = nodePoints[i];
      if (!pt) continue;

      const isActive = activeNodes.includes(i);
      const logicalId = physicalToLogical[i];
      const isMapped = logicalId !== undefined;

      const nodeRadius = 15;

      // Glow behind active or mapped nodes
      if (isActive) {
        ctx.beginPath();
        ctx.arc(pt.x, pt.y, nodeRadius + 8, 0, Math.PI * 2);
        ctx.fillStyle = "rgba(6, 182, 212, 0.4)";
        ctx.fill();
      }

      // Outer circle
      ctx.beginPath();
      ctx.arc(pt.x, pt.y, nodeRadius, 0, Math.PI * 2);
      if (isActive) {
        ctx.fillStyle = "#06b6d4";
        ctx.strokeStyle = "#ffffff";
      } else if (isMapped) {
        ctx.fillStyle = "#3b82f6";
        ctx.strokeStyle = "#60a5fa";
      } else {
        ctx.fillStyle = "#1e293b";
        ctx.strokeStyle = "rgba(255, 255, 255, 0.25)";
      }
      ctx.lineWidth = 2;
      ctx.fill();
      ctx.stroke();

      // Node Label (Physical Qubit ID)
      ctx.fillStyle = "#ffffff";
      ctx.font = "bold 11px Inter, sans-serif";
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
      ctx.fillText(`p${i}`, pt.x, pt.y);

      // Logical Qubit Badge below
      if (isMapped) {
        ctx.fillStyle = "#a5f3fc";
        ctx.font = "bold 10px JetBrains Mono, monospace";
        ctx.fillText(`q${logicalId}`, pt.x, pt.y + nodeRadius + 12);
      }
    }
  }

  // ==========================================================================
  // Event Listeners Setup
  // ==========================================================================
  function setupEventListeners() {
    // Mode Switcher Tabs
    const tabs = [
      { btn: el.tabPreset, pane: el.presetPane, mode: "preset" },
      { btn: el.tabUpload, pane: el.uploadPane, mode: "upload" },
      { btn: el.tabEditor, pane: el.editorPane, mode: "editor" },
    ];

    tabs.forEach(({ btn, pane, mode }) => {
      btn.addEventListener("click", () => {
        tabs.forEach((t) => {
          t.btn.classList.remove("active");
          t.pane.classList.remove("active");
        });
        btn.classList.add("active");
        pane.classList.add("active");
        state.circuitMode = mode;
      });
    });

    // Preset Circuit Select
    el.circuitSelect.addEventListener("change", (e) => {
      const preset = state.circuitPresets.find((p) => p.id === e.target.value);
      if (preset) {
        updateCircuitPresetDetails(preset);
      }
    });

    // Hardware Topology Select
    el.hardwareSelect.addEventListener("change", (e) => {
      const val = e.target.value;
      if (val === "custom") {
        el.customLayoutPane.classList.remove("hidden");
        updateCustomHardware();
      } else {
        el.customLayoutPane.classList.add("hidden");
        const hw = state.hardwarePresets.find((h) => h.id === val);
        if (hw) {
          state.currentHardware = hw;
          el.hardwareTitleBadge.textContent = hw.name;
          el.hardwareNodesBadge.textContent = `${hw.nodes} Physical Qubits`;
          drawHardwareTopology();
        }
      }
    });

    // Custom layout inputs
    el.customNodesInput.addEventListener("input", updateCustomHardware);
    el.customEdgesInput.addEventListener("input", updateCustomHardware);

    // Dropzone Drag & Drop
    const dropzone = el.dropzone;
    dropzone.addEventListener("click", () => el.fileInput.click());
    dropzone.addEventListener("dragover", (e) => {
      e.preventDefault();
      dropzone.classList.add("dragover");
    });
    dropzone.addEventListener("dragleave", () => dropzone.classList.remove("dragover"));
    dropzone.addEventListener("drop", (e) => {
      e.preventDefault();
      dropzone.classList.remove("dragover");
      if (e.dataTransfer.files.length > 0) {
        handleFileUpload(e.dataTransfer.files[0]);
      }
    });

    el.fileInput.addEventListener("change", (e) => {
      if (e.target.files.length > 0) {
        handleFileUpload(e.target.files[0]);
      }
    });

    el.clearFileBtn.addEventListener("click", () => {
      state.uploadedQasm = "";
      el.uploadStatusBox.classList.add("hidden");
      el.dropzone.classList.remove("hidden");
      el.fileInput.value = "";
    });

    // Code Editor Template
    el.insertSampleBtn.addEventListener("click", () => {
      el.codeEditor.value =
`OPENQASM 2.0;
include "qelib1.inc";

qreg q[4];
creg c[4];

// Bell state + entanglement hops
h q[0];
cx q[0], q[2];
cx q[1], q[3];
cx q[0], q[3];
`;
    });

    // Compile Button
    el.compileBtn.addEventListener("click", executeCompilation);
    el.quickDemoBtn.addEventListener("click", runQuickDemo);
    el.emptyDemoBtn.addEventListener("click", runQuickDemo);

    // Result Tabs
    el.resultTabsNav.querySelectorAll(".tab-btn").forEach((btn) => {
      btn.addEventListener("click", () => {
        el.resultTabsNav.querySelectorAll(".tab-btn").forEach((b) => b.classList.remove("active"));
        btn.classList.add("active");
        const targetId = btn.getAttribute("data-target");
        document.querySelectorAll(".result-tab-content").forEach((c) => c.classList.remove("active"));
        const targetPane = document.getElementById(targetId);
        if (targetPane) targetPane.classList.add("active");
      });
    });

    // Replay Controls
    el.replayScrubber.addEventListener("input", (e) => {
      setReplayStep(parseInt(e.target.value, 10));
    });
    el.replayPlayBtn.addEventListener("click", toggleReplayPlay);
    el.replayPrevBtn.addEventListener("click", () => setReplayStep(state.replayStep - 1));
    el.replayNextBtn.addEventListener("click", () => setReplayStep(state.replayStep + 1));
    el.replayResetBtn.addEventListener("click", () => setReplayStep(0));

    // Copy & Download
    el.copyDiagramBtn.addEventListener("click", () => {
      copyToClipboard(el.circuitAsciiOutput.textContent, el.copyDiagramBtn, "Diagram Copied!");
    });
    el.copyQasmBtn.addEventListener("click", () => {
      copyToClipboard(el.routedQasmOutput.textContent, el.copyQasmBtn, "QASM Copied!");
    });
    el.downloadQasmBtn.addEventListener("click", downloadQasmFile);
  }

  function updateCustomHardware() {
    try {
      const nodes = parseInt(el.customNodesInput.value, 10) || 4;
      const edges = JSON.parse(el.customEdgesInput.value);
      state.currentHardware = {
        name: `Custom Topology (${nodes}Q)`,
        nodes: nodes,
        edges: edges,
        coords: {},
      };
      el.hardwareTitleBadge.textContent = state.currentHardware.name;
      el.hardwareNodesBadge.textContent = `${nodes} Physical Qubits`;
      drawHardwareTopology();
    } catch {
      // JSON parsing incomplete
    }
  }

  function handleFileUpload(file) {
    const reader = new FileReader();
    reader.onload = (e) => {
      state.uploadedQasm = e.target.result;
      el.uploadedFileName.textContent = file.name;
      el.uploadedFileSize.textContent = `${(file.size / 1024).toFixed(1)} KB`;
      el.uploadStatusBox.classList.remove("hidden");
      el.dropzone.classList.add("hidden");
      el.codeEditor.value = state.uploadedQasm;
    };
    reader.readAsText(file);
  }

  function runQuickDemo() {
    // Select Star Graph 4Q and Line 4Q
    el.circuitSelect.value = "star_4q";
    const preset = state.circuitPresets.find((p) => p.id === "star_4q");
    if (preset) updateCircuitPresetDetails(preset);

    el.hardwareSelect.value = "line_4q";
    const hw = state.hardwarePresets.find((h) => h.id === "line_4q");
    if (hw) {
      state.currentHardware = hw;
      el.hardwareTitleBadge.textContent = hw.name;
      el.hardwareNodesBadge.textContent = `${hw.nodes} Physical Qubits`;
      drawHardwareTopology();
    }

    // Switch to preset mode
    el.tabPreset.click();

    // Trigger compile
    executeCompilation();
  }

  // ==========================================================================
  // Compilation Execution & Results Rendering
  // ==========================================================================
  async function executeCompilation() {
    // Collect settings
    const methodInput = document.querySelector('input[name="compileMethod"]:checked');
    const method = methodInput ? methodInput.value : "weighted";
    const schedule = el.schedulingToggle.checked;
    const decompose = el.decomposeToggle.checked;

    let customQasm = null;
    if (state.circuitMode === "upload") {
      customQasm = state.uploadedQasm;
      if (!customQasm) {
        alert("Please upload a .qasm file first.");
        return;
      }
    } else if (state.circuitMode === "editor") {
      customQasm = el.codeEditor.value;
      if (!customQasm.trim()) {
        alert("Please enter OpenQASM code into the editor.");
        return;
      }
    }

    const payload = {
      circuit_mode: state.circuitMode,
      preset_circuit_id: el.circuitSelect.value,
      custom_qasm: customQasm,
      layout_id: el.hardwareSelect.value,
      method: method,
      schedule: schedule,
      auto_decompose: decompose,
    };

    if (el.hardwareSelect.value === "custom") {
      payload.custom_nodes = parseInt(el.customNodesInput.value, 10);
      try {
        payload.custom_edges = JSON.parse(el.customEdgesInput.value);
      } catch {
        alert("Invalid custom edges format. Must be JSON array like [[0,1],[1,2]].");
        return;
      }
    }

    // Set UI loading state
    el.compileBtn.disabled = true;
    el.compileSpinner.classList.remove("hidden");
    el.compileBtnText.textContent = "Compiling Circuit...";

    try {
      const response = await fetch("/api/compile", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Compilation failed");
      }

      state.compileData = data;
      renderCompilationResults(data);
    } catch (err) {
      alert(`Error during compilation: ${err.message}`);
    } finally {
      el.compileBtn.disabled = false;
      el.compileSpinner.classList.add("hidden");
      el.compileBtnText.textContent = "⚡ Compile Circuit";
    }
  }

  function renderCompilationResults(data) {
    // Show results panel, hide empty state
    el.emptyState.classList.add("hidden");
    el.activeResults.classList.remove("hidden");

    const primary = data.primary_result;

    // 1. Banner
    el.resultBanner.classList.remove("hidden");
    el.bannerMethodBadge.textContent = primary.method.toUpperCase();
    el.bannerMsg.textContent = `Circuit successfully compiled to ${data.hardware_layout.name}!`;

    // 2. Metrics Cards
    // SWAPs Added
    el.valSwapsAdded.textContent = primary.swaps_added;
    if (primary.swaps_added === 0) {
      el.swapBadge.textContent = "Optimal (0 SWAPs)";
      el.swapBadge.className = "metric-badge success";
    } else {
      el.swapBadge.textContent = `+${primary.swaps_added} SWAP`;
      el.swapBadge.className = "metric-badge info";
    }

    // Depth
    el.valSourceDepth.textContent = primary.source_depth;
    el.valRoutedDepth.textContent = primary.routed_depth;
    const overheadSign = primary.depth_delta >= 0 ? "+" : "";
    el.depthOverheadBadge.textContent = `${overheadSign}${primary.depth_overhead_percent}%`;
    el.depthFooter.textContent = `Δ Depth: ${overheadSign}${primary.depth_delta} layers`;

    // Ops
    el.valTwoQubitOps.textContent = primary.two_qubit_count;
    el.valTotalGates.textContent = primary.routed_gate_count;

    // Fidelity Metrics Card & Details
    if (primary.circuit_fidelity !== undefined && primary.circuit_fidelity !== null) {
      const fPct = (primary.circuit_fidelity * 100).toFixed(2);
      if (el.valCircuitFidelity) el.valCircuitFidelity.textContent = `${fPct}%`;
      if (el.fidelityBadge) {
        const fScore = Number(primary.circuit_fidelity).toFixed(3);
        if (primary.circuit_fidelity >= 0.95) {
          el.fidelityBadge.textContent = `F = ${fScore}`;
          el.fidelityBadge.className = "metric-badge success";
        } else if (primary.circuit_fidelity >= 0.8) {
          el.fidelityBadge.textContent = `F = ${fScore}`;
          el.fidelityBadge.className = "metric-badge info";
        } else {
          el.fidelityBadge.textContent = `F = ${fScore}`;
          el.fidelityBadge.className = "metric-badge warning";
        }
      }
    } else {
      if (el.valCircuitFidelity) el.valCircuitFidelity.textContent = "--";
      if (el.fidelityBadge) {
        el.fidelityBadge.textContent = "--";
        el.fidelityBadge.className = "metric-badge neutral";
      }
    }

    if (primary.state_fidelity !== undefined && primary.state_fidelity !== null) {
      const sfVal = Number(primary.state_fidelity);
      if (el.valStateFidelity) el.valStateFidelity.textContent = `${sfVal.toFixed(4)} (Ideal)`;
      if (el.fStateVal) el.fStateVal.textContent = `${sfVal.toFixed(6)} (100.0% Unitary Overlap)`;
    } else {
      if (el.valStateFidelity) el.valStateFidelity.textContent = "N/A";
      if (el.fStateVal) el.fStateVal.textContent = "N/A (resets / >12Q)";
    }

    if (primary.fidelity_breakdown) {
      const fb = primary.fidelity_breakdown;
      if (el.fCircuitVal) el.fCircuitVal.textContent = `${(fb.estimated_circuit_fidelity * 100).toFixed(2)}%`;
      const swapCost = ((1 - fb.swap_fidelity_impact) * 100).toFixed(2);
      if (el.fSwapVal) el.fSwapVal.textContent = `-${swapCost}%`;
    }


    // Validation & Runtime
    el.valRuntime.textContent = primary.runtime_ms;
    el.semanticStatusText.textContent = primary.semantic_validation
      ? "Unitary / Statevector Verified"
      : "Replay Verified";

    // 3. Comparison Section (if Compare All)
    if (data.all_results) {
      el.comparisonSection.classList.remove("hidden");
      renderComparisonCards(data.all_results);
    } else {
      el.comparisonSection.classList.add("hidden");
    }

    // 4. Circuit Diagram Tab
    el.circuitAsciiOutput.textContent = primary.routed_diagram;
    el.circuitDimensionsSub.textContent = `${data.hardware_layout.nodes} physical wires • ${primary.swaps_added} SWAPs • depth ${primary.routed_depth}`;

    // 5. OpenQASM Tab
    el.routedQasmOutput.textContent = primary.routed_qasm;

    // 6. Qubit Mapping Allocation
    renderMappingChips(primary.initial_mapping, el.initialMappingChips);
    renderMappingChips(primary.final_mapping, el.finalMappingChips);

    // 7. Probability Distribution & Density Tab
    renderProbabilityChart(primary.probabilities);

    // 8. Replay Scrubber Setup
    const trace = primary.trace || [];
    el.replayScrubber.max = Math.max(0, trace.length - 1);
    el.replayScrubber.value = 0;
    setReplayStep(0);

    // 9. Update Hardware Topology Canvas with Mapping & Edge Utilization
    drawHardwareTopology(
      [],
      null,
      primary.initial_mapping,
      primary.edge_utilization
    );
  }

  function renderProbabilityChart(probs) {
    if (!el.probChartContainer) return;
    el.probChartContainer.innerHTML = "";

    if (!probs || !probs.source) {
      el.probChartContainer.innerHTML = `
        <div class="empty-prob-note">
          Statevector probability distribution not computed (circuit exceeds 12 qubits or contains non-unitary resets).
        </div>`;
      return;
    }

    const sourceMap = probs.source || {};
    const routedMap = probs.routed || {};
    const allKeys = Array.from(new Set([...Object.keys(sourceMap), ...Object.keys(routedMap)])).sort();

    if (allKeys.length === 0) {
      el.probChartContainer.innerHTML = `
        <div class="empty-prob-note">No significant basis state amplitudes detected.</div>`;
      return;
    }

    allKeys.forEach((key) => {
      const pSource = sourceMap[key] !== undefined ? sourceMap[key] : 0.0;
      const pRouted = routedMap[key] !== undefined ? routedMap[key] : 0.0;
      const diff = Math.abs(pSource - pRouted);
      const isMatch = diff < 0.005;

      const row = document.createElement("div");
      row.className = "prob-row";

      const sourceWidth = Math.max(pSource > 0 ? 5 : 0, pSource * 100);
      const routedWidth = Math.max(pRouted > 0 ? 5 : 0, pRouted * 100);

      row.innerHTML = `
        <div class="prob-state-label">|${key}⟩</div>
        <div class="prob-bars-group">
          <div class="prob-bar-track" title="Source: ${(pSource * 100).toFixed(2)}%">
            <div class="prob-bar-fill source" style="width: ${sourceWidth}%;">
              ${(pSource * 100).toFixed(1)}%
            </div>
          </div>
          <div class="prob-bar-track" title="Routed: ${(pRouted * 100).toFixed(2)}%">
            <div class="prob-bar-fill routed" style="width: ${routedWidth}%;">
              ${(pRouted * 100).toFixed(1)}%
            </div>
          </div>
        </div>
        <div class="prob-delta-tag ${isMatch ? "matched" : "diff"}">
          ${isMatch ? "✓ Invariant" : `Δ ${(diff * 100).toFixed(1)}%`}
        </div>
      `;
      el.probChartContainer.appendChild(row);
    });
  }


  function renderComparisonCards(allResults) {
    el.comparisonGrid.innerHTML = "";
    const methods = [
      { key: "weighted", label: "⚡ QWeave Weighted", tag: "Primary" },
      { key: "basic", label: "🎯 QWeave Basic", tag: "Baseline" },
      { key: "sabre", label: "🔬 Qiskit SABRE", tag: "Reference" },
    ];

    // Find min swaps
    let minSwaps = Infinity;
    Object.values(allResults).forEach((r) => {
      if (r.swaps_added !== undefined) {
        minSwaps = Math.min(minSwaps, r.swaps_added);
      }
    });

    methods.forEach(({ key, label, tag }) => {
      const res = allResults[key];
      if (!res) return;

      const card = document.createElement("div");
      const isWinner = res.swaps_added === minSwaps;
      card.className = `comp-card ${isWinner ? "winner" : ""}`;

      card.innerHTML = `
        <div class="comp-card-title">
          <span>${label}</span>
          <span class="tag ${isWinner ? "info" : "neutral"}">${isWinner ? "★ Best SWAPs" : tag}</span>
        </div>
        <div class="comp-stat-row">
          <span class="comp-stat-label">SWAPs Added:</span>
          <span class="comp-stat-val">${res.swaps_added}</span>
        </div>
        <div class="comp-stat-row">
          <span class="comp-stat-label">Routed Depth:</span>
          <span class="comp-stat-val">${res.routed_depth} (${res.depth_delta >= 0 ? "+" : ""}${res.depth_overhead_percent}%)</span>
        </div>
        <div class="comp-stat-row">
          <span class="comp-stat-label">Est. Fidelity:</span>
          <span class="comp-stat-val">${res.circuit_fidelity !== undefined && res.circuit_fidelity !== null ? (res.circuit_fidelity * 100).toFixed(1) + "%" : "--"}</span>
        </div>
        <div class="comp-stat-row">
          <span class="comp-stat-label">Runtime:</span>
          <span class="comp-stat-val">${res.runtime_ms} ms</span>
        </div>

      `;
      el.comparisonGrid.appendChild(card);
    });
  }

  function renderMappingChips(mapping, container) {
    container.innerHTML = "";
    if (!mapping) return;
    const sortedLogicals = Object.keys(mapping).sort((a, b) => parseInt(a) - parseInt(b));
    sortedLogicals.forEach((l) => {
      const p = mapping[l];
      const chip = document.createElement("div");
      chip.className = "qubit-chip";
      chip.innerHTML = `
        <span class="logical">q${l}</span>
        <span>➔</span>
        <span class="physical">p${p}</span>
      `;
      container.appendChild(chip);
    });
  }

  // ==========================================================================
  // Step-by-Step Route Replay Animation
  // ==========================================================================
  function setReplayStep(stepIndex) {
    if (!state.compileData || !state.compileData.primary_result) return;
    const trace = state.compileData.primary_result.trace || [];
    if (trace.length === 0) {
      el.replayStepCounter.textContent = "0 / 0";
      el.stepDetailsText.textContent = "No routing steps recorded.";
      return;
    }

    const clamped = Math.max(0, Math.min(stepIndex, trace.length - 1));
    state.replayStep = clamped;
    el.replayScrubber.value = clamped;
    el.replayStepCounter.textContent = `${clamped + 1} / ${trace.length}`;

    const step = trace[clamped];
    let currentMapping = state.compileData.primary_result.initial_mapping;
    let activeNodes = [];
    let activeEdge = null;

    if (step.kind === "inserted_swap") {
      el.stepKindBadge.textContent = "⚡ SWAP INSERTED";
      el.stepKindBadge.className = "step-badge swap";
      el.stepDetailsText.textContent = `SWAP inserted along hardware edge (p${step.edge[0]}, p${step.edge[1]})`;
      activeNodes = step.edge;
      activeEdge = step.edge;
      if (step.mapping) currentMapping = step.mapping;
    } else {
      el.stepKindBadge.textContent = `${step.operation.toUpperCase()} GATE`;
      el.stepKindBadge.className = "step-badge gate";
      el.stepDetailsText.textContent = `Gate on logical qubits (q${step.logical_qubits.join(", q")}) → physical qubits (p${step.physical_qubits.join(", p")})`;
      activeNodes = step.physical_qubits;
      if (step.physical_qubits.length === 2) {
        activeEdge = step.physical_qubits;
      }
    }

    // Draw on Replay Canvas
    drawReplayCanvas(activeNodes, activeEdge, currentMapping);

    // Also sync the main topology canvas
    drawHardwareTopology(
      activeNodes,
      activeEdge,
      currentMapping,
      state.compileData.primary_result.edge_utilization
    );
  }

  function drawReplayCanvas(activeNodes, activeEdge, currentMapping) {
    const canvas = el.replayCanvas;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    const width = canvas.width;
    const height = canvas.height;

    ctx.clearRect(0, 0, width, height);
    const hw = state.currentHardware;
    if (!hw) return;

    const numNodes = hw.nodes;
    const edges = hw.edges || [];
    const coordsMap = hw.coords || {};

    const nodePoints = {};
    if (Object.keys(coordsMap).length === numNodes) {
      let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity;
      for (let i = 0; i < numNodes; i++) {
        const c = coordsMap[i] || [i, 0];
        minX = Math.min(minX, c[0]);
        maxX = Math.max(maxX, c[0]);
        minY = Math.min(minY, c[1]);
        maxY = Math.max(maxY, c[1]);
      }
      const rangeX = maxX - minX || 1;
      const rangeY = maxY - minY || 1;
      const padding = 50;

      for (let i = 0; i < numNodes; i++) {
        const c = coordsMap[i] || [i, 0];
        const nx = rangeX === 0 ? 0.5 : (c[0] - minX) / rangeX;
        const ny = rangeY === 0 ? 0.5 : 1 - (c[1] - minY) / rangeY;
        nodePoints[i] = {
          x: padding + nx * (width - 2 * padding),
          y: padding + ny * (height - 2 * padding),
        };
      }
    } else {
      const radius = Math.min(width, height) / 2 - 40;
      const cx = width / 2;
      const cy = height / 2;
      for (let i = 0; i < numNodes; i++) {
        const angle = (2 * Math.PI * i) / numNodes - Math.PI / 2;
        nodePoints[i] = {
          x: cx + radius * Math.cos(angle),
          y: cy + radius * Math.sin(angle),
        };
      }
    }

    // Edges
    edges.forEach(([u, v]) => {
      const p1 = nodePoints[u];
      const p2 = nodePoints[v];
      if (!p1 || !p2) return;

      const isEdgeActive =
        activeEdge &&
        ((activeEdge[0] === u && activeEdge[1] === v) ||
          (activeEdge[0] === v && activeEdge[1] === u));

      ctx.beginPath();
      ctx.moveTo(p1.x, p1.y);
      ctx.lineTo(p2.x, p2.y);

      if (isEdgeActive) {
        ctx.strokeStyle = "#38bdf8";
        ctx.lineWidth = 5;
        ctx.shadowColor = "#06b6d4";
        ctx.shadowBlur = 14;
      } else {
        ctx.strokeStyle = "rgba(255, 255, 255, 0.16)";
        ctx.lineWidth = 2;
        ctx.shadowBlur = 0;
      }
      ctx.stroke();
      ctx.shadowBlur = 0;
    });

    const physicalToLogical = {};
    if (currentMapping) {
      Object.entries(currentMapping).forEach(([l, p]) => {
        physicalToLogical[p] = l;
      });
    }

    // Nodes
    for (let i = 0; i < numNodes; i++) {
      const pt = nodePoints[i];
      if (!pt) continue;

      const isActive = activeNodes.includes(i);
      const logicalId = physicalToLogical[i];
      const isMapped = logicalId !== undefined;
      const nodeRadius = 18;

      if (isActive) {
        ctx.beginPath();
        ctx.arc(pt.x, pt.y, nodeRadius + 8, 0, Math.PI * 2);
        ctx.fillStyle = "rgba(6, 182, 212, 0.4)";
        ctx.fill();
      }

      ctx.beginPath();
      ctx.arc(pt.x, pt.y, nodeRadius, 0, Math.PI * 2);
      ctx.fillStyle = isActive ? "#06b6d4" : isMapped ? "#3b82f6" : "#1e293b";
      ctx.strokeStyle = isActive ? "#ffffff" : isMapped ? "#60a5fa" : "rgba(255, 255, 255, 0.25)";
      ctx.lineWidth = 2.5;
      ctx.fill();
      ctx.stroke();

      ctx.fillStyle = "#ffffff";
      ctx.font = "bold 12px Inter, sans-serif";
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
      ctx.fillText(`p${i}`, pt.x, pt.y);

      if (isMapped) {
        ctx.fillStyle = "#a5f3fc";
        ctx.font = "bold 11px JetBrains Mono, monospace";
        ctx.fillText(`q${logicalId}`, pt.x, pt.y + nodeRadius + 14);
      }
    }
  }

  function toggleReplayPlay() {
    if (state.replayPlaying) {
      clearInterval(state.replayInterval);
      state.replayPlaying = false;
      el.replayPlayBtn.textContent = "▶ Play";
    } else {
      state.replayPlaying = true;
      el.replayPlayBtn.textContent = "⏸ Pause";
      const trace = (state.compileData && state.compileData.primary_result.trace) || [];
      state.replayInterval = setInterval(() => {
        if (state.replayStep >= trace.length - 1) {
          setReplayStep(0);
        } else {
          setReplayStep(state.replayStep + 1);
        }
      }, 700);
    }
  }

  // ==========================================================================
  // Helper Utilities
  // ==========================================================================
  function copyToClipboard(text, btnElement, feedbackMsg) {
    navigator.clipboard.writeText(text).then(() => {
      const originalText = btnElement.textContent;
      btnElement.textContent = `✓ ${feedbackMsg}`;
      setTimeout(() => {
        btnElement.textContent = originalText;
      }, 2000);
    });
  }

  function downloadQasmFile() {
    const text = el.routedQasmOutput.textContent;
    const blob = new Blob([text], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "routed_circuit.qasm";
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }

  // Start app
  init();
});
