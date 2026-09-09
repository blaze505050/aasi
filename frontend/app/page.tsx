"use client";

import React, { useState, useEffect, useRef } from "react";

interface Message {
  id: string;
  sender: "user" | "assistant";
  content: string;
  model?: string;
  timestamp: string;
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
  "How is specific impulse (Isp) defined in rocketry?",
  "Explain the Tsiolkovsky rocket equation assumptions.",
  "What physical phenomenon defines the Kármán line?",
];

export default function AASIChatApp() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "initial-welcome",
      sender: "assistant",
      content:
        "Greetings. I am AASI, an experimental AI research assistant for aerospace engineering, space science, and related physics disciplines.\n\n" +
        "Please note that I am an experimental reasoning assistant and not an engineering certification authority. " +
        "In this phase, I do not have direct access to external calculation solvers or flight simulation tools. " +
        "How can I assist your technical inquiry today?",
      model: "AASI Agent",
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
        setErrorMessage(`Ollama Runtime Notice: ${data.error}`);
      } else {
        setErrorMessage(null);
      }
    } catch (err: any) {
      setHealth(null);
      setErrorMessage(
        `Cannot connect to AASI backend at ${API_BASE}. Ensure the FastAPI server is running via 'uvicorn backend.main:app --port 8000'.`
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
        model: data.model || health?.configured_model || "Ollama",
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
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
        content:
          "Conversation history cleared. Ready for aerospace research queries and problem formulation.",
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
            <span className="logo-badge">PHASE 1</span>
            <div className="title-group">
              <h1>
                <span className="title-accent">AASI</span>
              </h1>
            </div>
          </div>

          {/* Telemetry Status Indicators */}
          <div className="telemetry-bar">
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
        {/* Aerospace Quick Prompts */}
        {messages.length <= 1 && (
          <div className="welcome-card">
            <div className="welcome-title">
              <span>Quick Aerospace Inquiries</span>
            </div>
            <p className="welcome-text">
              Select a foundational topic below or submit your own engineering problem statement:
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
            <span>AASI is processing inquiry through open-weight model...</span>
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
            placeholder="Ask a technical aerospace, astrodynamics, or propulsion question..."
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
          <span>AASI Phase 1 Prototype • Open-weight Engine</span>
        </div>
      </footer>
    </main>
  );
}
