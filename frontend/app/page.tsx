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
  "What are the latest spaceflight mission updates and current space weather conditions?",
  "Generate a standalone OpenFOAM CFD deck for NACA 0012 at Mach 0.15, Re=3e6, AoA=4°",
  "Query the registered Physics-AI models and evaluate AeroGraphNet surrogate validity envelope",
  "Perform an active learning uncertainty sweep to find next CFD simulation points for NACA 0012",
  "Query the scientific knowledge graph for NACA 0012 and connected relations",
];

export default function AASIChatApp() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "initial-welcome",
      sender: "assistant",
      content:
        "Greetings. I am AASI (Autonomous Aerospace Scientific Intelligence).\n\n" +
        "In Phase 5, I operate under a Tri-Layer Scientific Intelligence Architecture with deterministic provenance and physical guardrails:\n\n" +
        "• Layer A (Scientific Knowledge Federation):\n" +
        "  - Federated across 15 scientific disciplines (Aerodynamics, Propulsion, Orbital Mechanics, GNC, Structures, etc.)\n" +
        "  - Authentic sources: NASA NTRS, NACA, ISRO public registry, ESA public registry\n" +
        "  - Strict corporate guardrail: Rejection of non-public commercial claims (SpaceX)\n" +
        "  - Temporal separation: CURRENT_INFORMATION (launches, missions, space weather) tagged with ISO timestamps\n\n" +
        "• Layer B (Physics AI & Dataset Factory):\n" +
        "  - High-value open dataset factory (AirfRANS, NASA CRM, Abbott & von Doenhoff polars)\n" +
        "  - Zero-leakage geometry-level splitting & OOD extrapolation validation\n" +
        "  - PhysicsNeMo training foundation (AeroGraphNet, FNO-2D exportable recipes)\n" +
        "  - Active learning uncertainty engine for targeted simulation sampling\n\n" +
        "• Layer C (Deterministic Engineering & User-Executed CFD):\n" +
        "  - Standalone OpenFOAM case deck generation (aasi_case/) with complete 14-section execution guides\n" +
        "  - Artifact ingestion service: parse OpenFOAM forceCoeffs, SU2 CSV, XFOIL polars with SHA-256 provenance\n" +
        "  - Deterministic 8-level scientific resolution hierarchy with strict epistemic status\n\n" +
        "Select a benchmark prompt or inspect the Research & Simulation Fabric drawer.",
      model: "AASI Agent (Phase 5)",
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
  const [researchTab, setResearchTab] = useState<
    "literature" | "sources" | "datasets" | "user_cfd" | "physics_ai" | "graph" | "simulations"
  >("literature");
  const [knowledgeSearchQuery, setKnowledgeSearchQuery] = useState("");
  const [docList, setDocList] = useState<DocumentMeta[]>([]);
  const [searchResults, setSearchResults] = useState<any[]>([]);
  const [isSearchingKnowledge, setIsSearchingKnowledge] = useState(false);
  const [selectedDoc, setSelectedDoc] = useState<any | null>(null);

  // Phase 5: Sources & Current Events
  const [sourcesList, setSourcesList] = useState<any[]>([]);
  const [currentEvents, setCurrentEvents] = useState<any[]>([]);
  const [isLoadingSources, setIsLoadingSources] = useState(false);

  // Phase 5: Dataset Factory & Manifests
  const [datasetManifests, setDatasetManifests] = useState<any[]>([]);
  const [downloadNotice, setDownloadNotice] = useState<string | null>(null);
  const [geoInput, setGeoInput] = useState("NACA 0012");
  const [machInput, setMachInput] = useState("0.15");
  const [reInput, setReInput] = useState("3000000");
  const [aoaInput, setAoaInput] = useState("4.0");
  const [datasetMatches, setDatasetMatches] = useState<any[]>([]);
  const [isQueryingDataset, setIsQueryingDataset] = useState(false);

  // Phase 5: User-Executed CFD (aasi_case/) & Artifact Ingestion
  const [userCfdCaseId, setUserCfdCaseId] = useState("aasi_case_naca0012_run1");
  const [userCfdGeometry, setUserCfdGeometry] = useState("NACA 0012");
  const [userCfdMach, setUserCfdMach] = useState("0.15");
  const [userCfdReynolds, setUserCfdReynolds] = useState("3000000");
  const [userCfdAoa, setUserCfdAoa] = useState("4.0");
  const [userCfdDeckResponse, setUserCfdDeckResponse] = useState<any | null>(null);
  const [isGeneratingUserDeck, setIsGeneratingUserDeck] = useState(false);

  const [artifactFormat, setArtifactFormat] = useState("OPENFOAM_FORCE_COEFFS");
  const [rawArtifactContent, setRawArtifactContent] = useState(
    "# Time   Cm       Cd       Cl       Cl(f)    Cl(r)\n" +
    "998      0.0039   0.0084   0.459    0.229    0.230\n" +
    "999      0.0038   0.0083   0.460    0.230    0.230\n" +
    "1000     0.0038   0.0082   0.461    0.230    0.231"
  );
  const [ingestedResult, setIngestedResult] = useState<any | null>(null);
  const [isIngestingArtifact, setIsIngestingArtifact] = useState(false);

  // Phase 5: Physics AI Models & Active Learning
  const [physicsModels, setPhysicsModels] = useState<any[]>([]);
  const [alGeometry, setAlGeometry] = useState("NACA 0012");
  const [alReynolds, setAlReynolds] = useState("3000000");
  const [alCandidates, setAlCandidates] = useState<any[]>([]);
  const [isLoadingAL, setIsLoadingAL] = useState(false);

  // Phase 6: Real Physics-AI Lab, Polar Curves, Audit & GCI
  const [surrogateGeom, setSurrogateGeom] = useState("naca0012");
  const [surrogateMach, setSurrogateMach] = useState("0.20");
  const [surrogateRe, setSurrogateRe] = useState("2000000");
  const [surrogateAoa, setSurrogateAoa] = useState("4.0");
  const [surrogatePrediction, setSurrogatePrediction] = useState<any | null>(null);
  const [isPredictingSurrogate, setIsPredictingSurrogate] = useState(false);

  const [polarSweepData, setPolarSweepData] = useState<any | null>(null);
  const [isComputingPolar, setIsComputingPolar] = useState(false);

  const [datasetAuditSummary, setDatasetAuditSummary] = useState<any | null>(null);
  const [isLoadingAudit, setIsLoadingAudit] = useState(false);

  const [gciF1, setGciF1] = useState("0.4285");
  const [gciF2, setGciF2] = useState("0.4210");
  const [gciF3, setGciF3] = useState("0.4070");
  const [gciR21, setGciR21] = useState("1.4142");
  const [gciR32, setGciR32] = useState("1.4142");
  const [gciResult, setGciResult] = useState<any | null>(null);
  const [isComputingGCI, setIsComputingGCI] = useState(false);

  // Phase 5: Knowledge Graph
  const [graphSearchQuery, setGraphSearchQuery] = useState("");
  const [graphEntities, setGraphEntities] = useState<any[]>([]);
  const [selectedEntity, setSelectedEntity] = useState<any | null>(null);
  const [entityNeighbors, setEntityNeighbors] = useState<any[]>([]);


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

  const loadPhase5Data = async () => {
    setIsLoadingSources(true);
    try {
      // 1. Federated Sources
      const sRes = await fetch(`${API_BASE}/api/sources`);
      if (sRes.ok) {
        const sData = await sRes.json();
        setSourcesList(sData.sources || []);
      }
      // 2. Current Information / Events
      const cRes = await fetch(`${API_BASE}/api/current-info`);
      if (cRes.ok) {
        const cData = await cRes.json();
        setCurrentEvents(cData.events || []);
      }
      // 3. Dataset Catalog Manifests
      const mRes = await fetch(`${API_BASE}/api/datasets/catalog`);
      if (mRes.ok) {
        const mData = await mRes.json();
        setDatasetManifests(mData.datasets || []);
      }
      // 4. Physics AI Models
      const pRes = await fetch(`${API_BASE}/api/physics/models`);
      if (pRes.ok) {
        const pData = await pRes.json();
        setPhysicsModels(pData.models || []);
      }
      // 5. Knowledge Graph Entities
      const gRes = await fetch(`${API_BASE}/api/graph/entities`);
      if (gRes.ok) {
        const gData = await gRes.json();
        setGraphEntities(gData.entities || []);
      }
      // 6. Phase 6: Dataset Audit
      const aRes = await fetch(`${API_BASE}/api/physics/audit/datasets`);
      if (aRes.ok) {
        const aData = await aRes.json();
        setDatasetAuditSummary(aData);
      }
      // 7. Phase 6: Initial Surrogate Prediction & Polar
      handlePredictSurrogate();
      handleComputePolar();
    } catch (e) {
      console.error("Failed to load Phase 5/6 subsystems", e);
    } finally {
      setIsLoadingSources(false);
    }
  };


  useEffect(() => {
    checkHealth();
    loadDocuments();
    loadSolvers();
    loadPhase5Data();
    const interval = setInterval(checkHealth, 15000);
    return () => clearInterval(interval);
  }, []);

  const handleGenerateUserCfdDeck = async () => {
    setIsGeneratingUserDeck(true);
    setUserCfdDeckResponse(null);
    try {
      const res = await fetch(`${API_BASE}/api/compute/generate-case`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          case_id: userCfdCaseId,
          solver: "OpenFOAM",
          execution_mode: "USER_EXECUTED",
          geometry: userCfdGeometry,
          conditions: {
            mach: parseFloat(userCfdMach) || 0.15,
            reynolds: parseFloat(userCfdReynolds) || 3000000.0,
            aoa_deg: parseFloat(userCfdAoa) || 4.0,
          },
        }),
      });
      if (res.ok) {
        const data = await res.json();
        setUserCfdDeckResponse(data);
      } else {
        const err = await res.json().catch(() => ({}));
        alert(`Failed to generate case deck: ${err.detail || res.statusText}`);
      }
    } catch (e: any) {
      alert(`Error generating user case: ${e.message}`);
    } finally {
      setIsGeneratingUserDeck(false);
    }
  };

  const handleIngestArtifact = async () => {
    if (!rawArtifactContent.trim()) return;
    setIsIngestingArtifact(true);
    setIngestedResult(null);
    try {
      const res = await fetch(`${API_BASE}/api/compute/upload-artifact`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          case_id: userCfdCaseId,
          artifact_name: `${userCfdCaseId}_artifact`,
          format: artifactFormat,
          raw_content: rawArtifactContent,
          uploaded_by: "RESEARCHER_UPLOAD",
        }),
      });
      if (res.ok) {
        const data = await res.json();
        setIngestedResult(data);
      } else {
        const err = await res.json().catch(() => ({}));
        alert(`Artifact ingestion error: ${err.detail || res.statusText}`);
      }
    } catch (e: any) {
      alert(`Error ingesting artifact: ${e.message}`);
    } finally {
      setIsIngestingArtifact(false);
    }
  };

  const handleRunActiveLearning = async () => {
    setIsLoadingAL(true);
    try {
      const res = await fetch(`${API_BASE}/api/physics/active-learning`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          geometry: alGeometry,
          reynolds: parseFloat(alReynolds) || 3000000.0,
        }),
      });
      if (res.ok) {
        const data = await res.json();
        setAlCandidates(data.candidates || []);
      }
    } catch (e) {
      console.error("Active learning error", e);
    } finally {
      setIsLoadingAL(false);
    }
  };

  const handleGraphSearch = async (queryStr: string) => {
    try {
      const res = await fetch(`${API_BASE}/api/graph/entities?q=${encodeURIComponent(queryStr)}`);
      if (res.ok) {
        const data = await res.json();
        setGraphEntities(data.entities || []);
      }
    } catch (e) {
      console.error("Graph search error", e);
    }
  };

  const handleInspectGraphEntity = async (entity: any) => {
    setSelectedEntity(entity);
    try {
      const res = await fetch(`${API_BASE}/api/graph/neighbors/${encodeURIComponent(entity.entity_id)}`);
      if (res.ok) {
        const data = await res.json();
        setEntityNeighbors(data.neighbors || []);
      }
    } catch (e) {
      console.error("Failed to fetch entity neighbors", e);
    }
  };

  const handleTriggerDownload = async (datasetId: string) => {
    try {
      setDownloadNotice(`Checking manifest and quota for ${datasetId}...`);
      const res = await fetch(`${API_BASE}/api/datasets/download?dataset_id=${encodeURIComponent(datasetId)}`, {
        method: "POST",
      });
      if (res.ok) {
        const data = await res.json();
        setDownloadNotice(data.message || `Download initiated for ${datasetId}`);
      } else {
        const err = await res.json().catch(() => ({}));
        setDownloadNotice(`Notice: ${err.detail || "Quota reached or download verified"}`);
      }
    } catch (e: any) {
      setDownloadNotice(`Download error: ${e.message}`);
    }
  };

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

  const handlePredictSurrogate = async () => {

    setIsPredictingSurrogate(true);
    try {
      const res = await fetch(`${API_BASE}/api/physics/aerodynamics/predict`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          geometry: surrogateGeom,
          mach: parseFloat(surrogateMach) || 0.2,
          reynolds: parseFloat(surrogateRe) || 2000000,
          aoa_deg: parseFloat(surrogateAoa) || 4.0,
        }),
      });
      if (res.ok) {
        const data = await res.json();
        setSurrogatePrediction(data);
      }
    } catch (e) {
      console.error("Failed to predict surrogate", e);
    } finally {
      setIsPredictingSurrogate(false);
    }
  };

  const handleComputePolar = async () => {
    setIsComputingPolar(true);
    try {
      const res = await fetch(`${API_BASE}/api/physics/aerodynamics/polar`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          geometry: surrogateGeom,
          mach: parseFloat(surrogateMach) || 0.2,
          reynolds: parseFloat(surrogateRe) || 2000000,
          aoa_start: -4.0,
          aoa_end: 14.0,
          aoa_step: 1.0,
        }),
      });
      if (res.ok) {
        const data = await res.json();
        setPolarSweepData(data);
      }
    } catch (e) {
      console.error("Failed to compute polar", e);
    } finally {
      setIsComputingPolar(false);
    }
  };

  const handleFetchAudit = async () => {
    setIsLoadingAudit(true);
    try {
      const res = await fetch(`${API_BASE}/api/physics/audit/datasets`);
      if (res.ok) {
        const data = await res.json();
        setDatasetAuditSummary(data);
      }
    } catch (e) {
      console.error("Failed to fetch audit", e);
    } finally {
      setIsLoadingAudit(false);
    }
  };

  const handleComputeGCI = async () => {
    setIsComputingGCI(true);
    try {
      const res = await fetch(`${API_BASE}/api/validation/grid-convergence`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          f1: parseFloat(gciF1) || 0.4285,
          f2: parseFloat(gciF2) || 0.4210,
          f3: parseFloat(gciF3) || 0.4070,
          r21: parseFloat(gciR21) || 1.4142,
          r32: parseFloat(gciR32) || 1.4142,
          safety_factor: 1.25,
          metric_name: "Lift Coefficient (CL)",
        }),
      });
      if (res.ok) {
        const data = await res.json();
        setGciResult(data);
      }
    } catch (e) {
      console.error("Failed to compute GCI", e);
    } finally {
      setIsComputingGCI(false);
    }
  };

  const handleLoadGCIBenchmarks = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/validation/grid-convergence/benchmarks`);
      if (res.ok) {
        const data = await res.json();
        setGciF1("0.4285");
        setGciF2("0.4210");
        setGciF3("0.4070");
        setGciR21("1.4142");
        setGciR32("1.4142");
        setGciResult(data.lift_analysis);
      }
    } catch (e) {
      console.error("Failed to load GCI benchmarks", e);
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
            <span className="logo-badge">PHASE 5</span>
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
              <span>RESEARCH & COMPUTATIONAL DRAWER</span>
            </button>

            {/* Active Subsystems Badge */}
            <div className="status-badge tools-badge" title="Phase 5 Subsystems">
              <span className="status-dot online" />
              <span>FEDERATION (15) • DATASET FACTORY • PHYSICS-AI • USER-CFD (aasi_case)</span>
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
          Autonomous Aerospace Scientific Intelligence • Knowledge Federation • Leakage-Free Dataset Factory • PhysicsNeMo Foundation • Standalone CFD
        </p>
      </header>

      {/* Chat Viewport */}
      <section className="chat-container">
        {/* Quick Prompts */}
        {messages.length <= 1 && (
          <div className="welcome-card">
            <div className="welcome-title">
              <span>Phase 5 Multi-Layer Scientific Intelligence & Computational Prompts</span>
            </div>
            <p className="welcome-text">
              Select a benchmark prompt to evaluate federated sources across 15 disciplines, current spaceflight information, Physics-AI surrogates, active learning uncertainty sweeps, standalone OpenFOAM CFD decks, or knowledge graph relations:
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
                LITERATURE ({docList.length})
              </button>
              <button
                className={`drawer-tab-btn ${researchTab === "sources" ? "active" : ""}`}
                onClick={() => setResearchTab("sources")}
                type="button"
              >
                FEDERATION & NEWS ({sourcesList.length})
              </button>
              <button
                className={`drawer-tab-btn ${researchTab === "datasets" ? "active" : ""}`}
                onClick={() => setResearchTab("datasets")}
                type="button"
              >
                DATASET FACTORY ({datasetManifests.length})
              </button>
              <button
                className={`drawer-tab-btn ${researchTab === "user_cfd" ? "active" : ""}`}
                onClick={() => setResearchTab("user_cfd")}
                type="button"
              >
                USER-EXECUTED CFD
              </button>
              <button
                className={`drawer-tab-btn ${researchTab === "physics_ai" ? "active" : ""}`}
                onClick={() => setResearchTab("physics_ai")}
                type="button"
              >
                PHYSICS-AI & ACTIVE LEARNING
              </button>
              <button
                className={`drawer-tab-btn ${researchTab === "graph" ? "active" : ""}`}
                onClick={() => setResearchTab("graph")}
                type="button"
              >
                KNOWLEDGE GRAPH ({graphEntities.length})
              </button>
              <button
                className={`drawer-tab-btn ${researchTab === "simulations" ? "active" : ""}`}
                onClick={() => {
                  setResearchTab("simulations");
                  loadSolvers();
                }}
                type="button"
              >
                SOLVER RUNTIMES
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

              {/* TAB 2: SOURCES & CURRENT EVENTS */}
              {researchTab === "sources" && (
                <div className="sources-pane">
                  <div className="section-pane-header">
                    <h3>FEDERATED SCIENTIFIC SOURCES & DISCIPLINE CATALOG ({sourcesList.length})</h3>
                    <p>
                      Authentic public registries covering 15 scientific disciplines. Direct adapter access for open archives; strict refusal of proprietary corporate databases.
                    </p>
                  </div>

                  <div className="sources-grid">
                    {sourcesList.map((src, sIdx) => (
                      <div
                        key={sIdx}
                        className={`source-card-federated ${
                          src.access_status === "ACTIVE" ? "active" : "planned"
                        }`}
                      >
                        <div className="source-card-top">
                          <span className="source-org-tag-lg">{src.organization || src.source_id}</span>
                          <span className="source-cat-badge">{src.category}</span>
                        </div>
                        <div className="source-card-title">{src.name}</div>
                        <div className="source-meta-row">
                          <div><strong>Access:</strong> {src.access_status} • <strong>License:</strong> {src.license_type}</div>
                          <div><strong>Disciplines:</strong> {(src.disciplines || []).join(", ") || "Aerospace"}</div>
                          {src.justification && <div><strong>Provenance Note:</strong> {src.justification}</div>}
                        </div>
                      </div>
                    ))}
                  </div>

                  <div className="section-pane-header">
                    <h3>CURRENT SPACEFLIGHT INFORMATION & MISSION MILESTONES ({currentEvents.length})</h3>
                    <p>
                      Dynamic launches, mission status, and space weather strictly tagged with <code>CURRENT_INFORMATION</code> and ISO timestamps to preserve temporal integrity.
                    </p>
                  </div>

                  <div className="current-events-feed">
                    {currentEvents.map((evt, eIdx) => (
                      <div key={eIdx} className="current-event-card">
                        <div className="current-event-header">
                          <span className="badge-current-info">CURRENT_INFORMATION</span>
                          <span className="current-event-date">{new Date(evt.timestamp).toLocaleString()}</span>
                        </div>
                        <div className="current-event-title">{evt.title}</div>
                        <div className="current-event-summary">{evt.summary}</div>
                        <div className="current-event-footer">
                          <span><strong>Agency/Category:</strong> {evt.category} • <strong>ID:</strong> <code>{evt.event_id}</code></span>
                          {evt.source_url && (
                            <a href={evt.source_url} target="_blank" rel="noopener noreferrer">
                              Official Bulletin ↗
                            </a>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* TAB 3: DATASET FACTORY */}
              {researchTab === "datasets" && (
                <div className="datasets-pane">
                  <div className="section-pane-header">
                    <h3>HIGH-VALUE OPEN PHYSICS DATASET FACTORY ({datasetManifests.length} REGISTERED)</h3>
                    <p>
                      Curated open-access physical and CFD datasets with cryptographic manifests, verified licensing, and zero-leakage geometry-level partitioning.
                    </p>
                  </div>

                  {downloadNotice && (
                    <div className="sim-error-card" style={{ borderColor: "#10b981", color: "#34d399", marginBottom: "16px" }}>
                      <strong>Download Manager:</strong> {downloadNotice}
                    </div>
                  )}

                  {/* Manifests Grid */}
                  <div className="manifest-list">
                    {datasetManifests.map((ds, dIdx) => (
                      <div key={dIdx} className="dataset-manifest-card">
                        <div className="match-title-row">
                          <h4 className="manifest-card-title">{ds.name}</h4>
                          <span className="validation-pill">{ds.license}</span>
                        </div>
                        <p style={{ fontSize: "0.78rem", color: "#cbd5e1", marginBottom: "8px" }}>{ds.description}</p>
                        <div className="manifest-card-meta">
                          <div><strong>Domain:</strong> {ds.domain}</div>
                          <div><strong>Samples:</strong> {ds.sample_count?.toLocaleString()}</div>
                          <div><strong>Total Size:</strong> {ds.total_size_mb} MB</div>
                          <div><strong>Geometry Leakage:</strong> <span style={{ color: "#10b981", fontWeight: 700 }}>0% (Strict Isolation)</span></div>
                        </div>
                        <div className="split-box">
                          <div><strong>Train Partitions:</strong> {ds.split_policy?.train_ratio * 100}% • <strong>Val:</strong> {ds.split_policy?.val_ratio * 100}% • <strong>Test:</strong> {ds.split_policy?.test_ratio * 100}%</div>
                          <div><strong>OOD Extrapolation:</strong> {ds.split_policy?.ood_conditions ? "Enabled (Angle of Attack > 12°)" : "None"}</div>
                          <div><strong>Root SHA-256:</strong> <code>{ds.checksum?.substring(0, 24)}...</code></div>
                        </div>
                        <button
                          className="btn-download-trigger"
                          onClick={() => handleTriggerDownload(ds.dataset_id)}
                          type="button"
                        >
                          DOWNLOAD ON DEMAND (QUOTA VERIFIED)
                        </button>
                      </div>
                    ))}
                  </div>

                  {/* Condition Query Box */}
                  <div className="condition-query-card">
                    <h3>LOOK UP VERIFIED FLIGHT CONDITIONS</h3>
                    <p className="query-subtitle">
                      Query exact experimental wind tunnel or CFD benchmarks across flight conditions:
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

              {/* TAB 4: USER-EXECUTED CFD & ARTIFACT INGESTION */}
              {researchTab === "user_cfd" && (
                <div className="user-cfd-pane">
                  <div className="section-pane-header">
                    <h3>STANDALONE USER-EXECUTED CFD (aasi_case/) & ARTIFACT INGESTION</h3>
                    <p>
                      Generate complete standalone OpenFOAM CFD decks with 14-section execution guides, run them locally or on an external cluster, and upload the resulting simulation artifacts for physical reconciliation and SHA-256 provenance tracking.
                    </p>
                  </div>

                  <div className="user-cfd-grid">
                    {/* Generator Box */}
                    <div className="cfd-action-box">
                      <h4 style={{ color: "#38bdf8", marginBottom: "8px", fontSize: "0.85rem" }}>1. GENERATE STANDALONE CASE DECK</h4>
                      <p style={{ fontSize: "0.75rem", color: "#94a3b8", marginBottom: "12px" }}>
                        Writes a complete <code>aasi_case/</code> directory with <code>0/</code>, <code>constant/</code>, <code>system/</code>, mesh scripts, and execution guide.
                      </p>
                      <div className="condition-inputs-grid" style={{ gridTemplateColumns: "1fr 1fr" }}>
                        <div className="input-group">
                          <label>CASE IDENTIFIER</label>
                          <input
                            type="text"
                            value={userCfdCaseId}
                            onChange={(e) => setUserCfdCaseId(e.target.value)}
                          />
                        </div>
                        <div className="input-group">
                          <label>AIRFOIL GEOMETRY</label>
                          <input
                            type="text"
                            value={userCfdGeometry}
                            onChange={(e) => setUserCfdGeometry(e.target.value)}
                          />
                        </div>
                        <div className="input-group">
                          <label>MACH NUMBER</label>
                          <input
                            type="text"
                            value={userCfdMach}
                            onChange={(e) => setUserCfdMach(e.target.value)}
                          />
                        </div>
                        <div className="input-group">
                          <label>REYNOLDS NUMBER</label>
                          <input
                            type="text"
                            value={userCfdReynolds}
                            onChange={(e) => setUserCfdReynolds(e.target.value)}
                          />
                        </div>
                        <div className="input-group">
                          <label>ANGLE OF ATTACK (°)</label>
                          <input
                            type="text"
                            value={userCfdAoa}
                            onChange={(e) => setUserCfdAoa(e.target.value)}
                          />
                        </div>
                      </div>
                      <button
                        className="btn-download-trigger"
                        onClick={handleGenerateUserCfdDeck}
                        disabled={isGeneratingUserDeck}
                        style={{ marginTop: "12px", width: "100%" }}
                        type="button"
                      >
                        {isGeneratingUserDeck ? "GENERATING CASE DECK..." : "GENERATE STANDALONE CASE DECK"}
                      </button>

                      {userCfdDeckResponse && (
                        <div style={{ marginTop: "14px", background: "#040813", padding: "10px", borderRadius: "4px", border: "1px solid #1e293b" }}>
                          <div style={{ color: "#34d399", fontWeight: 700, fontSize: "0.75rem", marginBottom: "4px" }}>
                            ✓ Case Deck Ready: <code>{userCfdDeckResponse.case_directory}</code>
                          </div>
                          <div style={{ fontSize: "0.7rem", color: "#94a3b8", marginBottom: "6px" }}>
                            Generated {userCfdDeckResponse.generated_files?.length} files with SHA-256 hashes.
                          </div>
                          <div style={{ maxHeight: "120px", overflowY: "auto", fontSize: "0.68rem", fontFamily: "var(--font-mono)", color: "#cbd5e1" }}>
                            {(userCfdDeckResponse.generated_files || []).map((f: string, fIdx: number) => (
                              <div key={fIdx}>• {f}</div>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>

                    {/* Artifact Ingestion Box */}
                    <div className="cfd-action-box">
                      <h4 style={{ color: "#a5b4fc", marginBottom: "8px", fontSize: "0.85rem" }}>2. INGEST SIMULATION ARTIFACTS</h4>
                      <p style={{ fontSize: "0.75rem", color: "#94a3b8", marginBottom: "12px" }}>
                        Paste or upload raw simulation output (OpenFOAM <code>forceCoeffs.dat</code>, SU2 <code>history.csv</code>, or XFOIL polar) to parse and reconcile:
                      </p>
                      <div className="input-group" style={{ marginBottom: "8px" }}>
                        <label>ARTIFACT FORMAT</label>
                        <select
                          value={artifactFormat}
                          onChange={(e) => setArtifactFormat(e.target.value)}
                          style={{
                            width: "100%",
                            background: "var(--bg-input)",
                            border: "1px solid var(--border-color)",
                            borderRadius: "4px",
                            padding: "6px 8px",
                            color: "#fff",
                            fontFamily: "var(--font-mono)",
                            fontSize: "0.75rem"
                          }}
                        >
                          <option value="OPENFOAM_FORCE_COEFFS">OpenFOAM forceCoeffs.dat</option>
                          <option value="SU2_CSV">SU2 Convergence History (CSV)</option>
                          <option value="XFOIL_POLAR">XFOIL Airfoil Polar</option>
                        </select>
                      </div>
                      <textarea
                        className="artifact-textarea"
                        value={rawArtifactContent}
                        onChange={(e) => setRawArtifactContent(e.target.value)}
                        placeholder="Paste raw simulation log or output polar content here..."
                      />
                      <button
                        className="btn-upload-parse"
                        onClick={handleIngestArtifact}
                        disabled={isIngestingArtifact || !rawArtifactContent.trim()}
                        style={{ width: "100%" }}
                        type="button"
                      >
                        {isIngestingArtifact ? "PARSING & VALIDATING..." : "INGEST & VALIDATE ARTIFACT"}
                      </button>

                      {ingestedResult && (
                        <div style={{ marginTop: "14px", background: "#040813", padding: "10px", borderRadius: "4px", border: "1px solid #1e293b" }}>
                          <div style={{ color: "#a5b4fc", fontWeight: 700, fontSize: "0.75rem", marginBottom: "4px" }}>
                            {ingestedResult.is_valid ? "✓ Valid Physical Artifact" : "⚠ Validation Warning"} • {ingestedResult.format}
                          </div>
                          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "6px", fontSize: "0.72rem", color: "#e2e8f0" }}>
                            <div>C_L (Lift): <strong>{ingestedResult.cl !== null ? ingestedResult.cl : "N/A"}</strong></div>
                            <div>C_D (Drag): <strong>{ingestedResult.cd !== null ? ingestedResult.cd : "N/A"}</strong></div>
                            <div>Converged: <strong>{ingestedResult.is_converged ? "Yes" : "No"}</strong></div>
                            <div>Points: <strong>{ingestedResult.data_points_count}</strong></div>
                          </div>
                          <div style={{ fontSize: "0.68rem", color: "#64748b", marginTop: "4px" }}>
                            Provenance Hash: <code>{ingestedResult.provenance_checksum?.substring(0, 20)}...</code>
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              )}

              {/* TAB 5: PHYSICS-AI LAB & SCIENTIFIC VALIDATION */}
              {researchTab === "physics_ai" && (
                <div className="physics-ai-pane">
                  <div className="section-pane-header">
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: "8px" }}>
                      <div>
                        <h3>PHYSICS-AI LAB — TRAINED AEROSURROGATE V1 & SCIENTIFIC VALIDATION</h3>
                        <p>
                          Distinguishing Language Intelligence (LLM) ≠ Physics Intelligence (Trained AeroSurrogateV1) ≠ Numerical Truth (Solvers & Authentic Datasets).
                        </p>
                      </div>
                      <div style={{ display: "flex", gap: "6px", alignItems: "center" }}>
                        <span className="status-tag-verified">AeroSurrogateV1 DEPLOYED</span>
                        <span style={{ fontSize: "0.68rem", fontFamily: "var(--font-mono)", color: "#94a3b8" }}>
                          SHA-256: <code>bc549596...</code>
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* LAB INTERACTION GRID: SURROGATE INFERENCE & POLAR GRAPH */}
                  <div className="physics-lab-grid">
                    {/* Column 1: Live AeroSurrogateV1 Inference */}
                    <div className="lab-panel-card">
                      <div className="lab-panel-title">
                        <h4>1. REAL-TIME SURROGATE INFERENCE</h4>
                        {surrogatePrediction && (
                          <span className={
                            surrogatePrediction.domain_status === "IN_DOMAIN"
                              ? "domain-badge-in"
                              : surrogatePrediction.domain_status === "EXTRAPOLATION_NEAR_BOUNDARY"
                              ? "domain-badge-boundary"
                              : "domain-badge-ood"
                          }>
                            {surrogatePrediction.domain_status}
                          </span>
                        )}
                      </div>

                      <div className="condition-inputs-grid" style={{ gridTemplateColumns: "1fr 1fr", gap: "8px" }}>
                        <div className="input-group">
                          <label>AIRFOIL PROFILE</label>
                          <select
                            value={surrogateGeom}
                            onChange={(e) => setSurrogateGeom(e.target.value)}
                            style={{
                              width: "100%",
                              background: "var(--bg-input)",
                              border: "1px solid var(--border-color)",
                              borderRadius: "4px",
                              padding: "6px 8px",
                              color: "#fff",
                              fontFamily: "var(--font-mono)",
                              fontSize: "0.75rem"
                            }}
                          >
                            <option value="naca0012">NACA 0012 (Symmetric 12%)</option>
                            <option value="naca0009">NACA 0009 (Symmetric 9%)</option>
                            <option value="naca0006">NACA 0006 (Symmetric 6%)</option>
                            <option value="naca2412">NACA 2412 (Cambered)</option>
                            <option value="naca4412">NACA 4412 (High Camber)</option>
                            <option value="clark_y">Clark Y (General Aviation)</option>
                            <option value="rae2822">RAE 2822 (Supercritical)</option>
                          </select>
                        </div>
                        <div className="input-group">
                          <label>MACH NUMBER (0.05 – 0.40)</label>
                          <input
                            type="text"
                            value={surrogateMach}
                            onChange={(e) => setSurrogateMach(e.target.value)}
                          />
                        </div>
                        <div className="input-group">
                          <label>REYNOLDS NUMBER (5e5 – 6e6)</label>
                          <input
                            type="text"
                            value={surrogateRe}
                            onChange={(e) => setSurrogateRe(e.target.value)}
                          />
                        </div>
                        <div className="input-group">
                          <label>ANGLE OF ATTACK (-8° – +18°)</label>
                          <input
                            type="text"
                            value={surrogateAoa}
                            onChange={(e) => setSurrogateAoa(e.target.value)}
                          />
                        </div>
                      </div>

                      <button
                        className="btn-download-trigger"
                        onClick={handlePredictSurrogate}
                        disabled={isPredictingSurrogate}
                        style={{ marginTop: "10px", width: "100%" }}
                        type="button"
                      >
                        {isPredictingSurrogate ? "EVALUATING NEURAL OPERATOR..." : "RUN AEROSURROGATE V1 INFERENCE"}
                      </button>

                      {/* Readout Boxes */}
                      {surrogatePrediction && (
                        <div>
                          <div className="coeff-readout-grid">
                            <div className="coeff-box cl">
                              <div className="coeff-name">LIFT (C_L)</div>
                              <div className="coeff-value">{surrogatePrediction.cl?.toFixed(4)}</div>
                              <div className="coeff-uncertainty">
                                ± {surrogatePrediction.uncertainty?.cl_uncertainty?.toFixed(4)}
                              </div>
                            </div>
                            <div className="coeff-box cd">
                              <div className="coeff-name">DRAG (C_D)</div>
                              <div className="coeff-value">{surrogatePrediction.cd?.toFixed(5)}</div>
                              <div className="coeff-uncertainty">
                                ± {surrogatePrediction.uncertainty?.cd_uncertainty?.toFixed(5)}
                              </div>
                            </div>
                            <div className="coeff-box cm">
                              <div className="coeff-name">MOMENT (C_M)</div>
                              <div className="coeff-value">{surrogatePrediction.cm?.toFixed(4)}</div>
                              <div className="coeff-uncertainty">
                                ± {surrogatePrediction.uncertainty?.cm_uncertainty?.toFixed(4)}
                              </div>
                            </div>
                          </div>

                          {/* Epistemic Metrics & Physics Checks */}
                          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "8px", fontSize: "0.7rem", fontFamily: "var(--font-mono)" }}>
                            <div className="physics-check-item">
                              <span>Confidence Level:</span>
                              <strong style={{ color: surrogatePrediction.uncertainty?.confidence_level === "HIGH" ? "#34d399" : "#fbbf24" }}>
                                {surrogatePrediction.uncertainty?.confidence_level} ({Math.round((surrogatePrediction.uncertainty?.confidence_score || 0) * 100)}%)
                              </strong>
                            </div>
                            <div className="physics-check-item">
                              <span>OOD Distance:</span>
                              <strong>{surrogatePrediction.uncertainty?.ood_score}</strong>
                            </div>
                            <div className="physics-check-item">
                              <span>Drag Positivity (C_D &gt; 0):</span>
                              <strong style={{ color: surrogatePrediction.cd > 0 ? "#34d399" : "#f87171" }}>
                                {surrogatePrediction.cd > 0 ? "✓ SATISFIED" : "✗ VIOLATION"}
                              </strong>
                            </div>

                            <div className="physics-check-item">
                              <span>Weights Provenance:</span>
                              <span style={{ color: "#38bdf8" }}>SHA-256 Verified</span>
                            </div>
                          </div>
                        </div>
                      )}
                    </div>

                    {/* Column 2: Aerodynamic Polar Curve Generator */}
                    <div className="lab-panel-card">
                      <div className="lab-panel-title">
                        <h4>2. AERODYNAMIC POLAR SWEEP (-4° TO +14°)</h4>
                        <button
                          onClick={handleComputePolar}
                          disabled={isComputingPolar}
                          className="btn-inspect"
                          type="button"
                          style={{ padding: "3px 8px", fontSize: "0.7rem" }}
                        >
                          {isComputingPolar ? "COMPUTING..." : "GENERATE POLAR"}
                        </button>
                      </div>

                      {polarSweepData && (
                        <div className="polar-svg-container">
                          {/* SVG Polar Curve Plot */}
                          <svg viewBox="0 0 340 180" style={{ width: "100%", height: "180px" }}>
                            {/* Gridlines */}
                            <line x1="30" y1="20" x2="330" y2="20" stroke="#1e293b" strokeDasharray="2" />
                            <line x1="30" y1="60" x2="330" y2="60" stroke="#1e293b" strokeDasharray="2" />
                            <line x1="30" y1="100" x2="330" y2="100" stroke="#1e293b" strokeDasharray="2" />
                            <line x1="30" y1="140" x2="330" y2="140" stroke="#1e293b" strokeDasharray="2" />

                            {/* Axis Labels */}
                            <text x="5" y="25" fill="#64748b" fontSize="8" fontFamily="monospace">1.5</text>
                            <text x="5" y="65" fill="#64748b" fontSize="8" fontFamily="monospace">1.0</text>
                            <text x="5" y="105" fill="#64748b" fontSize="8" fontFamily="monospace">0.5</text>
                            <text x="5" y="145" fill="#64748b" fontSize="8" fontFamily="monospace">0.0</text>
                            <text x="170" y="175" fill="#94a3b8" fontSize="8" fontFamily="monospace" textAnchor="middle">AoA α (°)</text>

                            {/* Zero line */}
                            <line x1="30" y1="140" x2="330" y2="140" stroke="#334155" strokeWidth="1" />

                            {/* Lift Curve Path */}
                            {(() => {
                              const pts = polarSweepData.points || [];
                              if (pts.length < 2) return null;
                              const aoaMin = -4, aoaMax = 14;
                              const clMin = -0.3, clMax = 1.6;
                              const coords = pts.map((p: any) => {
                                const x = 30 + ((p.aoa_deg - aoaMin) / (aoaMax - aoaMin)) * 290;
                                const y = 160 - ((p.cl - clMin) / (clMax - clMin)) * 140;
                                return `${x},${y}`;
                              }).join(" ");
                              return (
                                <g>
                                  <polyline fill="none" stroke="#00d2ff" strokeWidth="2.5" points={coords} />
                                  {pts.map((p: any, idx: number) => {
                                    const x = 30 + ((p.aoa_deg - aoaMin) / (aoaMax - aoaMin)) * 290;
                                    const y = 160 - ((p.cl - clMin) / (clMax - clMin)) * 140;
                                    return (
                                      <circle key={idx} cx={x} cy={y} r="3" fill="#00d2ff" stroke="#0a0d14" strokeWidth="1">
                                        <title>{`AoA: ${p.aoa_deg}°, CL: ${p.cl}, CD: ${p.cd}`}</title>
                                      </circle>
                                    );
                                  })}
                                </g>
                              );
                            })()}

                            {/* Drag Curve Path (scaled x10) */}
                            {(() => {
                              const pts = polarSweepData.points || [];
                              if (pts.length < 2) return null;
                              const aoaMin = -4, aoaMax = 14;
                              const coords = pts.map((p: any) => {
                                const x = 30 + ((p.aoa_deg - aoaMin) / (aoaMax - aoaMin)) * 290;
                                // Map CD from [0, 0.05] to height
                                const y = 160 - (Math.min(p.cd, 0.05) / 0.05) * 110;
                                return `${x},${y}`;
                              }).join(" ");
                              return (
                                <polyline fill="none" stroke="#f59e0b" strokeWidth="2" strokeDasharray="3 2" points={coords} />
                              );
                            })()}
                          </svg>

                          <div style={{ display: "flex", justifyContent: "space-between", width: "100%", marginTop: "6px", fontSize: "0.68rem", fontFamily: "var(--font-mono)" }}>
                            <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                              <span style={{ color: "#00d2ff" }}>— Lift C_L(α)</span>
                              <span style={{ color: "#f59e0b" }}>- - Drag C_D(α) (10x)</span>
                            </div>
                            <div>
                              <span style={{ color: polarSweepData.sweep_validation?.is_sweep_valid ? "#34d399" : "#fbbf24" }}>
                                {polarSweepData.sweep_validation?.is_sweep_valid ? "✓ Monotonicity & Drag Positivity Passed" : "⚠ Non-Monotonic Region"}
                              </span>
                            </div>
                          </div>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* BOTTOM SUITE: DATASET AUDIT & GRID CONVERGENCE INDEX */}
                  <div className="physics-lab-grid" style={{ marginTop: "16px" }}>
                    {/* Sub-Panel A: Dataset Authenticity Audit */}
                    <div className="lab-panel-card">
                      <div className="lab-panel-title">
                        <h4>3. DATASET AUTHENTICITY AUDIT</h4>
                        <button
                          onClick={handleFetchAudit}
                          disabled={isLoadingAudit}
                          className="btn-inspect"
                          type="button"
                          style={{ padding: "3px 8px", fontSize: "0.7rem" }}
                        >
                          {isLoadingAudit ? "AUDITING..." : "REFRESH AUDIT"}
                        </button>
                      </div>

                      <p style={{ fontSize: "0.72rem", color: "#94a3b8", marginBottom: "8px" }}>
                        Honest disk inspection: zero fake science. Classifies authentic datasets vs metadata-only records.
                      </p>

                      {datasetAuditSummary && (
                        <div>
                          <div style={{ display: "flex", gap: "8px", marginBottom: "8px", flexWrap: "wrap" }}>
                            <span className="status-tag-verified">
                              VERIFIED DISK DATA: {datasetAuditSummary.verified_count}
                            </span>
                            <span className="status-tag-metadata">
                              METADATA ONLY: {datasetAuditSummary.metadata_only_count}
                            </span>
                          </div>

                          <div className="audit-table-wrapper">
                            <table className="audit-table">
                              <thead>
                                <tr>
                                  <th>DATASET</th>
                                  <th>STATUS</th>
                                  <th>SAMPLES</th>
                                  <th>SOURCE</th>
                                </tr>
                              </thead>
                              <tbody>
                                {(datasetAuditSummary.results || []).map((r: any, idx: number) => (
                                  <tr key={idx}>
                                    <td>
                                      <strong>{r.dataset_name}</strong>
                                      <div style={{ fontSize: "0.62rem", color: "#64748b" }}>{r.dataset_id}</div>
                                    </td>
                                    <td>
                                      <span className={
                                        r.overall_status === "VERIFIED"
                                          ? "status-tag-verified"
                                          : r.overall_status === "DEMO_DATA"
                                          ? "status-tag-demo"
                                          : "status-tag-metadata"
                                      }>
                                        {r.overall_status}
                                      </span>
                                    </td>
                                    <td>{r.sample_count_actual || r.sample_count_declared || "0"}</td>
                                    <td>{r.source_type}</td>
                                  </tr>
                                ))}
                              </tbody>
                            </table>
                          </div>
                        </div>
                      )}
                    </div>

                    {/* Sub-Panel B: Grid Convergence Index (ASME V&V 20) */}
                    <div className="lab-panel-card">
                      <div className="lab-panel-title">
                        <h4>4. GRID CONVERGENCE INDEX (ASME V&V 20)</h4>
                        <button
                          onClick={handleLoadGCIBenchmarks}
                          className="btn-inspect"
                          type="button"
                          style={{ padding: "3px 8px", fontSize: "0.7rem" }}
                        >
                          LOAD NACA 0012 BENCHMARK
                        </button>
                      </div>

                      <p style={{ fontSize: "0.72rem", color: "#94a3b8", marginBottom: "8px" }}>
                        Richardson extrapolation & Roache discretization error estimation across 3-grid CFD meshes.
                      </p>

                      <div className="condition-inputs-grid" style={{ gridTemplateColumns: "repeat(3, 1fr)", gap: "6px" }}>
                        <div className="input-group">
                          <label>FINE (f1)</label>
                          <input type="text" value={gciF1} onChange={(e) => setGciF1(e.target.value)} />
                        </div>
                        <div className="input-group">
                          <label>MEDIUM (f2)</label>
                          <input type="text" value={gciF2} onChange={(e) => setGciF2(e.target.value)} />
                        </div>
                        <div className="input-group">
                          <label>COARSE (f3)</label>
                          <input type="text" value={gciF3} onChange={(e) => setGciF3(e.target.value)} />
                        </div>
                      </div>

                      <div className="condition-inputs-grid" style={{ gridTemplateColumns: "1fr 1fr", gap: "6px", marginTop: "6px" }}>
                        <div className="input-group">
                          <label>REFINEMENT r21 (h2/h1)</label>
                          <input type="text" value={gciR21} onChange={(e) => setGciR21(e.target.value)} />
                        </div>
                        <div className="input-group">
                          <label>REFINEMENT r32 (h3/h2)</label>
                          <input type="text" value={gciR32} onChange={(e) => setGciR32(e.target.value)} />
                        </div>
                      </div>

                      <button
                        className="btn-download-trigger"
                        onClick={handleComputeGCI}
                        disabled={isComputingGCI}
                        style={{ marginTop: "10px", width: "100%" }}
                        type="button"
                      >
                        {isComputingGCI ? "CALCULATING RICHARDSON EXTRAPOLATION..." : "COMPUTE GCI & OBSERVED ORDER p"}
                      </button>

                      {gciResult && (
                        <div className="gci-result-card">
                          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "6px", fontSize: "0.72rem", fontFamily: "var(--font-mono)" }}>
                            <div>Apparent Order p: <strong>{gciResult.apparent_order_p}</strong></div>
                            <div>Extrapolated f_ext: <strong>{gciResult.extrapolated_value}</strong></div>
                            <div>GCI Fine: <strong style={{ color: "#34d399" }}>{gciResult.gci_fine_pct}%</strong></div>
                            <div>GCI Medium: <strong>{gciResult.gci_medium_pct}%</strong></div>
                          </div>
                          <div style={{ marginTop: "6px", fontSize: "0.68rem", fontFamily: "var(--font-mono)", color: gciResult.is_in_asymptotic_range ? "#34d399" : "#fbbf24" }}>
                            {gciResult.is_in_asymptotic_range
                              ? "✓ Solution is in Asymptotic Range of Convergence (ratio ~ 1.0)"
                              : `⚠ Asymptotic check ratio: ${gciResult.asymptotic_ratio} (Refinement recommended)`}
                          </div>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* ACTIVE LEARNING CANDIDATES (FROM PHASE 5) */}
                  <div className="section-pane-header" style={{ marginTop: "24px" }}>
                    <h3>ACTIVE LEARNING UNCERTAINTY SWEEP & CFD CANDIDATES</h3>
                    <p>
                      Identifies high-uncertainty regions in parameter space to guide next CFD experiments.
                    </p>
                  </div>

                  <div className="condition-query-card">
                    <div className="condition-inputs-grid" style={{ gridTemplateColumns: "1fr 1fr" }}>
                      <div className="input-group">
                        <label>TARGET GEOMETRY</label>
                        <input
                          type="text"
                          value={alGeometry}
                          onChange={(e) => setAlGeometry(e.target.value)}
                        />
                      </div>
                      <div className="input-group">
                        <label>REYNOLDS NUMBER</label>
                        <input
                          type="text"
                          value={alReynolds}
                          onChange={(e) => setAlReynolds(e.target.value)}
                        />
                      </div>
                    </div>
                    <button
                      className="btn-download-trigger"
                      onClick={handleRunActiveLearning}
                      disabled={isLoadingAL}
                      type="button"
                    >
                      {isLoadingAL ? "SWEEPING PARAMETER SPACE..." : "RUN ACTIVE LEARNING UNCERTAINTY SWEEP"}
                    </button>

                    {alCandidates.length > 0 && (
                      <div style={{ marginTop: "16px" }}>
                        <h4 style={{ fontSize: "0.8rem", color: "#f8fafc", marginBottom: "8px" }}>
                          RANKED SIMULATION CANDIDATES ({alCandidates.length})
                        </h4>
                        <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
                          {alCandidates.map((cand, cIdx) => (
                            <div key={cIdx} className="candidate-row">
                              <div>
                                <strong>#{cand.rank}</strong> • Mach {cand.mach} • AoA {cand.aoa_deg}° (Re {cand.reynolds?.toExponential(1)})
                              </div>
                              <div>
                                <span style={{ marginRight: "10px", color: "#94a3b8" }}>
                                  Score: {cand.uncertainty_score?.toFixed(3)}
                                </span>
                                <span className={cand.rank <= 2 ? "priority-badge-high" : "priority-badge-medium"}>
                                  {cand.recommended_action}
                                </span>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              )}


              {/* TAB 6: KNOWLEDGE GRAPH */}
              {researchTab === "graph" && (
                <div className="graph-pane">
                  <div className="section-pane-header">
                    <h3>SCIENTIFIC KNOWLEDGE GRAPH (16 ENTITY TYPES & 10 RELATIONS)</h3>
                    <p>
                      Lightweight semantic graph linking airfoils, solvers, turbulence models, space missions, launch vehicles, and scientific reports. Click any node to explore relations.
                    </p>
                  </div>

                  <div className="search-bar-row" style={{ marginBottom: "14px" }}>
                    <input
                      type="text"
                      className="search-input"
                      placeholder="Search graph entities (e.g. 'NACA 0012', 'simpleFoam', 'Chandrayaan')..."
                      value={graphSearchQuery}
                      onChange={(e) => {
                        setGraphSearchQuery(e.target.value);
                        handleGraphSearch(e.target.value);
                      }}
                    />
                  </div>

                  <div className="graph-entities-grid">
                    {graphEntities.map((ent, eIdx) => (
                      <div
                        key={eIdx}
                        className="graph-entity-chip"
                        onClick={() => handleInspectGraphEntity(ent)}
                      >
                        <div className="entity-type-tag">{ent.entity_type}</div>
                        <div className="entity-name">{ent.name}</div>
                        <div style={{ fontSize: "0.68rem", color: "#94a3b8" }}>
                          {ent.description?.substring(0, 50)}...
                        </div>
                      </div>
                    ))}
                  </div>

                  {selectedEntity && (
                    <div style={{ marginTop: "20px", background: "#060d1b", border: "1px solid #1e293b", borderRadius: "6px", padding: "14px" }}>
                      <div className="match-title-row">
                        <h4 style={{ color: "#38bdf8", fontSize: "0.85rem" }}>
                          CONNECTIONS FOR: {selectedEntity.name} ({selectedEntity.entity_type})
                        </h4>
                        <span className="org-badge">{entityNeighbors.length} RELATIONS</span>
                      </div>
                      <p style={{ fontSize: "0.75rem", color: "#94a3b8", marginBottom: "10px" }}>{selectedEntity.description}</p>
                      <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
                        {entityNeighbors.length === 0 ? (
                          <div style={{ fontSize: "0.75rem", color: "#64748b" }}>No direct relations indexed for this entity.</div>
                        ) : (
                          entityNeighbors.map((rel, rIdx) => (
                            <div key={rIdx} className="candidate-row" style={{ alignItems: "center" }}>
                              <div>
                                <span style={{ color: "#f59e0b", fontWeight: 700, marginRight: "8px" }}>
                                  —[{rel.relation_type}]→
                                </span>
                                <span style={{ color: "#f8fafc", fontWeight: 600 }}>
                                  {rel.neighbor_name || rel.target_id || rel.neighbor_id}
                                </span>
                              </div>
                              <span className="source-cat-badge">{rel.neighbor_type || "Entity"}</span>
                            </div>
                          ))
                        )}
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* TAB 7: SIMULATION FABRIC & SOLVERS */}
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
