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
        msg_lower = message.lower().strip()

        # Pure conceptual checks - if user explicitly asks for explanation/definition without specific numbers
        if re.search(r"\b(what is|explain|define|describe|how does|how do|why do|why is|overview of)\b", msg_lower):
            has_numbers = bool(re.search(r"\b\d+(\.\d+)?\s*(km|m/s|kg|s|deg)\b", msg_lower))
            if not has_numbers and not re.search(r"\b(calculate|compute|solve|find the numerical)\b", msg_lower):
                return None

        # Ambiguous calculation questions missing parameters -> clarify rather than hallucinate
        if re.search(r"\bhow fast does a satellite move\b", msg_lower) or (
            re.search(r"\b(orbital velocity|orbital speed)\b", msg_lower)
            and not re.search(r"\d+", msg_lower)
            and re.search(r"\b(how|what|calculate|compute|find)\b", msg_lower)
        ):
            return "clarification", "orbital_velocity", {
                "message": (
                    "Parameter Clarification Needed: To calculate orbital velocity, AASI requires:\n\n"
                    "1. Orbital altitude (e.g. 500 km above Earth's surface)\n"
                    "2. Central celestial body (e.g. Earth, Moon, Mars, Sun - defaults to Earth)\n\n"
                    "Please specify the desired altitude (and body if not Earth)."
                )
            }

        if re.search(r"\bhow much delta[-_\s]*v do i need\b", msg_lower) or (
            re.search(r"\bdelta[-_\s]*v\b", msg_lower)
            and re.search(r"\b(how much|calculate|needed)\b", msg_lower)
            and not re.search(r"\d+", msg_lower)
        ):
            return "clarification", "delta_v", {
                "message": (
                    "Parameter Clarification Needed: To calculate required Delta-v, AASI requires:\n\n"
                    "- For an orbital maneuver: Initial and final orbital altitudes (in km)\n"
                    "- For a rocket stage: Vehicle mass ratio (m0/mf) and specific impulse (Isp in seconds)\n\n"
                    "Please provide the orbital altitudes or propulsion specifications."
                )
            }

        if re.search(r"\bhow much (?:fuel|propellant) does a rocket need\b", msg_lower) or (
            re.search(r"\b(fuel|propellant)\b", msg_lower)
            and re.search(r"\brocket\b", msg_lower)
            and re.search(r"\b(how much|calculate|needed)\b", msg_lower)
            and not re.search(r"\d+", msg_lower)
        ):
            return "clarification", "propellant_mass", {
                "message": (
                    "Parameter Clarification Needed: To calculate required propellant mass, AASI requires:\n\n"
                    "1. Vehicle dry / payload mass (kg)\n"
                    "2. Engine specific impulse (Isp in seconds)\n"
                    "3. Target Delta-v (m/s)\n\n"
                    "Please provide these parameters to compute the propellant requirements."
                )
            }

        # Central body extraction
        def _extract_body(text: str) -> str:
            # Check known celestial bodies first
            known_bodies = ["earth", "moon", "mars", "sun", "jupiter", "saturn", "venus", "mercury", "uranus", "neptune", "pluto"]
            for body_candidate in known_bodies:
                if re.search(r"\b" + body_candidate + r"\b", text):
                    return body_candidate.capitalize()

            # Check context words 'around <body_name>', 'for <body_name>', 'from <body_name>'
            body_match = re.search(r"\b(?:around|for|from|of)\s+([a-zA-Z]+)\b", text)
            if body_match:
                candidate = body_match.group(1).strip().capitalize()
                excluded = {"A", "The", "An", "Altitude", "Circular", "Satellite", "Orbit", "Low", "Leo", "Geo", "This", "That"}
                if candidate not in excluded:
                    return candidate

            return "Earth"

        # 1. Hohmann Transfer
        if "hohmann" in msg_lower and (
            "transfer" in msg_lower or "delta-v" in msg_lower or "deltav" in msg_lower or "dv" in msg_lower or "calculate" in msg_lower or "km" in msg_lower
        ):
            # Check pattern 'from X to Y' or 'between X and Y'
            range_match = re.search(r"(?:from|between)\s+([-+]?\d+(?:\.\d+)?)\s*(?:km)?\s+(?:to|and)\s+([-+]?\d+(?:\.\d+)?)", msg_lower)
            if range_match:
                alt1 = float(range_match.group(1))
                alt2 = float(range_match.group(2))
                return "orbit", "hohmann_transfer", {
                    "initial_altitude_km": alt1,
                    "final_altitude_km": alt2,
                    "central_body": _extract_body(msg_lower),
                }
            numbers = re.findall(r"[-+]?\d+(?:\.\d+)?", message)
            if len(numbers) >= 2:
                try:
                    return "orbit", "hohmann_transfer", {
                        "initial_altitude_km": float(numbers[0]),
                        "final_altitude_km": float(numbers[1]),
                        "central_body": _extract_body(msg_lower),
                    }
                except (ValueError, IndexError):
                    pass

        # 2. Escape Velocity
        if "escape" in msg_lower and ("velocity" in msg_lower or "speed" in msg_lower):
            alt_match = re.search(r"(?:at|from|for|altitude\s*(?:of|=|is|:|\s))\s*([-+]?\d+(?:\.\d+)?)", msg_lower)
            if alt_match:
                return "orbit", "escape_velocity", {
                    "altitude_km": float(alt_match.group(1)),
                    "central_body": _extract_body(msg_lower),
                }
            numbers = re.findall(r"[-+]?\d+(?:\.\d+)?", message)
            if numbers:
                try:
                    return "orbit", "escape_velocity", {
                        "altitude_km": float(numbers[0]),
                        "central_body": _extract_body(msg_lower),
                    }
                except (ValueError, IndexError):
                    pass

        # 3. Circular Orbital Velocity / Period
        if (
            "circular" in msg_lower
            or "orbital velocity" in msg_lower
            or "orbital speed" in msg_lower
            or "orbit velocity" in msg_lower
            or "orbit speed" in msg_lower
            or ("orbital" in msg_lower and "period" in msg_lower)
        ) and ("altitude" in msg_lower or "orbit" in msg_lower or "km" in msg_lower):
            alt_match = re.search(r"(?:altitude\s*(?:of|=|is|:|\s)|at\s+)\s*([-+]?\d+(?:\.\d+)?)", msg_lower)
            if alt_match:
                return "orbit", "circular_orbit", {
                    "altitude_km": float(alt_match.group(1)),
                    "central_body": _extract_body(msg_lower),
                }
            numbers = re.findall(r"[-+]?\d+(?:\.\d+)?", message)
            if numbers:
                try:
                    return "orbit", "circular_orbit", {
                        "altitude_km": float(numbers[0]),
                        "central_body": _extract_body(msg_lower),
                    }
                except (ValueError, IndexError):
                    pass

        # 4. Rocket Equation (Tsiolkovsky)
        if (
            "rocket" in msg_lower
            or "isp" in msg_lower
            or "tsiolkovsky" in msg_lower
            or "propellant" in msg_lower
        ) and (
            "delta" in msg_lower
            or "dv" in msg_lower
            or "calculate" in msg_lower
            or "velocity" in msg_lower
            or "mass" in msg_lower
        ):
            isp_match = re.search(r"(?:isp|specific impulse)\s*(?:=|of|is|:|\s)\s*([-+]?\d+(?:\.\d+)?)", msg_lower)
            m0_match = re.search(r"(?:initial\s*(?:mass)?|m0|wet\s*mass|launch\s*mass)\s*(?:=|of|is|:|\s)\s*([-+]?\d+(?:\.\d+)?)", msg_lower)
            mf_match = re.search(r"(?:final\s*(?:mass)?|mf|dry\s*mass|empty\s*mass|burnout\s*mass)\s*(?:=|of|is|:|\s)\s*([-+]?\d+(?:\.\d+)?)", msg_lower)

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
            dv_match = re.search(r"(?:delta[-_\s]*v|target\s*delta[-_\s]*v|dv)\s*(?:=|of|is|:|\s)\s*([-+]?\d+(?:\.\d+)?)", msg_lower)
            if dv_match and isp_match and not (m0_match and mf_match):
                try:
                    return "rocket", "required_mass_ratio", {
                        "delta_v_m_s": float(dv_match.group(1)),
                        "isp_s": float(isp_match.group(1)),
                    }
                except ValueError:
                    pass

        # 5. Unit Conversion
        unit_match = re.search(r"convert\s+([-+]?\d+(?:\.\d+)?)\s*([a-zA-Z_/^0-9]+)\s+to\s+([a-zA-Z_/^0-9]+)", message, re.IGNORECASE)
        if unit_match:
            try:
                val = float(unit_match.group(1))
                u_from = unit_match.group(2).strip()
                u_to = unit_match.group(3).strip()
                return "units", "convert", {
                    "value": val,
                    "from_unit": u_from,
                    "to_unit": u_to,
                }
            except (ValueError, IndexError):
                pass

        # 6. Symbolic Equation Solving
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
        if not user_message or not user_message.strip():
            raise ValueError("User message cannot be empty or whitespace.")

        intent = self.detect_calculation_intent(user_message)

        if intent is None:
            # Check knowledge subsystem for validated physical datasets or literature
            from backend.knowledge.service import get_knowledge_service
            knowledge_svc = get_knowledge_service()

            # 1. Check if query asks for specific validated physical conditions
            resolution = knowledge_svc.resolve_scientific_query(user_message)
            if resolution.get("resolution_type") == "EXACT_VALIDATED_DATASET":
                matched_pts = resolution.get("matched_points", [])
                geo = resolution.get("query_conditions", {}).get("geometry", "Airfoil")
                conds = resolution.get("query_conditions", {})
                target_var = resolution.get("target_variable", "aerodynamic coefficients")
                uncertainty = resolution.get("uncertainty", {})

                pt_desc = ", ".join(f"{k} = {v}" for k, v in matched_pts[0].items()) if matched_pts else "N/A"
                unc_desc = ", ".join(f"{k}: +/- {v}" for k, v in uncertainty.items()) if uncertainty else "Standard experimental bounds"

                resp_text = (
                    f"**Verified Reference Dataset Match:**\n\n"
                    f"According to verified {('experimental' if resolution.get('is_experimental') else 'benchmark CFD')} data from "
                    f"**{resolution.get('source')}** ({resolution.get('citation')}):\n\n"
                    f"- **Geometry:** {geo}\n"
                    f"- **Conditions:** Mach {conds.get('mach', 'N/A')}, Re {conds.get('reynolds', 'N/A')}, AoA {conds.get('aoa_deg', 'N/A')} deg\n"
                    f"- **Data Point:** {pt_desc}\n"
                    f"- **Reported Uncertainty:** {unc_desc}\n"
                    f"- **Validation Status:** {resolution.get('validation_status')}\n\n"
                    f"This value is retrieved directly from the verified dataset registry and was not fabricated."
                )

                rag_result = knowledge_svc.rag_pipeline.synthesize_response(
                    user_query=user_message,
                    retrieved=[],
                    llm_response_text=resp_text,
                    dataset_match=resolution,
                )

                return {
                    "response": resp_text,
                    "tool_calls": [],
                    "calculations": [],
                    "verification": {"status": "MATCHED_REFERENCE_DATASET", "dataset_id": resolution.get("dataset_id")},
                    "sources": rag_result.get("sources", []),
                    "evidence": rag_result.get("evidence", []),
                    "assumptions": rag_result.get("assumptions", []),
                    "provenance": rag_result.get("provenance", []),
                    "limitations": rag_result.get("limitations", []),
                    "dataset_match": resolution,
                    "model": self.model,
                    "status": "success",
                }

            # 2. Check if query explicitly asks for literature, reports, or aerodynamic data
            msg_lower = user_message.lower()
            literature_keywords = [
                "nasa", "ntrs", "naca", "report", "paper", "literature", "publication",
                "study", "journal", "experiment", "measured", "wind tunnel", "aerodynamic behavior",
                "sp-8005", "tr-824", "tr-460", "tn-d-628", "tm-x-1361", "rp-1111", "sp-8013",
                "sutton-graves", "drag polar", "critical mach", "van driest", "eddy viscosity",
                "solar constant", "meteoroid", "drag coefficient of naca"
            ]
            is_literature_query = any(kw in msg_lower for kw in literature_keywords)

            if is_literature_query:
                lit_matches = knowledge_svc.search_literature(user_message, k=3)
                if lit_matches and lit_matches[0].relevance >= 0.15:
                    context_block = knowledge_svc.rag_pipeline.build_context_block(lit_matches)
                    system_with_rag = f"{self.system_prompt}\n\n{knowledge_svc.rag_pipeline.SECURITY_PROMPT_HEADER}\n\n{context_block}"
                    
                    try:
                        res = await self.generate_response(user_message, system_override=system_with_rag)
                        model_resp = res["response"]
                        model_name = res["model"]
                    except (OllamaUnavailableError, OllamaRuntimeError) as err:
                        logger.warning("Model synthesis unavailable (%s); formatting deterministic literature synthesis", err)
                        model_name = f"{self.model} (deterministic-grounded)"
                        model_resp = (
                            f"**Verified Scientific Literature Grounding:**\n\n"
                            f"Based on **{lit_matches[0].source}** ({lit_matches[0].title}, {lit_matches[0].provenance.report_number or lit_matches[0].year}):\n\n"
                            f"{lit_matches[0].snippet}\n"
                        )

                    rag_result = knowledge_svc.rag_pipeline.synthesize_response(
                        user_query=user_message,
                        retrieved=lit_matches,
                        llm_response_text=model_resp,
                    )

                    return {
                        "response": rag_result["answer"],
                        "tool_calls": [],
                        "calculations": [],
                        "verification": None,
                        "sources": rag_result.get("sources", []),
                        "evidence": rag_result.get("evidence", []),
                        "assumptions": rag_result.get("assumptions", []),
                        "provenance": rag_result.get("provenance", []),
                        "limitations": rag_result.get("limitations", []),
                        "model": model_name,
                        "status": "success",
                    }

            # Pure conceptual question -> direct LLM answer
            res = await self.generate_response(user_message)
            return {
                "response": res["response"],
                "tool_calls": [],
                "calculations": [],
                "verification": None,
                "sources": [],
                "evidence": [],
                "assumptions": [],
                "provenance": [],
                "limitations": [],
                "model": res["model"],
                "status": "success",
            }

        tool_name, operation, params = intent

        # Handle parameter clarification requests
        if tool_name == "clarification":
            return {
                "response": params["message"],
                "tool_calls": [
                    {
                        "tool": "agent_reasoning",
                        "operation": f"request_clarification_{operation}",
                        "status": "clarification_needed",
                        "trace": [
                            f"Identified engineering calculation domain: {operation}",
                            "Detected missing required parameters",
                            "Prompted user for explicit parameters and SI units to avoid unverified speculation",
                        ],
                    }
                ],
                "calculations": [],
                "verification": None,
                "model": self.model,
                "status": "clarification_needed",
            }

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
            try:
                llm_res = await self.generate_response(synthesis_prompt)
                resp_content = llm_res["response"]
                model_used = llm_res["model"]
                trace_steps.append("Completed response synthesis with model")
            except (OllamaUnavailableError, OllamaRuntimeError) as llm_err:
                logger.warning("Model synthesis unavailable/timed out (%s); generating deterministic synthesis", llm_err)
                trace_steps.append(f"Model synthesis note: {str(llm_err)}")
                model_used = f"{self.model} (deterministic-fallback)"
                resp_content = (
                    f"**Verified Engineering Calculation Results:**\n\n"
                    f"The requested calculation for `{tool_name}.{operation}` was executed using verified physical libraries.\n\n"
                    f"**Inputs:**\n{inputs_summary}\n\n"
                    f"**Results:**\n{calc_summary}\n\n"
                    f"**Assumptions:**\n{assumptions_summary}"
                )

            return {
                "response": resp_content,
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
                "model": model_used,
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
