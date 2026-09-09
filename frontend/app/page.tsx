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

interface Message {
  id: string;
  sender: "user" | "assistant";
  content: string;
  model?: string;
  timestamp: string;
  tool_calls?: ToolCall[];
  calculations?: CalculationData[];
  verification?: VerificationData | null;
}

interface HealthStatus {
  status: string;
  version: string;
  ollama_connected: boolean;
  configured_model: string;
  error?: string | null;
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

const QUICK_PROMPTS = [
  "What is a Hohmann transfer?",
  "What is the circular orbital velocity at 500 km altitude around Earth?",
  "Calculate the Δv required for a Hohmann transfer from a 200 km circular orbit to a 500 km circular orbit around Earth.",
  "For a rocket with Isp = 350 s, initial mass = 10000 kg, final mass = 3000 kg, calculate Δv.",
];

export default function AASIChatApp() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "initial-welcome",
      sender: "assistant",
      content:
        "Greetings. I am AASI, an experimental AI research assistant for aerospace engineering and space science.\n\n" +
        "In Phase 2, I am equipped with verified Python engineering tools for orbital mechanics (Astropy), " +
        "rocket propulsion (RocketPy standard equations), and symbolic verification (SymPy).\n\n" +
        "Ask a conceptual question or submit an engineering problem with parameters to trigger real computational calculations.",
      model: "AASI Agent (Phase 2)",
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    },
  ]);
  const [inputMessage, setInputMessage] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [isCheckingHealth, setIsCheckingHealth] = useState(false);

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

  useEffect(() => {
    checkHealth();
    const interval = setInterval(checkHealth, 15000);
    return () => clearInterval(interval);
  }, []);

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
        content: "Session reset. Ready for aerospace inquiries and engineering calculations.",
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
            <span className="logo-badge">PHASE 2</span>
            <div className="title-group">
              <h1>
                <span className="title-accent">AASI</span>
              </h1>
            </div>
          </div>

          {/* Telemetry Status Indicators */}
          <div className="telemetry-bar">
            {/* Active Tools Badge */}
            <div className="status-badge tools-badge" title="Registered Computational Tools">
              <span className="status-dot online" />
              <span>TOOLS: ORBIT • ROCKET • MATH</span>
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

            {/* Model Badge */}
            {health?.configured_model && (
              <div className="status-badge model-badge">
                <span>MODEL: {health.configured_model}</span>
              </div>
            )}

            {/* Clear Button */}
            <button
              onClick={clearChat}
              className="btn-icon"
              title="Reset conversation session"
              type="button"
            >
              CLEAR
            </button>

            {/* Refresh Diagnostics */}
            <button
              onClick={checkHealth}
              className="btn-icon"
              title="Refresh connection status"
              type="button"
              disabled={isCheckingHealth}
            >
              {isCheckingHealth ? "..." : "REFRESH"}
            </button>
          </div>
        </div>

        <p className="header-subtitle">
          Experimental AI research assistant for aerospace engineering & space science.
        </p>
      </header>

      {/* Chat Viewport */}
      <section className="chat-container">
        {/* Quick Prompts */}
        {messages.length <= 1 && (
          <div className="welcome-card">
            <div className="welcome-title">
              <span>Phase 2 Engineering Inquiries</span>
            </div>
            <p className="welcome-text">
              Test conceptual reasoning or run real numerical solvers with explicit SI units:
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

              {/* 1. AASI PROCESS TRACE (if tool executed) */}
              {msg.tool_calls && msg.tool_calls.length > 0 && (
                <div className="tool-trace-block">
                  <div className="tool-trace-header">AASI PROCESS</div>
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

              {/* 2. CALCULATION DETAILS CARD (if calculation data present) */}
              {msg.calculations && msg.calculations.length > 0 && (
                <div className="calculation-card">
                  <div className="calculation-header">
                    <span>CALCULATION: {msg.calculations[0].calculation.toUpperCase()}</span>
                    <span className="calculation-tool-tag">TOOL: {msg.calculations[0].tool.toUpperCase()}</span>
                  </div>

                  {/* Inputs */}
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

                  {/* Outputs */}
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

                  {/* Assumptions */}
                  {msg.calculations[0].assumptions && msg.calculations[0].assumptions.length > 0 && (
                    <div className="calc-section">
                      <span className="calc-section-title">PHYSICAL ASSUMPTIONS:</span>
                      <ul className="calc-assumptions-list">
                        {msg.calculations[0].assumptions.map((asm, aIdx) => (
                          <li key={aIdx}>• {asm}</li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* Independent SymPy Verification */}
                  {msg.verification && (
                    <div className="verification-badge-container">
                      <span className="verification-badge">
                        ✓ Independently verified with SymPy (relative error: {msg.verification.relative_error})
                      </span>
                    </div>
                  )}
                </div>
              )}

              {/* 3. AASI EXPLANATION */}
              <div className="bubble-content">{msg.content}</div>
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
            <span>AASI is reasoning and executing scientific tools...</span>
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
            placeholder="Ask a technical concept or submit parameters for orbital / rocket calculations..."
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
          <span>AASI Phase 2 • Astropy • RocketPy • SymPy</span>
        </div>
      </footer>
    </main>
  );
}
