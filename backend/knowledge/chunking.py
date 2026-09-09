"""Structure-aware chunking preserving section hierarchy, equations, and cryptographic provenance."""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple
from .models import Chunk, Equation, Provenance


class StructureAwareChunker:
    """Chunks documents while preserving sections, page numbers, tables, and equations."""

    def __init__(
        self,
        target_chunk_size: int = 500,  # characters
        overlap: int = 50,
        max_chunk_size: int = 1000,
    ):
        self.target_chunk_size = target_chunk_size
        self.overlap = overlap
        self.max_chunk_size = max_chunk_size

        # Regex patterns for detecting scientific equations
        self._latex_pattern = re.compile(
            r"(\$\$(.*?)\$\$|\\\[(.*?)\\\]|\$(.*?)\$|\\begin\{equation\}(.*?)\\end\{equation\})",
            re.DOTALL
        )
        self._ascii_equation_pattern = re.compile(
            r"([A-Za-z0-9_\(\)\{\}\^\+\-\*\/]+(?:\s*=\s*)[A-Za-z0-9_\(\)\{\}\^\+\-\*\/\s\.\\\^]+)"
        )
        # Header detection
        self._section_pattern = re.compile(
            r"^(?:(?:Section|\d+\.|\bI{1,3}\.|\bIV\.|\bV\.)\s+)?([A-Z0-9\s,\-–]{3,60})$",
            re.MULTILINE
        )

    def extract_equations(
        self, text: str, document_id: str, page: Optional[int] = None
    ) -> List[Equation]:
        """Extract scientific equations with surrounding context and variable hints."""
        equations: List[Equation] = []
        eq_idx = 1

        # 1. LaTeX-style equations
        for match in self._latex_pattern.finditer(text):
            full_match = match.group(0).strip()
            # extract clean inner latex if available
            latex_inner = match.group(2) or match.group(3) or match.group(4) or match.group(5) or full_match
            start_pos = max(0, match.start() - 80)
            end_pos = min(len(text), match.end() + 80)
            surrounding = text[start_pos:end_pos].strip()

            vars_dict, units_dict = self._infer_variables(full_match)
            equations.append(
                Equation(
                    equation_id=f"{document_id}-eq{eq_idx}",
                    equation_text=full_match,
                    latex=latex_inner.strip(),
                    source_document_id=document_id,
                    page=page,
                    surrounding_context=surrounding,
                    variables=vars_dict,
                    units=units_dict,
                    extraction_confidence=0.95,
                )
            )
            eq_idx += 1

        # 2. Key aerospace formulas (e.g. C_L = 2*pi*alpha, Delta_v = Isp*g0*ln(m0/mf)) if not already captured
        if not equations:
            for match in self._ascii_equation_pattern.finditer(text):
                candidate = match.group(1).strip()
                # filter false positives: must have typical mathematical characters and length
                if len(candidate) > 5 and any(sym in candidate for sym in ["=", "Delta", "Isp", "Re", "Mach", "CL", "CD", "rho", "mu"]):
                    start_pos = max(0, match.start() - 60)
                    end_pos = min(len(text), match.end() + 60)
                    surrounding = text[start_pos:end_pos].strip()
                    vars_dict, units_dict = self._infer_variables(candidate)
                    equations.append(
                        Equation(
                            equation_id=f"{document_id}-eq{eq_idx}",
                            equation_text=candidate,
                            latex=None,
                            source_document_id=document_id,
                            page=page,
                            surrounding_context=surrounding,
                            variables=vars_dict,
                            units=units_dict,
                            extraction_confidence=0.80,
                        )
                    )
                    eq_idx += 1

        return equations

    def _infer_variables(self, eq_text: str) -> Tuple[Dict[str, str], Dict[str, str]]:
        """Heuristic identification of common aerospace variables and units."""
        vars_dict: Dict[str, str] = {}
        units_dict: Dict[str, str] = {}

        aerospace_var_hints = {
            "C_L": ("Lift coefficient", "dimensionless"),
            "CL": ("Lift coefficient", "dimensionless"),
            "C_D": ("Drag coefficient", "dimensionless"),
            "CD": ("Drag coefficient", "dimensionless"),
            "C_M": ("Pitching moment coefficient", "dimensionless"),
            "CM": ("Pitching moment coefficient", "dimensionless"),
            "Cp": ("Pressure coefficient", "dimensionless"),
            "alpha": ("Angle of attack", "deg / rad"),
            "Mach": ("Mach number", "dimensionless"),
            "Re": ("Reynolds number", "dimensionless"),
            "rho": ("Density", "kg/m^3"),
            "mu": ("Standard gravitational parameter / dynamic viscosity", "m^3/s^2 or Pa*s"),
            "Isp": ("Specific impulse", "seconds"),
            "Delta_v": ("Velocity increment", "m/s"),
            "v": ("Velocity", "m/s"),
            "r": ("Orbital radius", "meters"),
        }

        for var, (desc, unit) in aerospace_var_hints.items():
            if var in eq_text:
                vars_dict[var] = desc
                units_dict[var] = unit

        return vars_dict, units_dict

    def chunk_document(
        self,
        document_id: str,
        source_id: str,
        text: str,
        pages_dict: Optional[Dict[int, str]] = None,
        default_section: str = "General",
    ) -> List[Chunk]:
        """Split a document into structure-aware, traceable chunks retaining page and section context."""
        chunks: List[Chunk] = []

        if pages_dict:
            # Process page by page
            chunk_num = 1
            for page_num, page_text in sorted(pages_dict.items()):
                page_chunks = self._chunk_section(
                    document_id=document_id,
                    source_id=source_id,
                    section=f"Page {page_num}",
                    text=page_text,
                    page=page_num,
                    start_index=chunk_num,
                )
                chunks.extend(page_chunks)
                chunk_num += len(page_chunks)
            return chunks

        # If no page dictionary provided, split by structural sections or paragraphs
        sections = self._split_into_sections(text, default_section)
        chunk_num = 1
        for section_name, section_text in sections:
            sec_chunks = self._chunk_section(
                document_id=document_id,
                source_id=source_id,
                section=section_name,
                text=section_text,
                page=1,
                start_index=chunk_num,
            )
            chunks.extend(sec_chunks)
            chunk_num += len(sec_chunks)

        return chunks

    def _split_into_sections(self, text: str, default_name: str) -> List[Tuple[str, str]]:
        """Split plain text into identifiable sections based on common headings."""
        common_headings = [
            "ABSTRACT",
            "SUMMARY",
            "INTRODUCTION",
            "NOMENCLATURE",
            "THEORETICAL ANALYSIS",
            "APPARATUS AND METHODS",
            "EXPERIMENTAL RESULTS",
            "RESULTS AND DISCUSSION",
            "CFD METHODOLOGY",
            "CONCLUSIONS",
            "REFERENCES",
        ]

        # Find positions of headings
        splits: List[Tuple[int, str]] = []
        for heading in common_headings:
            for m in re.finditer(rf"(?:\n|\A)(#+\s*)?({re.escape(heading)})(?:\n|\:)", text, re.IGNORECASE):
                splits.append((m.start(), m.group(2).strip().upper()))

        if not splits:
            return [(default_name, text)]

        splits.sort(key=lambda x: x[0])
        sections: List[Tuple[str, str]] = []

        # Text before first heading
        if splits[0][0] > 0:
            preamble = text[: splits[0][0]].strip()
            if preamble:
                sections.append((default_name, preamble))

        for i, (start_idx, h_name) in enumerate(splits):
            end_idx = splits[i + 1][0] if i + 1 < len(splits) else len(text)
            body = text[start_idx:end_idx].strip()
            if body:
                sections.append((h_name, body))

        return sections

    def _chunk_section(
        self,
        document_id: str,
        source_id: str,
        section: str,
        text: str,
        page: Optional[int],
        start_index: int,
    ) -> List[Chunk]:
        """Subdivide a section or page into individual chunks with equations."""
        chunks: List[Chunk] = []
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]

        current_text = ""
        current_idx = start_index

        for para in paragraphs:
            if len(current_text) + len(para) + 2 > self.max_chunk_size and current_text:
                # Flush current chunk
                eqs = self.extract_equations(current_text, document_id, page)
                chunk_id = f"{document_id}-c{current_idx}"
                chunks.append(
                    Chunk(
                        chunk_id=chunk_id,
                        document_id=document_id,
                        source_id=source_id,
                        page=page,
                        section=section,
                        heading=section,
                        content=current_text.strip(),
                        equations=eqs,
                        tables=[],
                        metadata={"length": len(current_text)},
                        content_hash=Provenance.compute_hash(current_text.strip()),
                    )
                )
                current_idx += 1
                # Overlap retention
                overlap_text = current_text[-self.overlap :] if len(current_text) > self.overlap else ""
                current_text = (overlap_text + " " + para).strip()
            else:
                if current_text:
                    current_text += "\n\n" + para
                else:
                    current_text = para

        if current_text.strip():
            eqs = self.extract_equations(current_text, document_id, page)
            chunk_id = f"{document_id}-c{current_idx}"
            chunks.append(
                Chunk(
                    chunk_id=chunk_id,
                    document_id=document_id,
                    source_id=source_id,
                    page=page,
                    section=section,
                    heading=section,
                    content=current_text.strip(),
                    equations=eqs,
                    tables=[],
                    metadata={"length": len(current_text)},
                    content_hash=Provenance.compute_hash(current_text.strip()),
                )
            )

        return chunks
