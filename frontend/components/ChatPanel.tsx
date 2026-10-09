"use client";

import React, { useState, useRef, useEffect } from "react";

interface ChatMessage {
  id: string;
  sender: "user" | "assistant";
  content: string;
  model?: string;
  timestamp: string;
  tool_calls?: { tool: string; operation: string; status: string }[];
}

interface ChatPanelProps {
  isOpen: boolean;
  onClose: () => void;
  apiBase?: string;
}

export const ChatPanel: React.FC<ChatPanelProps> = ({
  isOpen,
  onClose,
  apiBase = process.env.NEXT_PUBLIC_API_URL || "",
}) => {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: "welcome",
      sender: "assistant",
      content:
        "I'm AASI — your aerospace scientific intelligence assistant. Ask me about aerodynamics, CFD analysis, airfoil characteristics, or any aerospace engineering question.\n\nI can perform calculations, search scientific literature, and explain physical phenomena with epistemic labeling.",
      model: "AASI",
      timestamp: "Online",
    },
  ]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSend = async () => {
    const text = input.trim();
    if (!text || isLoading) return;

    const userMsg: ChatMessage = {
      id: `user-${Date.now()}`,
      sender: "user",
      content: text,
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    };

    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setIsLoading(true);

    try {
      const res = await fetch(`${apiBase}/api/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: text }),
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: "Could not connect to LLM service." }));
        throw new Error(err.detail || "Server error");
      }

      const data = await res.json();

      const assistantMsg: ChatMessage = {
        id: `assistant-${Date.now()}`,
        sender: "assistant",
        content: data.response || "No response received.",
        model: data.model,
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
        tool_calls: data.tool_calls,
      };

      setMessages((prev) => [...prev, assistantMsg]);
    } catch (err: any) {
      const errorMsg: ChatMessage = {
        id: `error-${Date.now()}`,
        sender: "assistant",
        content: err.message || "Connection to AASI backend failed. Ensure the server is running at the configured API endpoint.",
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <>
      {/* Backdrop overlay */}
      <div
        className={`chat-overlay ${isOpen ? "visible" : ""}`}
        onClick={onClose}
      />

      {/* Drawer */}
      <div className={`chat-drawer ${isOpen ? "open" : ""}`}>
        <div className="chat-drawer-header">
          <div>
            <div className="chat-drawer-title">AASI Assistant</div>
            <div style={{ fontSize: "0.62rem", color: "var(--text-muted)", marginTop: "2px" }}>
              Aerospace scientific Q&A with epistemic labeling
            </div>
          </div>
          <button className="chat-drawer-close" onClick={onClose} aria-label="Close chat">
            ✕
          </button>
        </div>

        <div className="chat-messages">
          {messages.map((msg) => (
            <div key={msg.id} className={`chat-msg ${msg.sender}`}>
              <div style={{ whiteSpace: "pre-wrap" }}>{msg.content}</div>
              {msg.tool_calls && msg.tool_calls.length > 0 && (
                <div
                  style={{
                    marginTop: "8px",
                    paddingTop: "8px",
                    borderTop: "1px solid rgba(255,255,255,0.08)",
                    fontSize: "0.65rem",
                    color: "var(--text-muted)",
                  }}
                >
                  <span style={{ fontWeight: 600, fontSize: "0.6rem", textTransform: "uppercase", letterSpacing: "0.05em" }}>
                    Tools used:
                  </span>
                  {msg.tool_calls.map((tc, i) => (
                    <div key={i} style={{ marginTop: "3px", fontFamily: "var(--font-mono)" }}>
                      <span style={{ color: "var(--accent-cyan)" }}>{tc.tool}</span>
                      <span style={{ color: "var(--text-muted)" }}> → {tc.operation}</span>
                      <span style={{ marginLeft: "6px", color: tc.status === "success" ? "var(--status-green)" : "var(--status-red)" }}>
                        {tc.status === "success" ? "✓" : "✗"}
                      </span>
                    </div>
                  ))}
                </div>
              )}
              <div
                style={{
                  marginTop: "6px",
                  fontSize: "0.58rem",
                  color: "var(--text-muted)",
                  opacity: 0.6,
                  textAlign: msg.sender === "user" ? "right" : "left",
                }}
              >
                {msg.timestamp}
                {msg.model && ` · ${msg.model}`}
              </div>
            </div>
          ))}

          {isLoading && (
            <div className="chat-msg assistant" style={{ display: "flex", alignItems: "center", gap: "8px" }}>
              <svg className="animate-spin" width="14" height="14" viewBox="0 0 24 24" fill="none">
                <circle
                  cx="12"
                  cy="12"
                  r="10"
                  stroke="currentColor"
                  strokeWidth="3"
                  strokeDasharray="31.4 31.4"
                  strokeLinecap="round"
                  opacity="0.3"
                />
                <path d="M12 2a10 10 0 0 1 10 10" stroke="var(--accent-cyan)" strokeWidth="3" strokeLinecap="round" />
              </svg>
              <span style={{ fontSize: "0.72rem", color: "var(--text-muted)" }}>Analyzing...</span>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        <div className="chat-input-area">
          <input
            className="chat-input"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask an aerospace question..."
            disabled={isLoading}
          />
          <button
            className="chat-send-btn"
            onClick={handleSend}
            disabled={isLoading || !input.trim()}
          >
            Send
          </button>
        </div>
      </div>
    </>
  );
};
