"use client";

import React, { useState, useEffect, useRef } from "react";

interface ToolCall {
  tool: string;
  operation: string;
  status: string;
  trace: string[];
}

interface CalculationData {
  tool: string;
  calculation: string;
  inputs: Record<string, any>;
  results: Record<string, any>;
  units?: Record<string, string>;
  assumptions?: string[];
}

interface VerificationData {
  is_verified: boolean;
  calculated_value: number;
  recomputed_value: number;
  relative_error: number;
  tolerance_rel: number;
  reference_formula: string;
}

interface CitationSource {
  title: string;
  source: string;
  year?: number;
  report_number?: string;
  url?: string;
  page?: number;
  relevance?: number;
}

interface EvidenceSnippet {
  document_id: string;
  title: string;
  page?: number;
  snippet: string;
}

interface ScientificDiscrepancy {
  source_a: string;
  source_b: string;
  value_a: number;
  value_b: number;
  relative_difference: number;
  physical_explanation?: string;
}

interface ScientificResultData {
  result_id?: string;
  epistemic_status: string;
  condition_match_status?: string;
  quantity: string;
  value?: number | null;
  units?: string | null;
  uncertainty?: number | null;
  conditions?: Record<string, any>;
  source_dataset_id?: string;
  citation?: string;
  methodology?: string;
  confidence?: number;
  discrepancies?: ScientificDiscrepancy[];
  limitations?: string[];
  trace?: string[];
}

interface SolverInfoData {
  solver: string;
  is_available: boolean;
  status: string;
  execution_environment?: string;
  executable_path?: string | null;
  version?: string | null;
  supported_physics?: string[];
  supported_domains?: string[];
  supported_dimensions?: string[];
  detection_diagnostic?: string | null;
}

interface SimulationManifestData {
  experiment_id: string;
  solver: string;
  solver_version?: string;
  geometry: string;
  run_mode: string;
  result_status: string;
  epistemic_status: string;
  input_checksum: string;
  output_checksum?: string | null;
  is_converged: boolean;
  cl?: number | null;
  cd?: number | null;
  cm?: number | null;
  residuals?: Record<string, number>;
  logs?: string[];
  result_files?: string[];
  input_parameters?: Record<string, any>;
  boundary_conditions?: Record<string, any>;
}

interface Message {
  id: string;
  sender: "user" | "assistant";
  content: string;
  model?: string;
  timestamp: string;
  tool_calls?: ToolCall[];
  calculations?: CalculationData[];
  verification?: VerificationData | null;
  sources?: CitationSource[];
  evidence?: EvidenceSnippet[];
  assumptions?: string[];
  provenance?: Record<string, any>[];
  limitations?: string[];
  dataset_match?: Record<string, any> | null;
  scientific_result?: ScientificResultData | null;
  resolution_trace?: string[];
}

interface HealthStatus {
  status: string;
  version: string;
  ollama_connected: boolean;
  configured_model: string;
  error?: string | null;
}

interface DocumentMeta {
  document_id: string;
  title: string;
  source: string;
  authors: string[];
  year?: string;
  report_number?: string;
  discipline?: string;
  url?: string;
  content_hash: string;
  chunk_count: number;
  equation_count: number;
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

const QUICK_PROMPTS = [
  "What is the drag coefficient of NACA 0012 at Mach 0.15, Re=3000000 and AoA=4°?",
  "What is the lift coefficient of NACA 0012 at Mach 0.25, Re=1500000, AoA=6° using AeroGraphNet surrogate?",
  "Generate an OpenFOAM simpleFoam simulation case for NACA 0012 at Mach 0.15 and AoA 4° in dry-run mode.",
  "What is the drag coefficient of an airfoil?",
  "What does NASA report about NACA 0012 aerodynamic behavior?",
];

export default function AASIChatApp() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "initial-welcome",
      sender: "assistant",
      content:
        "Greetings. I am AASI (Autonomous Aerospace Scientific Intelligence).\n\n" +
        "In Phase 4, I operate under a deterministic 8-level scientific resolution hierarchy with strict epistemic classification:\n" +
        "• Level 0: Query normalization and completeness audit (geometry, Mach, Reynolds, AoA)\n" +
        "• Level 1: Scientific dataset registry\n" +
        "• Level 2: Official experimental wind tunnel database (NASA TN-D-628 polar)\n" +
        "• Level 3: Validated benchmark CFD database (OpenFOAM RANS, SA/SST closures)\n" +
        "• Level 4: Physics AI surrogates with declared validity envelopes\n" +
        "• Level 5: Analytical and numerical engineering solvers (Astropy, RocketPy, SymPy)\n" +
        "• Level 6: Local & remote simulation execution fabric (OpenFOAM dry-run case generator)\n" +
        "• Level 7: Graceful clarification requests for underspecified conditions\n\n" +
        "Select a benchmark prompt or inspect the Research & Simulation Fabric drawer.",
      model: "AASI Agent (Phase 4)",
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    },
  ]);
  const [inputMessage, setInputMessage] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [isCheckingHealth, setIsCheckingHealth] = useState(false);

  // Research & Simulation Drawer State
  const [isResearchOpen, setIsResearchOpen] = useState(false);
  const [researchTab, setResearchTab] = useState<"literature" | "datasets" | "simulations">("literature");
  const [knowledgeSearchQuery, setKnowledgeSearchQuery] = useState("");
  const [docList, setDocList] = useState<DocumentMeta[]>([]);
  const [searchResults, setSearchResults] = useState<any[]>([]);
  const [isSearchingKnowledge, setIsSearchingKnowledge] = useState(false);
  const [selectedDoc, setSelectedDoc] = useState<any | null>(null);

  // Dataset Condition Search State
  const [geoInput, setGeoInput] = useState("NACA 0012");
  const [machInput, setMachInput] = useState("0.15");
  const [reInput, setReInput] = useState("3000000");
  const [aoaInput, setAoaInput] = useState("4.0");
  const [datasetMatches, setDatasetMatches] = useState<any[]>([]);
  const [isQueryingDataset, setIsQueryingDataset] = useState(false);

  // Simulation Fabric State
  const [solversList, setSolversList] = useState<SolverInfoData[]>([]);
  const [isLoadingSolvers, setIsLoadingSolvers] = useState(false);
  const [simCaseId, setSimCaseId] = useState("naca0012-simplefoam-subsonic-001");
  const [simSolver, setSimSolver] = useState("OpenFOAM");
  const [simGeometry, setSimGeometry] = useState("NACA 0012");
  const [simMach, setSimMach] = useState("0.15");
  const [simReynolds, setSimReynolds] = useState("3000000");
  const [simAoa, setSimAoa] = useState("4.0");
  const [simTurbulence, setSimTurbulence] = useState("k-omega SST");
  const [simMeshCells, setSimMeshCells] = useState("16384");
  const [simRunMode, setSimRunMode] = useState("DRY_RUN");
  const [simManifest, setSimManifest] = useState<SimulationManifestData | null>(null);
  const [isSubmittingSim, setIsSubmittingSim] = useState(false);
  const [simError, setSimError] = useState<string | null>(null);
  const [selectedManifestModal, setSelectedManifestModal] = useState<SimulationManifestData | null>(null);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  const checkHealth = async () => {
    setIsCheckingHealth(true);
    try {
      const res = await fetch(`${API_BASE}/api/health`);
      if (!res.ok) {
        throw new Error(`Backend returned HTTP status ${res.status}`);
      }
      const data: HealthStatus = await res.json();
      setHealth(data);
      if (!data.ollama_connected && data.error) {
        setErrorMessage(`Ollama Notice: ${data.error}`);
      } else {
        setErrorMessage(null);
      }
    } catch (err: any) {
      setHealth(null);
      setErrorMessage(
        `Cannot connect to AASI backend at ${API_BASE}. Ensure the FastAPI server is running.`
      );
    } finally {
      setIsCheckingHealth(false);
    }
  };

  const loadDocuments = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/knowledge/documents`);
      if (res.ok) {
        const data = await res.json();
        setDocList(data.documents || []);
      }
    } catch (e) {
      console.error("Failed to load documents", e);
    }
  };

  const loadSolvers = async () => {
    setIsLoadingSolvers(true);
    try {
      const res = await fetch(`${API_BASE}/api/solvers`);
      if (res.ok) {
        const data = await res.json();
        setSolversList(data.solvers || []);
      }
    } catch (e) {
      console.error("Failed to load solvers", e);
    } finally {
      setIsLoadingSolvers(false);
    }
  };

  useEffect(() => {
    checkHealth();
    loadDocuments();
    loadSolvers();
    const interval = setInterval(checkHealth, 15000);
    return () => clearInterval(interval);
  }, []);

  const handleKnowledgeSearch = async () => {
    if (!knowledgeSearchQuery.trim()) return;
    setIsSearchingKnowledge(true);
    try {
      const res = await fetch(`${API_BASE}/api/knowledge/search`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: knowledgeSearchQuery, k: 5 }),
      });
      if (res.ok) {
        const data = await res.json();
        setSearchResults(data.results || []);
      }
    } catch (e) {
      console.error("Knowledge search error", e);
    } finally {
      setIsSearchingKnowledge(false);
    }
  };

  const handleDatasetQuery = async () => {
    setIsQueryingDataset(true);
    try {
      const res = await fetch(`${API_BASE}/api/knowledge/datasets/query`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          geometry: geoInput,
          mach: machInput ? parseFloat(machInput) : undefined,
          reynolds: reInput ? parseFloat(reInput) : undefined,
          aoa_deg: aoaInput ? parseFloat(aoaInput) : undefined,
        }),
      });
      if (res.ok) {
        const data = await res.json();
        setDatasetMatches(data.matches || []);
      }
    } catch (e) {
      console.error("Dataset query error", e);
    } finally {
      setIsQueryingDataset(false);
    }
  };

  const handleRunSimulation = async () => {
    setIsSubmittingSim(true);
    setSimError(null);
    try {
      const res = await fetch(`${API_BASE}/api/simulations`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          case_id: simCaseId,
          solver: simSolver,
          geometry: simGeometry,
          mach: parseFloat(simMach) || 0.15,
          reynolds: parseFloat(simReynolds) || 3000000.0,
          aoa_deg: parseFloat(simAoa) || 4.0,
          turbulence_model: simTurbulence,
          mesh_cells: parseInt(simMeshCells, 10) || 16384,
          run_mode: simRunMode,
          max_iterations: 1000,
          convergence_tolerance: 1e-6,
        }),
      });
      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || `Server returned ${res.status}`);
      }
      const data = await res.json();
      setSimManifest(data);
    } catch (err: any) {
      setSimError(err.message || "Failed to submit simulation case.");
    } finally {
      setIsSubmittingSim(false);
    }
  };

  const handleInspectDoc = async (docId: string) => {
    try {
      const res = await fetch(`${API_BASE}/api/knowledge/documents/${docId}`);
      if (res.ok) {
        const doc = await res.json();
        setSelectedDoc(doc);
      }
    } catch (e) {
      console.error("Failed to fetch doc details", e);
    }
  };

  const handleSendMessage = async (textToSend?: string) => {
    const text = (textToSend || inputMessage).trim();
    if (!text || isLoading) return;

    const userMessage: Message = {
      id: "user-" + Date.now(),
      sender: "user",
      content: text,
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInputMessage("");
    setErrorMessage(null);
    setIsLoading(true);

    try {
      const response = await fetch(`${API_BASE}/api/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: text }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        const detail = errorData.detail || `Server error (${response.status})`;
        throw new Error(detail);
      }

      const data = await response.json();
      const assistantMessage: Message = {
        id: "assistant-" + Date.now(),
        sender: "assistant",
        content: data.response,
        model: data.model || health?.configured_model || "AASI Agent (Phase 4)",
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
        tool_calls: data.tool_calls || [],
        calculations: data.calculations || [],
        verification: data.verification,
        sources: data.sources || [],
        evidence: data.evidence || [],
        assumptions: data.assumptions || [],
        provenance: data.provenance || [],
        limitations: data.limitations || [],
        dataset_match: data.dataset_match,
        scientific_result: data.scientific_result,
        resolution_trace: data.resolution_trace || [],
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (err: any) {
      setErrorMessage(err.message || "Failed to communicate with AASI backend.");
    } finally {
      setIsLoading(false);
      setTimeout(() => textareaRef.current?.focus(), 100);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const clearChat = () => {
    setMessages([
      {
        id: "initial-welcome",
        sender: "assistant",
        content: "Session reset. Ready for scientific result resolution, simulation cases, and engineering queries.",
        model: "AASI Agent",
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      },
    ]);
    setErrorMessage(null);
  };

  const renderEpistemicBadge = (status: string) => {
    switch (status) {
      case "OFFICIAL_EXPERIMENT":
        return <span className="epistemic-badge exp">OFFICIAL EXPERIMENT</span>;
      case "VALIDATED_CFD":
        return <span className="epistemic-badge cfd">VALIDATED BENCHMARK CFD</span>;
      case "SURROGATE_PREDICTION":
        return <span className="epistemic-badge surrogate">SURROGATE PREDICTION</span>;
      case "ANALYTICAL_RESULT":
        return <span className="epistemic-badge analytical">ANALYTICAL RESULT</span>;
      case "LOCAL_CFD":
        return <span className="epistemic-badge local">LOCAL SIMULATION</span>;
      case "DEMO_DATA":
        return <span className="epistemic-badge demo">DEMO DATA</span>;
      case "NO_RESULT":
      default:
        return <span className="epistemic-badge no-result">NO VALIDATED RESULT</span>;
    }
  };

  return (
    <main className="app-container">
      {/* Header */}
      <header className="app-header">
        <div className="header-top">
          <div className="brand-section">
            <span className="logo-badge">PHASE 4</span>
            <div className="title-group">
              <h1>
                <span className="title-accent">AASI</span>
              </h1>
            </div>
          </div>

          {/* Telemetry Status Indicators */}
          <div className="telemetry-bar">
            {/* Knowledge & Research Toggle */}
            <button
              onClick={() => setIsResearchOpen(true)}
              className="btn-research-toggle"
              title="Open Scientific Knowledge, Datasets, and Simulation Fabric"
              type="button"
            >
              <span className="pulse-research-icon" />
              <span>RESEARCH & SIMULATION FABRIC</span>
            </button>

            {/* Active Solvers Badge */}
            <div className="status-badge tools-badge" title="Computational Tools & Simulation Fabric">
              <span className="status-dot online" />
              <span>8-LEVEL RESOLUTION • OPENFOAM (DRY-RUN) • ASTROPY • ROCKETPY</span>
            </div>

            {/* Backend Status */}
            <div className="status-badge" title="FastAPI Gateway Status">
              <span
                className={`status-dot ${
                  isCheckingHealth ? "loading" : health ? "online" : "offline"
                }`}
              />
              <span>BACKEND: {health ? "ONLINE" : "OFFLINE"}</span>
            </div>

            {/* Ollama Status */}
            <div className="status-badge" title="Local Model Runtime">
              <span
                className={`status-dot ${
                  isCheckingHealth
                    ? "loading"
                    : health?.ollama_connected
                    ? "online"
                    : "offline"
                }`}
              />
              <span>
                OLLAMA:{" "}
                {health?.ollama_connected
                  ? "CONNECTED"
                  : health
                  ? "UNREACHABLE"
                  : "DISCONNECTED"}
              </span>
            </div>

            {/* Clear Button */}
            <button
              onClick={clearChat}
              className="btn-icon"
              title="Reset conversation session"
              type="button"
            >
              CLEAR
            </button>
          </div>
        </div>

        <p className="header-subtitle">
          Autonomous Aerospace Scientific Intelligence • Epistemic Provenance • Deterministic Resolution Hierarchy • Simulation Fabric
        </p>
      </header>

      {/* Chat Viewport */}
      <section className="chat-container">
        {/* Quick Prompts */}
        {messages.length <= 1 && (
          <div className="welcome-card">
            <div className="welcome-title">
              <span>Phase 4 Deterministic Scientific Resolution & Simulation Prompts</span>
            </div>
            <p className="welcome-text">
              Select a benchmark prompt to evaluate the 8-level resolution hierarchy, multi-source conflict reconciliation, surrogate envelopes, or simulation case generation:
            </p>
            <div className="quick-prompts">
              {QUICK_PROMPTS.map((prompt, idx) => (
                <button
                  key={idx}
                  className="prompt-pill"
                  onClick={() => handleSendMessage(prompt)}
                  type="button"
                >
                  {prompt}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Message Log */}
        {messages.map((msg) => (
          <div key={msg.id} className={`message-row ${msg.sender}`}>
            {msg.sender === "assistant" && (
              <div className="avatar assistant-avatar" title="AASI Agent">
                AI
              </div>
            )}

            <div className="bubble">
              <div className="bubble-meta">
                <span>{msg.sender === "assistant" ? "AASI" : "RESEARCHER"}</span>
                {msg.model && <span>• {msg.model}</span>}
                <span>• {msg.timestamp}</span>
              </div>

              {/* 1. SCIENTIFIC RESOLUTION PROCESS TRACE (Phase 4 Hierarchy) */}
              {msg.resolution_trace && msg.resolution_trace.length > 0 && (
                <div className="resolution-trace-card">
                  <div className="resolution-trace-header">
                    <span className="trace-title">SCIENTIFIC RESOLUTION PROCESS (8-LEVEL HIERARCHY)</span>
                    <span className="trace-count">{msg.resolution_trace.length} MILESTONES</span>
                  </div>
                  <ul className="resolution-trace-steps">
                    {msg.resolution_trace.map((step, sIdx) => (
                      <li key={sIdx} className="resolution-step-item">
                        <span className="step-badge">L{sIdx}</span>
                        <span className="step-text">{step}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* 2. FIRST-CLASS SCIENTIFIC RESULT CARD WITH EPISTEMIC CLASSIFICATION */}
              {msg.scientific_result && (
                <div className="scientific-result-card">
                  <div className="result-card-top">
                    <div className="result-badge-group">
                      {renderEpistemicBadge(msg.scientific_result.epistemic_status)}
                      {msg.scientific_result.condition_match_status && (
                        <span className="match-status-badge">
                          MATCH: {msg.scientific_result.condition_match_status}
                        </span>
                      )}
                    </div>
                    {msg.scientific_result.confidence !== undefined && (
                      <span className="confidence-pill">
                        CONFIDENCE: {(msg.scientific_result.confidence * 100).toFixed(0)}%
                      </span>
                    )}
                  </div>

                  {/* Primary Numerical Output */}
                  {msg.scientific_result.value !== undefined && msg.scientific_result.value !== null && (
                    <div className="result-metric-display">
                      <div className="metric-quantity">
                        {msg.scientific_result.quantity}
                      </div>
                      <div className="metric-value-row">
                        <span className="metric-number">
                          {typeof msg.scientific_result.value === "object"
                            ? JSON.stringify(msg.scientific_result.value)
                            : String(msg.scientific_result.value)}
                        </span>
                        {msg.scientific_result.units && (
                          <span className="metric-units">{msg.scientific_result.units}</span>
                        )}
                        {msg.scientific_result.uncertainty !== null && msg.scientific_result.uncertainty !== undefined && (
                          <span className="metric-uncertainty">
                            (Uncertainty: {typeof msg.scientific_result.uncertainty === "object"
                              ? Object.entries(msg.scientific_result.uncertainty).map(([k, v]) => `±${v} (${k})`).join(", ")
                              : `±${msg.scientific_result.uncertainty}`})
                          </span>
                        )}
                      </div>
                    </div>
                  )}

                  {/* Flow and Geometric Conditions */}
                  {msg.scientific_result.conditions && Object.keys(msg.scientific_result.conditions).length > 0 && (
                    <div className="result-conditions-section">
                      <span className="section-label">NORMALIZED CONDITIONS:</span>
                      <div className="conditions-grid">
                        {Object.entries(msg.scientific_result.conditions).map(([k, v]) => (
                          <div key={k} className="condition-item">
                            <span className="cond-key">{k}:</span>
                            <span className="cond-val">{String(v)}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Provenance and Citation */}
                  {(msg.scientific_result.source_dataset_id || msg.scientific_result.citation || msg.scientific_result.methodology) && (
                    <div className="result-provenance-section">
                      <div className="provenance-row">
                        <strong>Source / Dataset:</strong> {msg.scientific_result.source_dataset_id || "N/A"}
                      </div>
                      {msg.scientific_result.citation && (
                        <div className="provenance-row">
                          <strong>Citation:</strong> {msg.scientific_result.citation}
                        </div>
                      )}
                      {msg.scientific_result.methodology && (
                        <div className="provenance-row">
                          <strong>Methodology:</strong> {msg.scientific_result.methodology}
                        </div>
                      )}
                    </div>
                  )}

                  {/* Multi-Source Discrepancies and Reconciliation */}
                  {msg.scientific_result.discrepancies && msg.scientific_result.discrepancies.length > 0 && (
                    <div className="discrepancy-section">
                      <span className="discrepancy-title">MULTI-SOURCE DISCREPANCY ANALYSIS & RECONCILIATION:</span>
                      {msg.scientific_result.discrepancies.map((disc, dIdx) => (
                        <div key={dIdx} className="discrepancy-card">
                          <div className="discrepancy-compare-row">
                            <span className="source-a-pill">{disc.source_a}: {disc.value_a}</span>
                            <span className="vs-tag">vs</span>
                            <span className="source-b-pill">{disc.source_b}: {disc.value_b}</span>
                            <span className="diff-pill">Δ {(disc.relative_difference * 100).toFixed(1)}%</span>
                          </div>
                          {disc.physical_explanation && (
                            <p className="physical-explanation-text">
                              <strong>Aerodynamic Reason:</strong> {disc.physical_explanation}
                            </p>
                          )}
                        </div>
                      ))}
                    </div>
                  )}

                  {/* Limitations */}
                  {msg.scientific_result.limitations && msg.scientific_result.limitations.length > 0 && (
                    <div className="result-limitations-section">
                      <strong>Limitations:</strong> {msg.scientific_result.limitations.join(" • ")}
                    </div>
                  )}
                </div>
              )}

              {/* 3. CITED LITERATURE & EVIDENCE */}
              {msg.sources && msg.sources.length > 0 && (
                <div className="citations-container">
                  <span className="citations-title">CITED SCIENTIFIC LITERATURE & PROVENANCE:</span>
                  <div className="sources-list">
                    {msg.sources.map((src, sIdx) => (
                      <div key={sIdx} className="source-pill" title={`Relevance: ${(src.relevance || 1).toFixed(2)}`}>
                        <span className="source-org-tag">{src.source}</span>
                        <span className="source-title-text">{src.title}</span>
                        {src.report_number && <span className="source-report-tag">{src.report_number}</span>}
                        {src.year && <span className="source-year">({src.year})</span>}
                        {src.url && (
                          <a href={src.url} target="_blank" rel="noopener noreferrer" className="source-link">
                            ↗ NTRS
                          </a>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* 4. CALCULATION DETAILS CARD (Phase 2 tools) */}
              {msg.calculations && msg.calculations.length > 0 && (
                <div className="calculation-card">
                  <div className="calculation-header">
                    <span>CALCULATION: {msg.calculations[0].calculation.toUpperCase()}</span>
                    <span className="calculation-tool-tag">TOOL: {msg.calculations[0].tool.toUpperCase()}</span>
                  </div>

                  <div className="calc-section">
                    <span className="calc-section-title">INPUTS:</span>
                    <div className="calc-grid">
                      {Object.entries(msg.calculations[0].inputs).map(([k, v]) => (
                        <div key={k} className="calc-item">
                          <span className="calc-label">{k}:</span>
                          <span className="calc-value">{String(v)}</span>
                        </div>
                      ))}
                    </div>
                  </div>

                  <div className="calc-section">
                    <span className="calc-section-title">OUTPUTS:</span>
                    <div className="calc-grid">
                      {Object.entries(msg.calculations[0].results).map(([k, v]) => (
                        <div key={k} className="calc-item">
                          <span className="calc-label">{k}:</span>
                          <span className="calc-value highlight">{String(v)}</span>
                        </div>
                      ))}
                    </div>
                  </div>

                  {msg.verification && (
                    <div className="verification-badge-container">
                      <span className="verification-badge">
                        ✓ Independently verified with SymPy (relative error: {msg.verification.relative_error})
                      </span>
                    </div>
                  )}
                </div>
              )}

              {/* 5. AASI EXPLANATION */}
              <div className="bubble-content">{msg.content}</div>

              {/* 6. ASSUMPTIONS & LIMITATIONS */}
              {((msg.assumptions && msg.assumptions.length > 0) || (msg.limitations && msg.limitations.length > 0)) && (
                <div className="assumptions-block">
                  {msg.assumptions && msg.assumptions.length > 0 && (
                    <div className="assumptions-list">
                      <strong>Assumptions:</strong> {msg.assumptions.join(" ")}
                    </div>
                  )}
                  {msg.limitations && msg.limitations.length > 0 && (
                    <div className="limitations-list">
                      <strong>Limitations:</strong> {msg.limitations.join(" ")}
                    </div>
                  )}
                </div>
              )}
            </div>

            {msg.sender === "user" && (
              <div className="avatar user-avatar" title="User">
                ME
              </div>
            )}
          </div>
        ))}

        {/* Loading Indicator */}
        {isLoading && (
          <div className="thinking-indicator">
            <div className="pulse-spinner" />
            <span>AASI is executing resolution hierarchy, verifying datasets, and reasoning...</span>
          </div>
        )}

        {/* Error Alert */}
        {errorMessage && (
          <div className="error-banner" role="alert">
            <strong>System Telemetry Notice</strong>
            <span>{errorMessage}</span>
          </div>
        )}

        <div ref={messagesEndRef} />
      </section>

      {/* Input Area */}
      <footer className="input-area">
        <div className="input-wrapper">
          <textarea
            ref={textareaRef}
            className="chat-input"
            rows={1}
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask a scientific question, cite NASA/NACA reports, submit flow conditions, or request simulation..."
            disabled={isLoading}
          />
          <div className="input-actions">
            <button
              className="btn-send"
              onClick={() => handleSendMessage()}
              disabled={isLoading || !inputMessage.trim()}
              type="button"
            >
              <span>SEND</span>
              <span>→</span>
            </button>
          </div>
        </div>
        <div className="input-hint">
          <span>Press Enter to send, Shift + Enter for new line</span>
          <span>AASI Phase 4 • Deterministic Resolution Hierarchy • Epistemic Provenance</span>
        </div>
      </footer>

      {/* RESEARCH & SIMULATION DRAWER MODAL */}
      {isResearchOpen && (
        <div className="drawer-overlay" onClick={() => setIsResearchOpen(false)}>
          <div className="research-drawer" onClick={(e) => e.stopPropagation()}>
            <div className="drawer-header">
              <div className="drawer-title-group">
                <h2>SCIENTIFIC KNOWLEDGE, DATASETS & SIMULATION FABRIC</h2>
                <span className="drawer-subtitle">NASA NTRS • Wind Tunnel Databases • Validated CFD • OpenFOAM Fabric</span>
              </div>
              <button className="btn-close-drawer" onClick={() => setIsResearchOpen(false)} type="button">
                ✕
              </button>
            </div>

            <div className="drawer-tabs">
              <button
                className={`drawer-tab-btn ${researchTab === "literature" ? "active" : ""}`}
                onClick={() => setResearchTab("literature")}
                type="button"
              >
                SCIENTIFIC LITERATURE ({docList.length})
              </button>
              <button
                className={`drawer-tab-btn ${researchTab === "datasets" ? "active" : ""}`}
                onClick={() => setResearchTab("datasets")}
                type="button"
              >
                PHYSICAL DATASETS (EXP & CFD)
              </button>
              <button
                className={`drawer-tab-btn ${researchTab === "simulations" ? "active" : ""}`}
                onClick={() => {
                  setResearchTab("simulations");
                  loadSolvers();
                }}
                type="button"
              >
                SIMULATION FABRIC & SOLVERS
              </button>
            </div>

            <div className="drawer-body">
              {/* TAB 1: LITERATURE */}
              {researchTab === "literature" && (
                <div className="literature-pane">
                  {/* Search Bar */}
                  <div className="search-bar-row">
                    <input
                      type="text"
                      className="search-input"
                      placeholder="Search reports, authors, Reynolds, Mach (e.g. 'NACA 0012 drag', 'solar constant')..."
                      value={knowledgeSearchQuery}
                      onChange={(e) => setKnowledgeSearchQuery(e.target.value)}
                      onKeyDown={(e) => e.key === "Enter" && handleKnowledgeSearch()}
                    />
                    <button
                      className="btn-search"
                      onClick={handleKnowledgeSearch}
                      disabled={isSearchingKnowledge}
                      type="button"
                    >
                      {isSearchingKnowledge ? "SEARCHING..." : "SEARCH"}
                    </button>
                  </div>

                  {/* Search Results if any */}
                  {searchResults.length > 0 && (
                    <div className="search-results-section">
                      <h3>SEARCH RESULTS ({searchResults.length})</h3>
                      <div className="results-grid">
                        {searchResults.map((res, rIdx) => (
                          <div key={rIdx} className="result-card">
                            <div className="result-card-header">
                              <span className="source-tag">{res.source}</span>
                              <span className="relevance-score">Score: {res.relevance}</span>
                            </div>
                            <h4 className="result-card-title">{res.title}</h4>
                            <p className="result-snippet">{res.snippet}</p>
                            <div className="result-provenance">
                              <span>Hash: <code>{res.provenance?.content_hash?.substring(0, 16)}...</code></span>
                              {res.url && <a href={res.url} target="_blank" rel="noopener noreferrer">View Source ↗</a>}
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Complete Document Catalog */}
                  <div className="documents-section">
                    <h3>INDEXED TECHNICAL REPORTS ({docList.length})</h3>
                    <div className="docs-table-wrapper">
                      <table className="docs-table">
                        <thead>
                          <tr>
                            <th>REPORT NUMBER</th>
                            <th>TITLE</th>
                            <th>SOURCE</th>
                            <th>DISCIPLINE</th>
                            <th>YEAR</th>
                            <th>ACTIONS</th>
                          </tr>
                        </thead>
                        <tbody>
                          {docList.map((doc) => (
                            <tr key={doc.document_id}>
                              <td className="mono-cell">{doc.report_number || doc.document_id}</td>
                              <td className="title-cell">{doc.title}</td>
                              <td><span className="org-badge">{doc.source}</span></td>
                              <td>{doc.discipline || "Aerospace"}</td>
                              <td>{doc.year || "—"}</td>
                              <td>
                                <button
                                  className="btn-inspect"
                                  onClick={() => handleInspectDoc(doc.document_id)}
                                  type="button"
                                >
                                  PROVENANCE
                                </button>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                </div>
              )}

              {/* TAB 2: DATASETS */}
              {researchTab === "datasets" && (
                <div className="datasets-pane">
                  {/* Condition Query Box */}
                  <div className="condition-query-card">
                    <h3>QUERY PHYSICAL AERODYNAMIC & CFD DATASETS</h3>
                    <p className="query-subtitle">
                      Look up exact verified experimental or CFD data points across flight conditions without fabrication:
                    </p>
                    <div className="condition-inputs-grid">
                      <div className="input-group">
                        <label>GEOMETRY</label>
                        <input
                          type="text"
                          value={geoInput}
                          onChange={(e) => setGeoInput(e.target.value)}
                          placeholder="e.g. NACA 0012"
                        />
                      </div>
                      <div className="input-group">
                        <label>MACH NUMBER</label>
                        <input
                          type="text"
                          value={machInput}
                          onChange={(e) => setMachInput(e.target.value)}
                          placeholder="e.g. 0.15"
                        />
                      </div>
                      <div className="input-group">
                        <label>REYNOLDS NUMBER</label>
                        <input
                          type="text"
                          value={reInput}
                          onChange={(e) => setReInput(e.target.value)}
                          placeholder="e.g. 3000000"
                        />
                      </div>
                      <div className="input-group">
                        <label>ANGLE OF ATTACK (DEG)</label>
                        <input
                          type="text"
                          value={aoaInput}
                          onChange={(e) => setAoaInput(e.target.value)}
                          placeholder="e.g. 4.0"
                        />
                      </div>
                    </div>
                    <button
                      className="btn-query-datasets"
                      onClick={handleDatasetQuery}
                      disabled={isQueryingDataset}
                      type="button"
                    >
                      {isQueryingDataset ? "QUERYING..." : "QUERY DATASETS"}
                    </button>
                  </div>

                  {/* Dataset Matches */}
                  {datasetMatches.length > 0 && (
                    <div className="matched-datasets-section">
                      <h3>VERIFIED DATASET MATCHES ({datasetMatches.length})</h3>
                      {datasetMatches.map((m, mIdx) => (
                        <div key={mIdx} className="dataset-match-item">
                          <div className="match-title-row">
                            <h4>{m.dataset_name}</h4>
                            <span className="validation-pill">{m.validation_status}</span>
                          </div>
                          <p className="match-meta">
                            <strong>Source:</strong> {m.source} • <strong>Citation:</strong> {m.citation}
                          </p>
                          <div className="matched-pts-table">
                            <table>
                              <thead>
                                <tr>
                                  <th>AoA (deg)</th>
                                  <th>C_L (Lift)</th>
                                  <th>C_D (Drag)</th>
                                  <th>C_M (Moment)</th>
                                </tr>
                              </thead>
                              <tbody>
                                {m.matched_points.map((pt: any, pIdx: number) => (
                                  <tr key={pIdx}>
                                    <td>{pt.aoa !== undefined ? pt.aoa : "—"}</td>
                                    <td className="highlight-cell">{pt.cl !== undefined ? pt.cl : "—"}</td>
                                    <td className="highlight-cell">{pt.cd !== undefined ? pt.cd : "—"}</td>
                                    <td>{pt.cm !== undefined ? pt.cm : "—"}</td>
                                  </tr>
                                ))}
                              </tbody>
                            </table>
                          </div>
                          <div className="match-checksum">
                            <span>SHA-256 Checksum: <code>{m.checksum}</code></span>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}

              {/* TAB 3: SIMULATION FABRIC & SOLVERS */}
              {researchTab === "simulations" && (
                <div className="simulations-pane">
                  {/* Security Sandbox Notice */}
                  <div className="sandbox-security-banner">
                    <div className="banner-badge">SECURITY SANDBOX ACTIVE</div>
                    <p>
                      Simulations execute in isolated temporary directories with strict executable allowlists (<code>simpleFoam</code>, <code>blockMesh</code>, <code>SU2_CFD</code>, <code>xfoil</code>). Raw shell input is rejected, timeouts enforced, and output files are cryptographically hashed into reproducible manifests.
                    </p>
                  </div>

                  {/* Solvers Discovery Status */}
                  <div className="solvers-discovery-section">
                    <div className="section-header-row">
                      <h3>DETECTED SCIENTIFIC SOLVERS & RUNTIMES</h3>
                      <button className="btn-refresh-solvers" onClick={loadSolvers} disabled={isLoadingSolvers} type="button">
                        {isLoadingSolvers ? "PROBING..." : "REFRESH ENVIRONMENT"}
                      </button>
                    </div>

                    <div className="solvers-grid">
                      {solversList.map((s) => (
                        <div key={s.solver} className={`solver-card ${s.is_available ? "available" : "unavailable"}`}>
                          <div className="solver-card-header">
                            <span className="solver-name">{s.solver}</span>
                            <span className={`solver-status-tag ${s.is_available ? "online" : "offline"}`}>
                              {s.status}
                            </span>
                          </div>
                          <p className="solver-desc">{s.detection_diagnostic || "Deterministic aerodynamic solver"}</p>
                          <div className="solver-meta-info">
                            <div><strong>Environment:</strong> {s.execution_environment || "host"}</div>
                            <div><strong>Path:</strong> <code>{s.executable_path || "Not detected in PATH"}</code></div>
                            <div><strong>Physics:</strong> {(s.supported_physics || []).join(", ") || "Aerodynamics (2D)"}</div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Interactive Simulation Case Generator */}
                  <div className="simulation-case-generator">
                    <h3>CREATE & VALIDATE SIMULATION CASE (DRY-RUN / VALIDATION)</h3>
                    <p className="generator-subtitle">
                      Configure aerodynamic simulation cases. In DRY_RUN mode, AASI writes authenticated OpenFOAM / SU2 dictionary decks, verifies boundary conditions, and generates reproducible manifests without requiring a live CFD cluster.
                    </p>

                    <div className="generator-form-grid">
                      <div className="input-group">
                        <label>CASE IDENTIFIER</label>
                        <input
                          type="text"
                          value={simCaseId}
                          onChange={(e) => setSimCaseId(e.target.value)}
                          placeholder="e.g. naca0012-simplefoam-subsonic-001"
                        />
                      </div>

                      <div className="input-group">
                        <label>TARGET SOLVER</label>
                        <select value={simSolver} onChange={(e) => setSimSolver(e.target.value)}>
                          <option value="OpenFOAM">OpenFOAM (simpleFoam)</option>
                          <option value="SU2">SU2 (SU2_CFD)</option>
                          <option value="XFOIL">XFOIL (Panel Method)</option>
                          <option value="XFLR5">XFLR5</option>
                        </select>
                      </div>

                      <div className="input-group">
                        <label>GEOMETRY</label>
                        <input
                          type="text"
                          value={simGeometry}
                          onChange={(e) => setSimGeometry(e.target.value)}
                          placeholder="e.g. NACA 0012"
                        />
                      </div>

                      <div className="input-group">
                        <label>MACH NUMBER</label>
                        <input
                          type="text"
                          value={simMach}
                          onChange={(e) => setSimMach(e.target.value)}
                          placeholder="e.g. 0.15"
                        />
                      </div>

                      <div className="input-group">
                        <label>REYNOLDS NUMBER</label>
                        <input
                          type="text"
                          value={simReynolds}
                          onChange={(e) => setSimReynolds(e.target.value)}
                          placeholder="e.g. 3000000"
                        />
                      </div>

                      <div className="input-group">
                        <label>ANGLE OF ATTACK (DEG)</label>
                        <input
                          type="text"
                          value={simAoa}
                          onChange={(e) => setSimAoa(e.target.value)}
                          placeholder="e.g. 4.0"
                        />
                      </div>

                      <div className="input-group">
                        <label>TURBULENCE CLOSURE</label>
                        <select value={simTurbulence} onChange={(e) => setSimTurbulence(e.target.value)}>
                          <option value="k-omega SST">k-omega SST</option>
                          <option value="Spalart-Allmaras">Spalart-Allmaras</option>
                          <option value="k-epsilon">k-epsilon</option>
                          <option value="Inviscid">Inviscid / Euler</option>
                        </select>
                      </div>

                      <div className="input-group">
                        <label>EXECUTION MODE</label>
                        <select value={simRunMode} onChange={(e) => setSimRunMode(e.target.value)}>
                          <option value="DRY_RUN">DRY_RUN (Case Deck & Manifest Only)</option>
                          <option value="VALIDATION_RUN">VALIDATION_RUN (Mesh & Schemes Check)</option>
                          <option value="FULL_RUN">FULL_RUN (Execute Solver)</option>
                        </select>
                      </div>
                    </div>

                    <div className="generator-actions-row">
                      <button
                        className="btn-submit-sim"
                        onClick={handleRunSimulation}
                        disabled={isSubmittingSim}
                        type="button"
                      >
                        {isSubmittingSim ? "GENERATING CASE..." : "GENERATE CASE & VALIDATE"}
                      </button>
                    </div>

                    {simError && (
                      <div className="sim-error-card">
                        <strong>Simulation Error:</strong> {simError}
                      </div>
                    )}

                    {/* Simulation Manifest Output */}
                    {simManifest && (
                      <div className="simulation-manifest-card">
                        <div className="manifest-header-row">
                          <div>
                            <h4>MANIFEST: {simManifest.experiment_id}</h4>
                            <span className="manifest-case-id">Solver: {simManifest.solver} ({simManifest.solver_version || "v2312"}) • Geometry: {simManifest.geometry}</span>
                          </div>
                          <span className="manifest-status-badge">{simManifest.result_status}</span>
                        </div>

                        <div className="manifest-meta-details">
                          <div><strong>Run Mode:</strong> <code>{simManifest.run_mode}</code> • <strong>Epistemic Status:</strong> <span className="epistemic-badge local">{simManifest.epistemic_status}</span></div>
                          <div><strong>Input Hash (SHA-256):</strong> <code>{simManifest.input_checksum}</code></div>
                          {simManifest.output_checksum && (
                            <div><strong>Output Hash:</strong> <code>{simManifest.output_checksum}</code></div>
                          )}
                          <div><strong>Convergence:</strong> {simManifest.is_converged ? "✓ Converged (< 1e-6)" : "Verified Dictionary & Deck Setup (Dry-Run)"}</div>
                        </div>

                        {simManifest.result_files && simManifest.result_files.length > 0 && (
                          <div className="manifest-hashes-section">
                            <h5>GENERATED ARTIFACT FILES ({simManifest.result_files.length})</h5>
                            <div className="hashes-table">
                              <table>
                                <thead>
                                  <tr>
                                    <th>GENERATED ARTIFACT</th>
                                  </tr>
                                </thead>
                                <tbody>
                                  {simManifest.result_files.map((fPath) => (
                                    <tr key={fPath}>
                                      <td className="mono-path">{fPath}</td>
                                    </tr>
                                  ))}
                                </tbody>
                              </table>
                            </div>
                          </div>
                        )}

                        {simManifest.logs && simManifest.logs.length > 0 && (
                          <div className="manifest-log-section">
                            <h5>EXECUTION & VALIDATION LOGS</h5>
                            <pre className="log-code-box">{simManifest.logs.join("\n")}</pre>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>

            {/* Document Detail Modal */}
            {selectedDoc && (
              <div className="doc-detail-modal" onClick={() => setSelectedDoc(null)}>
                <div className="doc-detail-content" onClick={(e) => e.stopPropagation()}>
                  <div className="doc-detail-header">
                    <h3>{selectedDoc.title}</h3>
                    <button className="btn-close-submodal" onClick={() => setSelectedDoc(null)} type="button">
                      ✕
                    </button>
                  </div>
                  <div className="doc-detail-body">
                    <div className="provenance-banner">
                      <h4>CRYPTOGRAPHIC PROVENANCE</h4>
                      <p><strong>Source Organization:</strong> {selectedDoc.provenance.source_organization}</p>
                      <p><strong>Report Number:</strong> {selectedDoc.provenance.report_number || "N/A"}</p>
                      <p><strong>Publication Date:</strong> {selectedDoc.provenance.publication_date || "N/A"}</p>
                      <p><strong>License:</strong> {selectedDoc.provenance.license}</p>
                      <p><strong>SHA-256 Hash:</strong> <code>{selectedDoc.provenance.content_hash}</code></p>
                      {selectedDoc.provenance.source_url && (
                        <p><strong>NTRS Link:</strong> <a href={selectedDoc.provenance.source_url} target="_blank" rel="noopener noreferrer">{selectedDoc.provenance.source_url}</a></p>
                      )}
                    </div>
                    {selectedDoc.abstract && (
                      <div className="doc-abstract-section">
                        <h4>ABSTRACT</h4>
                        <p>{selectedDoc.abstract}</p>
                      </div>
                    )}
                    {selectedDoc.equations && selectedDoc.equations.length > 0 && (
                      <div className="doc-equations-section">
                        <h4>EXTRACTED SCIENTIFIC EQUATIONS ({selectedDoc.equations.length})</h4>
                        {selectedDoc.equations.map((eq: any, eIdx: number) => (
                          <div key={eIdx} className="equation-box">
                            <div className="equation-formula">{eq.latex || eq.equation_text}</div>
                            {eq.surrounding_context && <div className="equation-context">{eq.surrounding_context}</div>}
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </main>
  );
}
