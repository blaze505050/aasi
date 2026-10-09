"use client";

import React, { useState } from "react";

export interface ColabExecutionPanelProps {
  jobId: string;
  geometryId: string;
  alphaDeg: number;
  reynolds: number;
  mach: number;
  colabState: string;
  caseHash?: string;
  notebookHash?: string;
  colabLaunchUrl?: string;
  onImportSuccess?: (data: any) => void;
  apiBase?: string;
}

export const ColabExecutionPanel: React.FC<ColabExecutionPanelProps> = ({
  jobId,
  geometryId,
  alphaDeg,
  reynolds,
  mach,
  colabState,
  caseHash,
  notebookHash,
  colabLaunchUrl = "https://colab.research.google.com",
  onImportSuccess,
  apiBase = "http://127.0.0.1:8000",
}) => {
  const [isImporting, setIsImporting] = useState<boolean>(false);
  const [importStatus, setImportStatus] = useState<string | null>(null);
  const [importError, setImportError] = useState<string | null>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      setSelectedFile(e.target.files[0]);
    }
  };

  const handleUploadResults = async () => {
    if (!selectedFile) {
      setImportError("Please select a results.tar.gz file first.");
      return;
    }

    setIsImporting(true);
    setImportError(null);
    setImportStatus("Uploading results archive and auditing cryptographic hashes...");

    try {
      const formData = new FormData();
      formData.append("file", selectedFile);

      const res = await fetch(`${apiBase}/api/compute/jobs/${jobId}/import`, {
        method: "POST",
        body: formData,
      });

      if (res.ok) {
        const data = await res.json();
        setImportStatus("Results imported & cryptographically verified! Physics Gate passed.");
        if (onImportSuccess) onImportSuccess(data);
      } else {
        const err = await res.json();
        setImportError(err.detail || "Failed to verify results archive.");
      }
    } catch (e: any) {
      setImportError(`Connection error: ${e.message}`);
    } finally {
      setIsImporting(false);
    }
  };

  const getStateColor = (state: string) => {
    switch (state) {
      case "RESULTS_VERIFIED":
        return "#10b981";
      case "RESULTS_IMPORTED":
        return "#06b6d4";
      case "COLAB_EXECUTED":
        return "#8b5cf6";
      case "COLAB_BUNDLE_READY":
        return "#f59e0b";
      default:
        return "#94a3b8";
    }
  };

  return (
    <div style={{ background: "#0f172a", border: "1px solid #334155", borderRadius: "8px", padding: "16px" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "10px", borderBottom: "1px solid #334155", paddingBottom: "12px" }}>
        <div>
          <span style={{ fontSize: "0.7rem", textTransform: "uppercase", letterSpacing: "1px", color: "#f59e0b", fontWeight: "bold" }}>
            COMPLIANT REMOTE COMPUTE FABRIC
          </span>
          <h3 style={{ fontSize: "1.1rem", fontWeight: 800, color: "#fff", margin: "2px 0 0 0" }}>
            Google Colab Execution Center
          </h3>
        </div>

        <span style={{
          padding: "4px 10px",
          borderRadius: "6px",
          fontSize: "0.75rem",
          fontWeight: "bold",
          background: "rgba(245, 158, 11, 0.15)",
          border: `1px solid ${getStateColor(colabState)}`,
          color: getStateColor(colabState),
        }}>
          STATE: {colabState}
        </span>
      </div>

      {/* Grid: Job Parameters & Execution Artifacts */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: "14px", marginTop: "14px" }}>
        {/* Parameters */}
        <div style={{ background: "#1e293b", border: "1px solid #334155", borderRadius: "6px", padding: "12px" }}>
          <div style={{ fontSize: "0.75rem", color: "#94a3b8", fontWeight: "bold", marginBottom: "8px" }}>
            📋 STAGED PARAMETERS
          </div>
          <div style={{ fontSize: "0.75rem", color: "#f8fafc", lineHeight: "1.6" }}>
            <div>Job ID: <code>{jobId}</code></div>
            <div>Airfoil Profile: <strong>{geometryId}</strong></div>
            <div>Angle of Attack: <strong>{alphaDeg}°</strong></div>
            <div>Reynolds Number: <strong>{reynolds.toExponential(1)}</strong></div>
            <div>Mach: <strong>{mach}</strong></div>
          </div>
        </div>

        {/* Cryptographic Digests */}
        <div style={{ background: "#1e293b", border: "1px solid #334155", borderRadius: "6px", padding: "12px" }}>
          <div style={{ fontSize: "0.75rem", color: "#10b981", fontWeight: "bold", marginBottom: "8px" }}>
            🛡️ IMMUTABLE ARTIFACT CHECKSUMS
          </div>
          <div style={{ fontSize: "0.7rem", color: "#94a3b8", lineHeight: "1.6", fontFamily: "var(--font-mono, monospace)" }}>
            <div>Case Tarball: <code>{caseHash ? `${caseHash.slice(0, 16)}...` : "data/compute_jobs/case.tar.gz"}</code></div>
            <div>Jupyter Notebook: <code>{notebookHash ? `${notebookHash.slice(0, 16)}...` : "notebook.ipynb staged"}</code></div>
            <div>Compliance: <strong>Zero Browser Scraping</strong></div>
            <div>Terms of Service: <strong>Fully Compliant</strong></div>
          </div>
        </div>
      </div>

      {/* Action Zone: Open in Colab & Submit Results */}
      <div style={{ marginTop: "16px", background: "rgba(30, 41, 59, 0.6)", border: "1px solid #334155", borderRadius: "6px", padding: "14px" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "12px" }}>
          <div>
            <div style={{ fontSize: "0.85rem", fontWeight: "bold", color: "#f8fafc" }}>
              1. Execute Simulation on Google Colab Hardware
            </div>
            <div style={{ fontSize: "0.75rem", color: "#94a3b8", marginTop: "2px" }}>
              One-click package ready. Click below to open Google Colab and run with zero manual command editing.
            </div>
          </div>

          <a
            href={colabLaunchUrl}
            target="_blank"
            rel="noopener noreferrer"
            style={{
              background: "linear-gradient(135deg, #f59e0b, #d97706)",
              color: "#000",
              fontWeight: 800,
              padding: "8px 18px",
              borderRadius: "6px",
              textDecoration: "none",
              fontSize: "0.8rem",
              display: "flex",
              alignItems: "center",
              gap: "6px",
              boxShadow: "0 0 15px rgba(245, 158, 11, 0.3)",
            }}
          >
            <span>🚀</span>
            <span>OPEN / RUN IN COLAB</span>
          </a>
        </div>

        {/* Upload Zone */}
        <div style={{ marginTop: "14px", borderTop: "1px solid #334155", paddingTop: "12px" }}>
          <div style={{ fontSize: "0.85rem", fontWeight: "bold", color: "#f8fafc", marginBottom: "8px" }}>
            2. Import Returned <code>results.tar.gz</code> Archive
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: "10px", flexWrap: "wrap" }}>
            <input
              type="file"
              accept=".tar.gz,.gz,.tar"
              onChange={handleFileChange}
              style={{
                fontSize: "0.75rem",
                color: "#cbd5e1",
                background: "#0f172a",
                border: "1px solid #475569",
                borderRadius: "4px",
                padding: "6px 10px",
              }}
            />
            <button
              type="button"
              onClick={handleUploadResults}
              disabled={isImporting || !selectedFile}
              style={{
                background: isImporting ? "#334155" : "linear-gradient(135deg, #0284c7, #0369a1)",
                color: "#fff",
                border: "none",
                borderRadius: "4px",
                padding: "7px 16px",
                fontSize: "0.75rem",
                fontWeight: "bold",
                cursor: isImporting || !selectedFile ? "not-allowed" : "pointer",
              }}
            >
              {isImporting ? "Verifying Archive..." : "Import & Verify Archive"}
            </button>
          </div>

          {importStatus && (
            <div style={{ marginTop: "8px", fontSize: "0.75rem", color: "#a7f3d0" }}>
              ✓ {importStatus}
            </div>
          )}
          {importError && (
            <div style={{ marginTop: "8px", fontSize: "0.75rem", color: "#fca5a5" }}>
              ❌ {importError}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
