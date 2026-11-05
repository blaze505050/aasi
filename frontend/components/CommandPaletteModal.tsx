"use client";

import React, { useState, useEffect, useRef } from "react";
import {
  Search,
  Compass,
  Zap,
  Layers,
  Database,
  Brain,
  Cpu,
  Sliders,
  FileText,
  ShieldAlert,
  ArrowRight,
  Command,
} from "lucide-react";

export interface CommandItem {
  id: string;
  category: "Workspaces" | "Inquiries" | "Benchmarks" | "Actions";
  title: string;
  description: string;
  badge?: string;
  icon: React.ReactNode;
  action: () => void;
}

interface CommandPaletteModalProps {
  isOpen: boolean;
  onClose: () => void;
  commands: CommandItem[];
}

export const CommandPaletteModal: React.FC<CommandPaletteModalProps> = ({
  isOpen,
  onClose,
  commands,
}) => {
  const [search, setSearch] = useState("");
  const [selectedIndex, setSelectedIndex] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (isOpen) {
      setSearch("");
      setSelectedIndex(0);
      setTimeout(() => inputRef.current?.focus(), 50);
    }
  }, [isOpen]);

  const filteredCommands = commands.filter((cmd) => {
    const q = search.toLowerCase();
    return (
      cmd.title.toLowerCase().includes(q) ||
      cmd.description.toLowerCase().includes(q) ||
      cmd.category.toLowerCase().includes(q)
    );
  });

  useEffect(() => {
    setSelectedIndex(0);
  }, [search]);

  // Keyboard navigation
  useEffect(() => {
    if (!isOpen) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        e.preventDefault();
        onClose();
      } else if (e.key === "ArrowDown") {
        e.preventDefault();
        setSelectedIndex((prev) =>
          prev < filteredCommands.length - 1 ? prev + 1 : 0
        );
      } else if (e.key === "ArrowUp") {
        e.preventDefault();
        setSelectedIndex((prev) =>
          prev > 0 ? prev - 1 : filteredCommands.length - 1
        );
      } else if (e.key === "Enter") {
        e.preventDefault();
        if (filteredCommands[selectedIndex]) {
          filteredCommands[selectedIndex].action();
          onClose();
        }
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, filteredCommands, selectedIndex, onClose]);

  if (!isOpen) return null;

  return (
    <div
      role="dialog"
      aria-modal="true"
      style={{
        position: "fixed",
        inset: 0,
        zIndex: 9999,
        display: "flex",
        alignItems: "flex-start",
        justifyContent: "center",
        paddingTop: "12vh",
        background: "rgba(3, 7, 18, 0.72)",
        backdropFilter: "blur(18px) saturate(180%)",
        WebkitBackdropFilter: "blur(18px) saturate(180%)",
        animation: "paletteFadeIn 180ms cubic-bezier(0.16, 1, 0.3, 1)",
      }}
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div
        style={{
          width: "100%",
          maxWidth: "680px",
          background: "var(--bg-card, #ffffff)",
          border: "1px solid var(--border-color, #e2e8f0)",
          borderRadius: "12px",
          boxShadow:
            "0 24px 70px rgba(0, 0, 0, 0.15), inset 0 1px 0 rgba(255, 255, 255, 0.5)",
          overflow: "hidden",
          display: "flex",
          flexDirection: "column",
        }}
      >
        {/* Input Bar */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: "12px",
            padding: "16px 20px",
            borderBottom: "1px solid var(--border-color, #e2e8f0)",
          }}
        >
          <Search size={20} color="var(--accent-gold, #d97706)" style={{ flexShrink: 0 }} />
          <input
            ref={inputRef}
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Type a command, query, or airfoil benchmark (e.g. NACA 0012, RAE 2822)..."
            style={{
              flex: 1,
              background: "transparent",
              border: "none",
              outline: "none",
              color: "var(--text-primary, #0f172a)",
              fontSize: "1rem",
              fontFamily: "var(--font-sans)",
            }}
          />
          <span
            style={{
              padding: "3px 8px",
              borderRadius: "6px",
              background: "var(--bg-secondary, #f1f5f9)",
              border: "1px solid var(--border-color, #e2e8f0)",
              color: "var(--text-secondary, #64748b)",
              fontSize: "0.72rem",
              fontFamily: "var(--font-mono)",
            }}
          >
            ESC
          </span>
        </div>

        {/* Results List */}
        <div
          style={{
            maxHeight: "380px",
            overflowY: "auto",
            padding: "10px",
            display: "flex",
            flexDirection: "column",
            gap: "4px",
          }}
        >
          {filteredCommands.length === 0 ? (
            <div
              style={{
                padding: "36px 20px",
                textAlign: "center",
                color: "#64748b",
                fontSize: "0.88rem",
              }}
            >
              No matching commands or benchmarks found.
            </div>
          ) : (
            filteredCommands.map((cmd, idx) => {
              const isSelected = idx === selectedIndex;
              return (
                <div
                  key={cmd.id}
                  onClick={() => {
                    cmd.action();
                    onClose();
                  }}
                  onMouseEnter={() => setSelectedIndex(idx)}
                  style={{
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "space-between",
                    padding: "10px 14px",
                    borderRadius: "10px",
                    cursor: "pointer",
                    background: isSelected
                      ? "rgba(245, 158, 11, 0.12)"
                      : "transparent",
                    border: isSelected
                      ? "1px solid rgba(245, 158, 11, 0.35)"
                      : "1px solid transparent",
                    transition: "all 120ms ease",
                  }}
                >
                  <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
                    <div
                      style={{
                        width: "32px",
                        height: "32px",
                        borderRadius: "6px",
                        background: isSelected
                          ? "rgba(217, 119, 6, 0.18)"
                          : "rgba(0, 0, 0, 0.04)",
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center",
                        color: isSelected ? "var(--accent-gold, #d97706)" : "var(--text-secondary, #64748b)",
                      }}
                    >
                      {cmd.icon}
                    </div>
                    <div>
                      <div
                        style={{
                          color: "var(--text-primary, #0f172a)",
                          fontSize: "0.88rem",
                          fontWeight: 600,
                        }}
                      >
                        {cmd.title}
                      </div>
                      <div
                        style={{
                          color: "var(--text-secondary, #475569)",
                          fontSize: "0.76rem",
                        }}
                      >
                        {cmd.description}
                      </div>
                    </div>
                  </div>

                  <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                    {cmd.badge && (
                      <span
                        style={{
                          padding: "2px 7px",
                          borderRadius: "5px",
                          background: "rgba(2, 132, 199, 0.1)",
                          color: "var(--accent-cyan, #0284c7)",
                          fontSize: "0.68rem",
                          fontFamily: "var(--font-mono)",
                        }}
                      >
                        {cmd.badge}
                      </span>
                    )}
                    <ArrowRight
                      size={14}
                      color={isSelected ? "var(--accent-cyan, #0284c7)" : "transparent"}
                      style={{ transition: "color 120ms ease" }}
                    />
                  </div>
                </div>
              );
            })
          )}
        </div>

        {/* Footer info bar */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            padding: "10px 18px",
            borderTop: "1px solid var(--border-color, #e2e8f0)",
            background: "var(--bg-secondary, #f8fafc)",
            fontSize: "0.72rem",
            color: "var(--text-secondary, #64748b)",
            fontFamily: "var(--font-mono)",
          }}
        >
          <div style={{ display: "flex", gap: "14px" }}>
            <span><strong style={{ color: "var(--text-primary, #0f172a)" }}>↑↓</strong> to navigate</span>
            <span><strong style={{ color: "var(--text-primary, #0f172a)" }}>↵</strong> to select</span>
            <span><strong style={{ color: "var(--text-primary, #0f172a)" }}>esc</strong> to close</span>
          </div>
          <div>AASI Universal Command Fabric</div>
        </div>
      </div>
    </div>
  );
};
