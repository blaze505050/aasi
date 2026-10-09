"use client";

import React, { useState, useEffect } from "react";
import { User, Shield, Key, LogIn, UserPlus, LogOut, CheckCircle, AlertCircle, X, Lock, Mail } from "lucide-react";

export interface AuthUser {
  user_id: string;
  username: string;
  email: string;
  role: string;
  org_id?: string;
  created_at?: string;
}

interface AuthModalProps {
  isOpen: boolean;
  onClose: () => void;
  apiBase: string;
  currentUser: AuthUser | null;
  onAuthSuccess: (user: AuthUser, token: string) => void;
  onLogout: () => void;
}

type AuthTab = "LOGIN" | "REGISTER" | "SSO";

export const AuthModal: React.FC<AuthModalProps> = ({
  isOpen,
  onClose,
  apiBase,
  currentUser,
  onAuthSuccess,
  onLogout,
}) => {
  const [tab, setTab] = useState<AuthTab>("LOGIN");
  const [usernameOrEmail, setUsernameOrEmail] = useState("");
  const [password, setPassword] = useState("");
  const [regUsername, setRegUsername] = useState("");
  const [regEmail, setRegEmail] = useState("");
  const [regPassword, setRegPassword] = useState("");
  const [ssoProvider, setSsoProvider] = useState("okta");
  const [ssoEmail, setSsoEmail] = useState("lead.aerodynamicist@boeing.com");
  const [ssoRole, setSsoRole] = useState("CHIEF_AERODYNAMICIST");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleSSOLogin = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const res = await fetch(`${apiBase}/api/auth/sso/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          provider_id: ssoProvider,
          email: ssoEmail.trim(),
          target_role: ssoRole,
        }),
      });
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.detail || "Enterprise SSO login failed.");
      }
      const data = await res.json();
      localStorage.setItem("aasi_auth_token", data.token);
      const meData: AuthUser = {
        user_id: data.user_id,
        username: data.username,
        email: data.email,
        role: data.role,
        org_id: data.org_id,
      };
      localStorage.setItem("aasi_user", JSON.stringify(meData));
      onAuthSuccess(meData, data.token);
      onClose();
    } catch (err: any) {
      setError(err.message || "SSO federated authentication failed.");
    } finally {
      setLoading(false);
    }
  };

  const handleLogin = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      const res = await fetch(`${apiBase}/api/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          username_or_email: usernameOrEmail.trim(),
          password: password,
        }),
      });

      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.detail || "Authentication failed. Check your credentials.");
      }

      const tokenData = await res.json();
      const token = tokenData.access_token;
      localStorage.setItem("aasi_auth_token", token);

      // Fetch user profile
      const meRes = await fetch(`${apiBase}/api/auth/me`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      const meData = meRes.ok ? await meRes.json() : {
        user_id: tokenData.user_id,
        username: usernameOrEmail,
        email: `${usernameOrEmail}@aasi.aero`,
        role: tokenData.role || "RESEARCHER",
      };

      localStorage.setItem("aasi_user", JSON.stringify(meData));
      onAuthSuccess(meData, token);
      onClose();
    } catch (err: any) {
      setError(err.message || "Failed to authenticate.");
    } finally {
      setLoading(false);
    }
  };

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      const res = await fetch(`${apiBase}/api/auth/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          username: regUsername.trim(),
          email: regEmail.trim(),
          password: regPassword,
          role: "RESEARCHER",
        }),
      });

      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.detail || "Registration failed. Try a different username/email.");
      }

      setSuccessMsg("Account successfully registered! Logging you in...");
      // Auto-login after registration
      setUsernameOrEmail(regUsername);
      setPassword(regPassword);
      setTimeout(async () => {
        const loginRes = await fetch(`${apiBase}/api/auth/login`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            username_or_email: regUsername.trim(),
            password: regPassword,
          }),
        });
        if (loginRes.ok) {
          const tData = await loginRes.json();
          localStorage.setItem("aasi_auth_token", tData.access_token);
          const meData = {
            user_id: tData.user_id,
            username: regUsername,
            email: regEmail,
            role: tData.role || "RESEARCHER",
          };
          localStorage.setItem("aasi_user", JSON.stringify(meData));
          onAuthSuccess(meData, tData.access_token);
          onClose();
        } else {
          setTab("LOGIN");
          setSuccessMsg("Registered! Please sign in.");
        }
      }, 700);
    } catch (err: any) {
      setError(err.message || "Registration failed.");
    } finally {
      setLoading(false);
    }
  };

  const handleDemoSignIn = async () => {
    setUsernameOrEmail("researcher");
    setPassword("aerospace-secure-password-2026");
    setError(null);
    setLoading(true);
    try {
      const res = await fetch(`${apiBase}/api/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          username_or_email: "researcher",
          password: "aerospace-secure-password-2026",
        }),
      });
      if (res.ok) {
        const tokenData = await res.json();
        localStorage.setItem("aasi_auth_token", tokenData.access_token);
        const meRes = await fetch(`${apiBase}/api/auth/me`, {
          headers: { Authorization: `Bearer ${tokenData.access_token}` },
        });
        const meData = meRes.ok ? await meRes.json() : {
          user_id: tokenData.user_id,
          username: "researcher",
          email: "researcher@aasi.aero",
          role: "RESEARCHER",
        };
        localStorage.setItem("aasi_user", JSON.stringify(meData));
        onAuthSuccess(meData, tokenData.access_token);
        onClose();
      } else {
        throw new Error("Demo profile login failed. Please register a new user.");
      }
    } catch (err: any) {
      setError(err.message || "Demo sign in failed.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      style={{
        position: "fixed",
        inset: 0,
        zIndex: 1000,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        background: "rgba(0, 0, 0, 0.75)",
        backdropFilter: "blur(8px)",
      }}
      onClick={onClose}
    >
      <div
        style={{
          width: "100%",
          maxWidth: "460px",
          background: "#0c111d",
          border: "1px solid #1e293b",
          borderRadius: "10px",
          boxShadow: "0 20px 50px rgba(0,0,0,0.6)",
          padding: "24px",
          color: "#f8fafc",
          position: "relative",
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Close Button */}
        <button
          onClick={onClose}
          style={{
            position: "absolute",
            top: "16px",
            right: "16px",
            background: "none",
            border: "none",
            color: "#64748b",
            cursor: "pointer",
          }}
        >
          <X size={18} />
        </button>

        {currentUser ? (
          /* Active User Profile View */
          <div>
            <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "16px" }}>
              <div
                style={{
                  width: "42px",
                  height: "42px",
                  borderRadius: "8px",
                  background: "rgba(56, 189, 248, 0.15)",
                  border: "1px solid rgba(56, 189, 248, 0.3)",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  color: "#38bdf8",
                }}
              >
                <User size={22} />
              </div>
              <div>
                <h3 style={{ fontSize: "1rem", fontWeight: 700, margin: 0 }}>{currentUser.username}</h3>
                <span style={{ fontSize: "0.74rem", color: "#94a3b8" }}>{currentUser.email}</span>
              </div>
            </div>

            <div
              style={{
                background: "#111827",
                border: "1px solid #1f2937",
                borderRadius: "8px",
                padding: "14px",
                marginBottom: "20px",
                fontSize: "0.78rem",
                display: "grid",
                gridTemplateColumns: "1fr 1fr",
                gap: "10px",
              }}
            >
              <div>
                <span style={{ color: "#64748b", display: "block", fontSize: "0.68rem" }}>ROLE / CLEARANCE</span>
                <span style={{ color: "#f59e0b", fontWeight: 700 }}>{currentUser.role}</span>
              </div>
              <div>
                <span style={{ color: "#64748b", display: "block", fontSize: "0.68rem" }}>SESSION STATUS</span>
                <span style={{ color: "#10b981", fontWeight: 700 }}>AUTHENTICATED</span>
              </div>
              <div>
                <span style={{ color: "#64748b", display: "block", fontSize: "0.68rem" }}>ORGANIZATION</span>
                <span style={{ color: "#cbd5e1", fontWeight: 600 }}>Orbit-1 Aerospace</span>
              </div>
              <div>
                <span style={{ color: "#64748b", display: "block", fontSize: "0.68rem" }}>TOKEN SECURITY</span>
                <span style={{ color: "#38bdf8", fontFamily: "var(--font-mono)", fontSize: "0.7rem" }}>PBKDF2-HMAC</span>
              </div>
            </div>

            <div style={{ display: "flex", gap: "10px" }}>
              <button
                onClick={() => {
                  localStorage.removeItem("aasi_auth_token");
                  localStorage.removeItem("aasi_user");
                  onLogout();
                  onClose();
                }}
                style={{
                  flex: 1,
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  gap: "6px",
                  padding: "9px 16px",
                  borderRadius: "6px",
                  background: "rgba(239, 68, 68, 0.15)",
                  border: "1px solid rgba(239, 68, 68, 0.3)",
                  color: "#ef4444",
                  fontSize: "0.8rem",
                  fontWeight: 600,
                  cursor: "pointer",
                }}
              >
                <LogOut size={14} />
                <span>Sign Out Session</span>
              </button>
              <button
                onClick={onClose}
                style={{
                  padding: "9px 20px",
                  borderRadius: "6px",
                  background: "#1e293b",
                  border: "1px solid #334155",
                  color: "#f8fafc",
                  fontSize: "0.8rem",
                  fontWeight: 600,
                  cursor: "pointer",
                }}
              >
                Close
              </button>
            </div>
          </div>
        ) : (
          /* Login / Register Form */
          <div>
            <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "16px" }}>
              <Shield size={20} color="#38bdf8" />
              <h3 style={{ fontSize: "1.05rem", fontWeight: 700, margin: 0 }}>AASI Aerospace Authentication</h3>
            </div>

            {/* Tab Switcher */}
            <div
              style={{
                display: "flex",
                background: "#111827",
                borderRadius: "6px",
                padding: "3px",
                marginBottom: "16px",
                border: "1px solid #1f2937",
              }}
            >
              <button
                type="button"
                onClick={() => { setTab("LOGIN"); setError(null); }}
                style={{
                  flex: 1,
                  padding: "6px 12px",
                  borderRadius: "4px",
                  border: "none",
                  background: tab === "LOGIN" ? "#1e293b" : "transparent",
                  color: tab === "LOGIN" ? "#f8fafc" : "#64748b",
                  fontSize: "0.78rem",
                  fontWeight: 600,
                  cursor: "pointer",
                  transition: "all 120ms ease",
                }}
              >
                Sign In
              </button>
              <button
                type="button"
                onClick={() => { setTab("REGISTER"); setError(null); }}
                style={{
                  flex: 1,
                  padding: "6px 12px",
                  borderRadius: "4px",
                  border: "none",
                  background: tab === "REGISTER" ? "#1e293b" : "transparent",
                  color: tab === "REGISTER" ? "#f8fafc" : "#64748b",
                  fontSize: "0.78rem",
                  fontWeight: 600,
                  cursor: "pointer",
                  transition: "all 120ms ease",
                }}
              >
                Register
              </button>
              <button
                type="button"
                onClick={() => { setTab("SSO"); setError(null); }}
                style={{
                  flex: 1,
                  padding: "6px 12px",
                  borderRadius: "4px",
                  border: "none",
                  background: tab === "SSO" ? "rgba(56, 189, 248, 0.15)" : "transparent",
                  color: tab === "SSO" ? "#38bdf8" : "#64748b",
                  fontSize: "0.78rem",
                  fontWeight: 600,
                  cursor: "pointer",
                  transition: "all 120ms ease",
                  borderLeft: "1px solid #1f2937",
                }}
              >
                Enterprise SSO
              </button>
            </div>

            {error && (
              <div
                style={{
                  background: "rgba(239, 68, 68, 0.12)",
                  border: "1px solid rgba(239, 68, 68, 0.3)",
                  borderRadius: "6px",
                  padding: "8px 12px",
                  color: "#f87171",
                  fontSize: "0.74rem",
                  display: "flex",
                  alignItems: "center",
                  gap: "6px",
                  marginBottom: "14px",
                }}
              >
                <AlertCircle size={14} />
                <span>{error}</span>
              </div>
            )}

            {successMsg && (
              <div
                style={{
                  background: "rgba(16, 185, 129, 0.12)",
                  border: "1px solid rgba(16, 185, 129, 0.3)",
                  borderRadius: "6px",
                  padding: "8px 12px",
                  color: "#34d399",
                  fontSize: "0.74rem",
                  display: "flex",
                  alignItems: "center",
                  gap: "6px",
                  marginBottom: "14px",
                }}
              >
                <CheckCircle size={14} />
                <span>{successMsg}</span>
              </div>
            )}

            {tab === "LOGIN" ? (
              <form onSubmit={handleLogin} style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
                <div>
                  <label style={{ fontSize: "0.72rem", color: "#94a3b8", display: "block", marginBottom: "4px" }}>
                    Username or Email
                  </label>
                  <div style={{ position: "relative" }}>
                    <input
                      type="text"
                      required
                      value={usernameOrEmail}
                      onChange={(e) => setUsernameOrEmail(e.target.value)}
                      placeholder="e.g. researcher"
                      style={{
                        width: "100%",
                        padding: "8px 12px 8px 32px",
                        borderRadius: "6px",
                        background: "#111827",
                        border: "1px solid #1f2937",
                        color: "#f8fafc",
                        fontSize: "0.8rem",
                      }}
                    />
                    <User size={14} color="#64748b" style={{ position: "absolute", left: "10px", top: "11px" }} />
                  </div>
                </div>

                <div>
                  <label style={{ fontSize: "0.72rem", color: "#94a3b8", display: "block", marginBottom: "4px" }}>
                    Password
                  </label>
                  <div style={{ position: "relative" }}>
                    <input
                      type="password"
                      required
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      placeholder="••••••••••••"
                      style={{
                        width: "100%",
                        padding: "8px 12px 8px 32px",
                        borderRadius: "6px",
                        background: "#111827",
                        border: "1px solid #1f2937",
                        color: "#f8fafc",
                        fontSize: "0.8rem",
                      }}
                    />
                    <Lock size={14} color="#64748b" style={{ position: "absolute", left: "10px", top: "11px" }} />
                  </div>
                </div>

                <button
                  type="submit"
                  disabled={loading}
                  style={{
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    gap: "6px",
                    padding: "9px 16px",
                    borderRadius: "6px",
                    background: "#38bdf8",
                    border: "none",
                    color: "#0a0d14",
                    fontSize: "0.82rem",
                    fontWeight: 700,
                    cursor: "pointer",
                    marginTop: "4px",
                  }}
                >
                  <LogIn size={14} />
                  <span>{loading ? "Authenticating..." : "Sign In to Platform"}</span>
                </button>

                <div style={{ textAlign: "center", margin: "6px 0", fontSize: "0.68rem", color: "#64748b" }}>
                  — OR QUICK LAUNCH —
                </div>

                <button
                  type="button"
                  onClick={handleDemoSignIn}
                  disabled={loading}
                  style={{
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    gap: "6px",
                    padding: "8px 14px",
                    borderRadius: "6px",
                    background: "rgba(245, 158, 11, 0.12)",
                    border: "1px solid rgba(245, 158, 11, 0.3)",
                    color: "#f59e0b",
                    fontSize: "0.78rem",
                    fontWeight: 600,
                    cursor: "pointer",
                  }}
                >
                  <Key size={13} />
                  <span>Sign In as Researcher (Default Aerospace Seat)</span>
                </button>
              </form>
            ) : tab === "REGISTER" ? (
              <form onSubmit={handleRegister} style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
                <div>
                  <label style={{ fontSize: "0.72rem", color: "#94a3b8", display: "block", marginBottom: "4px" }}>
                    Username
                  </label>
                  <div style={{ position: "relative" }}>
                    <input
                      type="text"
                      required
                      value={regUsername}
                      onChange={(e) => setRegUsername(e.target.value)}
                      placeholder="e.g. aero_engineer"
                      style={{
                        width: "100%",
                        padding: "8px 12px 8px 32px",
                        borderRadius: "6px",
                        background: "#111827",
                        border: "1px solid #1f2937",
                        color: "#f8fafc",
                        fontSize: "0.8rem",
                      }}
                    />
                    <User size={14} color="#64748b" style={{ position: "absolute", left: "10px", top: "11px" }} />
                  </div>
                </div>

                <div>
                  <label style={{ fontSize: "0.72rem", color: "#94a3b8", display: "block", marginBottom: "4px" }}>
                    Work Email
                  </label>
                  <div style={{ position: "relative" }}>
                    <input
                      type="email"
                      required
                      value={regEmail}
                      onChange={(e) => setRegEmail(e.target.value)}
                      placeholder="name@company.aero"
                      style={{
                        width: "100%",
                        padding: "8px 12px 8px 32px",
                        borderRadius: "6px",
                        background: "#111827",
                        border: "1px solid #1f2937",
                        color: "#f8fafc",
                        fontSize: "0.8rem",
                      }}
                    />
                    <Mail size={14} color="#64748b" style={{ position: "absolute", left: "10px", top: "11px" }} />
                  </div>
                </div>

                <div>
                  <label style={{ fontSize: "0.72rem", color: "#94a3b8", display: "block", marginBottom: "4px" }}>
                    Password (Min 8 chars, mixed case, number)
                  </label>
                  <div style={{ position: "relative" }}>
                    <input
                      type="password"
                      required
                      value={regPassword}
                      onChange={(e) => setRegPassword(e.target.value)}
                      placeholder="Create secure passphrase"
                      style={{
                        width: "100%",
                        padding: "8px 12px 8px 32px",
                        borderRadius: "6px",
                        background: "#111827",
                        border: "1px solid #1f2937",
                        color: "#f8fafc",
                        fontSize: "0.8rem",
                      }}
                    />
                    <Lock size={14} color="#64748b" style={{ position: "absolute", left: "10px", top: "11px" }} />
                  </div>
                </div>

                <button
                  type="submit"
                  disabled={loading}
                  style={{
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    gap: "6px",
                    padding: "9px 16px",
                    borderRadius: "6px",
                    background: "#10b981",
                    border: "none",
                    color: "#0a0d14",
                    fontSize: "0.82rem",
                    fontWeight: 700,
                    cursor: "pointer",
                    marginTop: "4px",
                  }}
                >
                  <UserPlus size={14} />
                  <span>{loading ? "Registering..." : "Create Free Account"}</span>
                </button>
              </form>
            ) : (
              <form onSubmit={handleSSOLogin} style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
                <div style={{ background: "rgba(56, 189, 248, 0.08)", border: "1px solid rgba(56, 189, 248, 0.25)", borderRadius: "6px", padding: "10px 12px" }}>
                  <div style={{ display: "flex", alignItems: "center", gap: "6px", color: "#38bdf8", fontSize: "0.76rem", fontWeight: 700, marginBottom: "4px" }}>
                    <Shield size={14} />
                    <span>SAML 2.0 / OIDC Identity Federation</span>
                  </div>
                  <p style={{ margin: 0, fontSize: "0.72rem", color: "#94a3b8", lineHeight: 1.4 }}>
                    Federated single sign-on with corporate identity providers. Hardware security key (FIDO2) and CAC/PIV smart card assertion compliant.
                  </p>
                </div>

                <div>
                  <label style={{ fontSize: "0.72rem", color: "#94a3b8", display: "block", marginBottom: "4px" }}>
                    Enterprise Identity Provider (IDP)
                  </label>
                  <select
                    value={ssoProvider}
                    onChange={(e) => setSsoProvider(e.target.value)}
                    style={{
                      width: "100%",
                      padding: "8px 12px",
                      borderRadius: "6px",
                      background: "#111827",
                      border: "1px solid #1f2937",
                      color: "#f8fafc",
                      fontSize: "0.8rem",
                      cursor: "pointer",
                    }}
                  >
                    <option value="okta">Okta Aerospace Cloud (SAML 2.0 / OIDC)</option>
                    <option value="azure_ad">Microsoft Entra ID / Azure AD Defense Cloud</option>
                    <option value="google_workspace">Google Workspace Enterprise SSO</option>
                    <option value="custom_saml">Custom Corporate SAML 2.0 Identity Provider</option>
                  </select>
                </div>

                <div>
                  <label style={{ fontSize: "0.72rem", color: "#94a3b8", display: "block", marginBottom: "4px" }}>
                    Corporate Work Email
                  </label>
                  <div style={{ position: "relative" }}>
                    <input
                      type="email"
                      required
                      value={ssoEmail}
                      onChange={(e) => setSsoEmail(e.target.value)}
                      placeholder="e.g. aero.lead@lockheedmartin.com"
                      style={{
                        width: "100%",
                        padding: "8px 12px 8px 32px",
                        borderRadius: "6px",
                        background: "#111827",
                        border: "1px solid #1f2937",
                        color: "#f8fafc",
                        fontSize: "0.8rem",
                      }}
                    />
                    <Mail size={14} color="#64748b" style={{ position: "absolute", left: "10px", top: "11px" }} />
                  </div>
                </div>

                <div>
                  <label style={{ fontSize: "0.72rem", color: "#94a3b8", display: "block", marginBottom: "4px" }}>
                    Aerospace Role Clearance Level
                  </label>
                  <select
                    value={ssoRole}
                    onChange={(e) => setSsoRole(e.target.value)}
                    style={{
                      width: "100%",
                      padding: "8px 12px",
                      borderRadius: "6px",
                      background: "#111827",
                      border: "1px solid #1f2937",
                      color: "#f8fafc",
                      fontSize: "0.8rem",
                      cursor: "pointer",
                    }}
                  >
                    <option value="CHIEF_AERODYNAMICIST">Chief Aerodynamicist (Full V&amp;V 20 Certification)</option>
                    <option value="LEAD_AERODYNAMICIST">Lead Aerodynamicist (Analysis &amp; Model Optimization)</option>
                    <option value="RESEARCHER">CFD Research Specialist (Execution &amp; Polar Export)</option>
                    <option value="AUDITOR">Compliance Auditor (Read-Only Audit &amp; Merkle Verification)</option>
                  </select>
                </div>

                <button
                  type="submit"
                  disabled={loading}
                  style={{
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    gap: "6px",
                    padding: "9px 16px",
                    borderRadius: "6px",
                    background: "#38bdf8",
                    border: "none",
                    color: "#0a0d14",
                    fontSize: "0.82rem",
                    fontWeight: 700,
                    cursor: "pointer",
                    marginTop: "4px",
                  }}
                >
                  <Shield size={14} />
                  <span>{loading ? "Authenticating SAML Assertion..." : "Federate Sign In with SAML 2.0"}</span>
                </button>

                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginTop: "4px" }}>
                  <a
                    href={`${apiBase}/api/auth/sso/saml/metadata.xml`}
                    target="_blank"
                    rel="noreferrer"
                    style={{ fontSize: "0.7rem", color: "#64748b", textDecoration: "underline" }}
                  >
                    Download SP SAML Metadata XML
                  </a>
                  <span style={{ fontSize: "0.7rem", color: "#64748b" }}>
                    ACS: /api/auth/sso/saml/acs
                  </span>
                </div>
              </form>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
