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
  "What does NASA report about NACA 0012 aerodynamic behavior?",
  "What is the drag coefficient of NACA 0012 at Mach 0.3, Re=500000 and AoA=8°?",
  "What is the solar constant outside Earth according to NASA SP-8005?",
  "What is the circular orbital velocity at 500 km altitude around Earth?",
  "For a rocket with Isp = 350 s, initial mass = 10000 kg, final mass = 3000 kg, calculate Δv.",
];

export default function AASIChatApp() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "initial-welcome",
      sender: "assistant",
      content:
        "Greetings. I am AASI (Autonomous Aerospace Scientific Intelligence).\n\n" +
        "In Phase 3, I am grounded in a verified Scientific Knowledge & Dataset Foundation with strict provenance tracking:\n" +
        "• NASA NTRS & historical NACA technical reports\n" +
        "• Wind-tunnel experimental polar databases (NACA 0012)\n" +
        "• OpenFOAM RANS CFD benchmark simulation metadata\n" +
        "• Astropy orbital mechanics, RocketPy propulsion, and SymPy solvers\n\n" +
        "Ask a scientific question, inspect reference datasets, or run engineering calculations.",
      model: "AASI Agent (Phase 3)",
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    },
  ]);
  const [inputMessage, setInputMessage] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [isCheckingHealth, setIsCheckingHealth] = useState(false);

  // Research Drawer State
  const [isResearchOpen, setIsResearchOpen] = useState(false);
  const [researchTab, setResearchTab] = useState<"literature" | "datasets">("literature");
  const [knowledgeSearchQuery, setKnowledgeSearchQuery] = useState("");
  const [docList, setDocList] = useState<DocumentMeta[]>([]);
  const [searchResults, setSearchResults] = useState<any[]>([]);
  const [isSearchingKnowledge, setIsSearchingKnowledge] = useState(false);
  const [selectedDoc, setSelectedDoc] = useState<any | null>(null);

  // Dataset Condition Search State
  const [geoInput, setGeoInput] = useState("NACA 0012");
  const [machInput, setMachInput] = useState("0.3");
  const [reInput, setReInput] = useState("500000");
  const [aoaInput, setAoaInput] = useState("8.0");
  const [datasetMatches, setDatasetMatches] = useState<any[]>([]);
  const [isQueryingDataset, setIsQueryingDataset] = useState(false);

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

  useEffect(() => {
    checkHealth();
    loadDocuments();
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
        model: data.model || health?.configured_model || "AASI Agent",
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
        content: "Session reset. Ready for scientific knowledge inquiries, dataset lookups, and engineering calculations.",
        model: "AASI Agent",
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      },
    ]);
    setErrorMessage(null);
  };

  return (
    <main className="app-container">
      {/* Header */}
      <header className="app-header">
        <div className="header-top">
          <div className="brand-section">
            <span className="logo-badge">PHASE 3</span>
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
              title="Open Scientific Knowledge and Dataset Catalog"
              type="button"
            >
              <span className="pulse-research-icon" />
              <span>RESEARCH CATALOG ({docList.length} DOCS)</span>
            </button>

            {/* Active Tools Badge */}
            <div className="status-badge tools-badge" title="Registered Computational Tools & RAG">
              <span className="status-dot online" />
              <span>FAISS RAG • NASA • ORBIT • ROCKET</span>
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
          Autonomous Aerospace Scientific Intelligence • Grounded in NASA/NACA Technical Archives & Physical Datasets
        </p>
      </header>

      {/* Chat Viewport */}
      <section className="chat-container">
        {/* Quick Prompts */}
        {messages.length <= 1 && (
          <div className="welcome-card">
            <div className="welcome-title">
              <span>Phase 3 Scientific & Engineering Inquiries</span>
            </div>
            <p className="welcome-text">
              Select a benchmark question to evaluate provenance-first scientific RAG or physical dataset retrieval:
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

              {/* 1. VERIFIED PHYSICAL DATASET MATCH (if dataset matched) */}
              {msg.dataset_match && (
                <div className="dataset-match-card">
                  <div className="dataset-match-header">
                    <span className="dataset-badge">
                      {msg.dataset_match.is_experimental ? "EXPERIMENTAL WIND TUNNEL DATA" : "BENCHMARK CFD SIMULATION"}
                    </span>
                    <span className="dataset-status-tag">✓ VALIDATED</span>
                  </div>
                  <div className="dataset-details-row">
                    <strong>{msg.dataset_match.dataset_name}</strong>
                  </div>
                  <div className="dataset-conditions-text">
                    Source: {msg.dataset_match.source} • Citation: {msg.dataset_match.citation}
                  </div>
                  {msg.dataset_match.matched_points && (
                    <div className="matched-points-grid">
                      {msg.dataset_match.matched_points.map((pt: any, pIdx: number) => (
                        <div key={pIdx} className="point-chip">
                          {Object.entries(pt).map(([k, v]) => (
                            <span key={k}><strong>{k}:</strong> {String(v)} </span>
                          ))}
                        </div>
                      ))}
                    </div>
                  )}
                  {msg.dataset_match.uncertainty && (
                    <div className="uncertainty-note">
                      Uncertainty: {Object.entries(msg.dataset_match.uncertainty).map(([k, v]) => `±${v} (${k})`).join(", ")}
                    </div>
                  )}
                </div>
              )}

              {/* 2. CITED SOURCES & PROVENANCE BADGES */}
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

              {/* 3. AASI PROCESS TRACE (if tool executed) */}
              {msg.tool_calls && msg.tool_calls.length > 0 && (
                <div className="tool-trace-block">
                  <div className="tool-trace-header">AASI PROCESS TRACE</div>
                  <ul className="tool-trace-list">
                    {msg.tool_calls[0].trace.map((step, sIdx) => (
                      <li key={sIdx}>
                        <span className="trace-check">✓</span>
                        <span>{step}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* 4. CALCULATION DETAILS CARD (if calculation data present) */}
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
              {(msg.assumptions && msg.assumptions.length > 0 || msg.limitations && msg.limitations.length > 0) && (
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
            <span>AASI is searching knowledge archives, datasets, and reasoning...</span>
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
            placeholder="Ask a scientific question, cite NASA/NACA reports, or submit flight conditions for verified datasets..."
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
          <span>AASI Phase 3 • Provenance-First Scientific RAG • Verified Datasets</span>
        </div>
      </footer>

      {/* RESEARCH DRAWER MODAL */}
      {isResearchOpen && (
        <div className="drawer-overlay" onClick={() => setIsResearchOpen(false)}>
          <div className="research-drawer" onClick={(e) => e.stopPropagation()}>
            <div className="drawer-header">
              <div className="drawer-title-group">
                <h2>SCIENTIFIC KNOWLEDGE & DATASET FOUNDATION</h2>
                <span className="drawer-subtitle">Cryptographic Provenance • NASA NTRS • NACA Historical Reports</span>
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
                PHYSICAL DATASETS (CFD & WIND TUNNEL)
              </button>
            </div>

            <div className="drawer-body">
              {researchTab === "literature" ? (
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
              ) : (
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
                          placeholder="e.g. 0.3"
                        />
                      </div>
                      <div className="input-group">
                        <label>REYNOLDS NUMBER</label>
                        <input
                          type="text"
                          value={reInput}
                          onChange={(e) => setReInput(e.target.value)}
                          placeholder="e.g. 500000"
                        />
                      </div>
                      <div className="input-group">
                        <label>ANGLE OF ATTACK (DEG)</label>
                        <input
                          type="text"
                          value={aoaInput}
                          onChange={(e) => setAoaInput(e.target.value)}
                          placeholder="e.g. 8.0"
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
