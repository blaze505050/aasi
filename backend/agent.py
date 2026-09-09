"""
AASI Agent Layer: Multi-stage reasoning, tool selection, execution, and synthesis.
"""

import logging
import re
from typing import Any, Dict, List, Optional, Tuple
import httpx

from backend.config import AASI_SYSTEM_PROMPT, settings
from backend.tools.registry import tool_registry

logger = logging.getLogger(__name__)


class AASIAgentError(Exception):
    """Base exception for AASI Agent errors."""
    pass


class OllamaUnavailableError(AASIAgentError):
    """Raised when the Ollama runtime is unreachable."""
    pass


class OllamaRuntimeError(AASIAgentError):
    """Raised when Ollama returns an error or fails during inference."""
    pass


class AASIAgent:
    """Orchestrates AI reasoning, tool routing, mathematical execution, and synthesis."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        timeout: Optional[float] = None,
        system_prompt: Optional[str] = None,
    ):
        self.base_url = (base_url or settings.ollama_base_url).rstrip("/")
        self.model = model or settings.ollama_model
        self.timeout = timeout or settings.ollama_timeout
        self.system_prompt = system_prompt or AASI_SYSTEM_PROMPT

    async def check_health(self) -> Tuple[bool, Optional[str]]:
        """
        Check if Ollama runtime is reachable and responsive.
        Returns a tuple of (is_healthy, status_or_error_message).
        """
        url = f"{self.base_url}/api/tags"
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(url)
                if response.status_code == 200:
                    data = response.json()
                    models = [m.get("name") for m in data.get("models", []) if "name" in m]
                    logger.debug("Ollama is reachable. Available models: %s", models)
                    return True, None
                else:
                    return False, f"Ollama returned HTTP status {response.status_code}"
        except httpx.ConnectError:
            return False, f"Could not connect to Ollama at {self.base_url}. Ensure Ollama is running."
        except httpx.TimeoutException:
            return False, f"Connection to Ollama timed out at {self.base_url}."
        except Exception as exc:
            return False, f"Unexpected error connecting to Ollama: {str(exc)}"

    async def generate_response(self, user_message: str, system_override: Optional[str] = None) -> Dict[str, Any]:
        """
        Directly send a prompt with system prompt to Ollama and return text.
        """
        if not user_message or not user_message.strip():
            raise ValueError("User message cannot be empty.")

        url = f"{self.base_url}/api/chat"
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": system_override or self.system_prompt,
                },
                {
                    "role": "user",
                    "content": user_message.strip(),
                },
            ],
            "stream": False,
        }

        logger.info("Dispatching prompt to Ollama model '%s' at %s", self.model, url)

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, json=payload)
        except httpx.ConnectError as exc:
            logger.error("Connection error while communicating with Ollama: %s", exc)
            raise OllamaUnavailableError(
                f"Cannot connect to Ollama at {self.base_url}. Please verify that the Ollama service is running "
                f"and accessible."
            ) from exc
        except httpx.TimeoutException as exc:
            logger.error("Timeout waiting for Ollama response: %s", exc)
            raise OllamaRuntimeError(
                f"Ollama timed out after {self.timeout}s waiting for model '{self.model}'."
            ) from exc
        except Exception as exc:
            logger.error("Unexpected network error while contacting Ollama: %s", exc)
            raise OllamaRuntimeError(f"Network error communicating with Ollama: {str(exc)}") from exc

        if response.status_code != 200:
            error_detail = response.text
            logger.error("Ollama returned error HTTP %d: %s", response.status_code, error_detail)
            if response.status_code == 404:
                raise OllamaRuntimeError(
                    f"Model '{self.model}' was not found in Ollama. "
                    f"Run `ollama pull {self.model}` to download it or change OLLAMA_MODEL."
                )
            raise OllamaRuntimeError(f"Ollama error (HTTP {response.status_code}): {error_detail}")

        try:
            data = response.json()
            model_response = data.get("message", {}).get("content", "")
            actual_model = data.get("model", self.model)
            return {
                "response": model_response,
                "model": actual_model,
                "status": "success",
            }
        except Exception as exc:
            logger.error("Failed to parse Ollama response JSON: %s", exc)
            raise OllamaRuntimeError(f"Failed to parse Ollama JSON response: {str(exc)}") from exc

    def detect_calculation_intent(self, message: str) -> Optional[Tuple[str, str, Dict[str, Any]]]:
        """
        Analyze user message to determine if an engineering calculation tool should be invoked.
        Returns (tool_name, operation, parameters) or None if conceptual.
        """
        msg_lower = message.lower()

        # Pure conceptual checks - if user explicitly asks for explanation/definition without specific numbers
        if re.search(r"^(what is|explain|define|describe|how does)\b", msg_lower):
            # Check if there are specific numerical parameters
            has_numbers = bool(re.search(r"\b\d+(\.\d+)?\s*(km|m/s|kg|s|deg)\b", msg_lower))
            if not has_numbers and not re.search(r"\bcalculate|compute|find\b", msg_lower):
                return None

        # 1. Hohmann Transfer
        if "hohmann" in msg_lower and ("transfer" in msg_lower or "delta-v" in msg_lower or "deltav" in msg_lower or "dv" in msg_lower or "calculate" in msg_lower or "km" in msg_lower):
            # Extract altitudes
            numbers = re.findall(r"[-+]?\d+(?:\.\d+)?", message)
            if len(numbers) >= 2:
                try:
                    alt1 = float(numbers[0])
                    alt2 = float(numbers[1])
                    body = "Earth"
                    if "mars" in msg_lower:
                        body = "Mars"
                    elif "moon" in msg_lower:
                        body = "Moon"
                    elif "sun" in msg_lower:
                        body = "Sun"
                    return "orbit", "hohmann_transfer", {
                        "initial_altitude_km": alt1,
                        "final_altitude_km": alt2,
                        "central_body": body,
                    }
                except (ValueError, IndexError):
                    pass

        # 2. Escape Velocity
        if "escape" in msg_lower and ("velocity" in msg_lower or "speed" in msg_lower):
            numbers = re.findall(r"[-+]?\d+(?:\.\d+)?", message)
            if numbers:
                try:
                    alt = float(numbers[0])
                    body = "Earth"
                    if "mars" in msg_lower:
                        body = "Mars"
                    elif "moon" in msg_lower:
                        body = "Moon"
                    return "orbit", "escape_velocity", {
                        "altitude_km": alt,
                        "central_body": body,
                    }
                except (ValueError, IndexError):
                    pass

        # 3. Circular Orbital Velocity / Period
        if ("circular" in msg_lower or "orbital velocity" in msg_lower or "orbital period" in msg_lower) and ("altitude" in msg_lower or "orbit" in msg_lower or "km" in msg_lower):
            numbers = re.findall(r"[-+]?\d+(?:\.\d+)?", message)
            if numbers:
                try:
                    alt = float(numbers[0])
                    body = "Earth"
                    if "mars" in msg_lower:
                        body = "Mars"
                    elif "moon" in msg_lower:
                        body = "Moon"
                    return "orbit", "circular_orbit", {
                        "altitude_km": alt,
                        "central_body": body,
                    }
                except (ValueError, IndexError):
                    pass

        # 4. Rocket Equation (Tsiolkovsky)
        if ("rocket" in msg_lower or "isp" in msg_lower or "tsiolkovsky" in msg_lower) and ("delta" in msg_lower or "dv" in msg_lower or "calculate" in msg_lower or "velocity" in msg_lower):
            isp_match = re.search(r"isp\s*=\s*([-+]?\d+(?:\.\d+)?)", msg_lower)
            m0_match = re.search(r"(?:initial\s*(?:mass)?|m0|wet\s*mass)\s*=\s*([-+]?\d+(?:\.\d+)?)", msg_lower)
            mf_match = re.search(r"(?:final\s*(?:mass)?|mf|dry\s*mass)\s*=\s*([-+]?\d+(?:\.\d+)?)", msg_lower)

            if isp_match and m0_match and mf_match:
                try:
                    return "rocket", "rocket_equation", {
                        "isp_s": float(isp_match.group(1)),
                        "initial_mass_kg": float(m0_match.group(1)),
                        "final_mass_kg": float(mf_match.group(1)),
                    }
                except ValueError:
                    pass

            # Alternative: required mass ratio for target delta-v
            dv_match = re.search(r"(?:delta[-_\s]*v|target\s*delta[-_\s]*v|dv)\s*=\s*([-+]?\d+(?:\.\d+)?)", msg_lower)
            if dv_match and isp_match and not (m0_match and mf_match):
                try:
                    return "rocket", "required_mass_ratio", {
                        "delta_v_m_s": float(dv_match.group(1)),
                        "isp_s": float(isp_match.group(1)),
                    }
                except ValueError:
                    pass

        # 5. Symbolic Equation Solving
        if re.search(r"\bsolve\b", msg_lower) and ("for" in msg_lower or "=" in message):
            eq_match = re.search(r"solve\s+([^\n,]+?)(?:\s+for\s+([a-zA-Z_]\w*))?$", message, re.IGNORECASE)
            if eq_match:
                eq_str = eq_match.group(1).strip()
                var_str = eq_match.group(2).strip() if eq_match.group(2) else "x"
                return "math", "solve_equation", {
                    "equation_str": eq_str,
                    "variable_str": var_str,
                }

        return None

    async def process_chat(self, user_message: str) -> Dict[str, Any]:
        """
        Full AASI reasoning and tool execution loop:
        1. Classify intent.
        2. Execute tool if numerical.
        3. Explain result via LLM.
        4. Return structured response with trace.
        """
        intent = self.detect_calculation_intent(user_message)

        if intent is None:
            # Pure conceptual question -> direct LLM answer
            res = await self.generate_response(user_message)
            return {
                "response": res["response"],
                "tool_calls": [],
                "calculations": [],
                "verification": None,
                "model": res["model"],
                "status": "success",
            }

        tool_name, operation, params = intent
        trace_steps: List[str] = [
            f"Identified aerospace calculation: {tool_name}.{operation}",
            f"Extracted input parameters: {params}",
        ]

        try:
            # Execute actual scientific calculation
            trace_steps.append(f"Executing verified tool '{tool_name}' (operation: '{operation}')")
            calc_result = tool_registry.execute(tool_name, operation, **params)
            trace_steps.append("Executed calculation successfully with physical constants")

            # Verification layer if applicable
            verification_data = None
            if tool_name == "rocket" and operation == "rocket_equation":
                # Verify Delta-v recomputation via SymPy
                from backend.tools.math_utils import verify_calculation
                v_calc = calc_result["results"]["delta_v_m_s"]
                isp_val = params["isp_s"]
                m0_val = params["initial_mass_kg"]
                mf_val = params["final_mass_kg"]
                verif = verify_calculation(
                    calculated_value=v_calc,
                    reference_formula="9.80665 * isp * log(m0 / mf)",
                    parameters={"isp": isp_val, "m0": m0_val, "mf": mf_val},
                    tolerance_rel=1e-4,
                )
                verification_data = verif
                trace_steps.append("Independently verified Delta-v with SymPy symbolic engine")

            elif tool_name == "orbit" and operation == "circular_orbit":
                # Verify circular velocity
                from backend.tools.math_utils import verify_calculation
                v_calc = calc_result["results"]["orbital_velocity_km_s"]
                r_val = calc_result["results"]["orbital_radius_km"]
                mu_val = calc_result["results"]["standard_gravitational_parameter_km3_s2"]
                verif = verify_calculation(
                    calculated_value=v_calc,
                    reference_formula="sqrt(mu / r)",
                    parameters={"mu": mu_val, "r": r_val},
                    tolerance_rel=1e-4,
                )
                verification_data = verif
                trace_steps.append("Independently verified orbital velocity with SymPy")

            # Prepare concise synthesis prompt for LLM
            calc_summary = "\n".join(f"- {k}: {v}" for k, v in calc_result["results"].items())
            inputs_summary = "\n".join(f"- {k}: {v}" for k, v in calc_result["inputs"].items())
            assumptions_summary = "\n".join(f"- {a}" for a in calc_result.get("assumptions", []))
            
            synthesis_prompt = (
                f"User Question: {user_message}\n\n"
                f"VERIFIED CALCULATION RESULTS FROM '{tool_name}.{operation}':\n"
                f"Inputs:\n{inputs_summary}\n\n"
                f"Results:\n{calc_summary}\n\n"
                f"Units: {calc_result.get('units', {})}\n\n"
                f"Assumptions:\n{assumptions_summary}\n\n"
                "Instructions:\n"
                "1. State the exact verified calculation results above.\n"
                "2. Clearly mention the inputs, the results with their units, and the physical assumptions.\n"
                "3. Do not attempt to recalculate or alter these verified numerical values.\n"
                "4. Provide a brief, technically sound aerospace explanation of what this result means."
            )

            trace_steps.append("Generating technical synthesis with open-weight model")
            llm_res = await self.generate_response(synthesis_prompt)
            trace_steps.append("Completed response synthesis")

            return {
                "response": llm_res["response"],
                "tool_calls": [
                    {
                        "tool": tool_name,
                        "operation": operation,
                        "status": "success",
                        "trace": trace_steps,
                    }
                ],
                "calculations": [calc_result],
                "verification": verification_data,
                "model": llm_res["model"],
                "status": "success",
            }

        except ValueError as val_err:
            trace_steps.append(f"Validation error: {str(val_err)}")
            return {
                "response": (
                    f"Parameter Validation Notice: Could not complete calculation for '{tool_name}.{operation}'.\n\n"
                    f"Reason: {str(val_err)}\n\n"
                    f"Please review the required parameters and units."
                ),
                "tool_calls": [
                    {
                        "tool": tool_name,
                        "operation": operation,
                        "status": "validation_error",
                        "trace": trace_steps,
                    }
                ],
                "calculations": [],
                "verification": None,
                "model": self.model,
                "status": "validation_error",
            }
        except Exception as exc:
            logger.exception("Unexpected error executing tool %s.%s", tool_name, operation)
            trace_steps.append(f"Execution failure: {str(exc)}")
            return {
                "response": (
                    f"Engineering Tool Error: An error occurred while executing '{tool_name}.{operation}': {str(exc)}"
                ),
                "tool_calls": [
                    {
                        "tool": tool_name,
                        "operation": operation,
                        "status": "error",
                        "trace": trace_steps,
                    }
                ],
                "calculations": [],
                "verification": None,
                "model": self.model,
                "status": "error",
            }


# Default module-level agent instance
default_agent = AASIAgent()
