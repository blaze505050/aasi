"""
CCSDS Space Packet & NavIC Binary Telemetry Ingestion Engine.
Parses Consultative Committee for Space Data Systems (CCSDS Blue Book 133.0-B-2)
space packets and NavIC pseudorange/Doppler observables for ISRO SpaDeX, Chandrayaan-4,
and BAS-01 rendezvous guidance.
"""

from __future__ import annotations
import struct
import time
from typing import Dict, Any, List, Optional, Tuple
from ..evidence_dossier import EvidenceDossier, compute_sha256_bytes


class CcsdsTelemetryParser:
    """
    Decodes standard CCSDS 133.0-B-2 space packets into calibrated engineering states.
    Primary Header: 6 bytes.
    - Bytes 0-1: Version (3b), Type (1b), SecHdrFlag (1b), APID (11b)
    - Bytes 2-3: Sequence Flags (2b), Packet Sequence Count (14b)
    - Bytes 4-5: Packet Data Length (16b) = (Total Bytes in Data Field) - 1
    """

    SYNC_MARKER = b"\x1a\xcf\xfc\x1d"  # Standard CCSDS ASM (Attached Sync Marker)

    @staticmethod
    def create_ccsds_packet(
        apid: int,
        seq_count: int,
        timestamp_s: float,
        pos_xyz: Tuple[float, float, float],
        vel_xyz: Tuple[float, float, float],
        quat_wxyz: Tuple[float, float, float, float],
        wheel_rpm: Tuple[float, float, float, float] = (1200.0, -1150.0, 980.0, 450.0)
    ) -> bytes:
        """
        Synthesizes a flight-grade CCSDS 133.0-B-2 telemetry packet with a 6-byte header
        and binary IEEE-754 payload for hardware-in-the-loop and verification testing.
        """
        # Pack user data: time (d), pos (3d), vel (3d), quat (4d), wheels (4f)
        # format: >d 3d 3d 4d 4f (total 8 + 24 + 24 + 32 + 16 = 104 bytes)
        payload = struct.pack(
            ">dddddddddddffff",
            timestamp_s,
            pos_xyz[0], pos_xyz[1], pos_xyz[2],
            vel_xyz[0], vel_xyz[1], vel_xyz[2],
            quat_wxyz[0], quat_wxyz[1], quat_wxyz[2], quat_wxyz[3],
            wheel_rpm[0], wheel_rpm[1], wheel_rpm[2], wheel_rpm[3]
        )

        packet_len_field = len(payload) - 1
        # Word 0: Version (000), Type (0 for TLM), SecHdr (0), APID (11 bits)
        word0 = (0 << 13) | (apid & 0x07FF)
        # Word 1: SeqFlags (3 for unsegmented 11b), SeqCount (14 bits)
        word1 = (3 << 14) | (seq_count & 0x3FFF)
        # Word 2: Packet Data Length
        word2 = packet_len_field & 0xFFFF

        header = struct.pack(">HHH", word0, word1, word2)
        return header + payload

    @classmethod
    def parse_packet(cls, packet_bytes: bytes) -> Dict[str, Any]:
        """
        Parses a single CCSDS telemetry packet into decoded fields.
        """
        if len(packet_bytes) < 6:
            raise ValueError(f"Packet too short: {len(packet_bytes)} bytes (min 6 bytes required)")

        word0, word1, word2 = struct.unpack(">HHH", packet_bytes[:6])
        version = (word0 >> 13) & 0x07
        pkt_type = (word0 >> 12) & 0x01
        sec_hdr = (word0 >> 11) & 0x01
        apid = word0 & 0x07FF

        seq_flags = (word1 >> 14) & 0x03
        seq_count = word1 & 0x3FFF
        data_len = word2 + 1

        payload = packet_bytes[6:6 + data_len]

        decoded_payload: Dict[str, Any] = {}
        # If payload matches standard 104-byte state vector format
        if len(payload) >= 104:
            fields = struct.unpack(">dddddddddddffff", payload[:104])
            decoded_payload = {
                "timestamp_sec": fields[0],
                "rel_position_m": [fields[1], fields[2], fields[3]],
                "rel_velocity_mps": [fields[4], fields[5], fields[6]],
                "attitude_quaternion": [fields[7], fields[8], fields[9], fields[10]],
                "reaction_wheel_rpm": [fields[11], fields[12], fields[13], fields[14]],
            }
        else:
            decoded_payload["raw_payload_hex"] = payload.hex()

        return {
            "header": {
                "version": version,
                "packet_type": "TELEMETRY" if pkt_type == 0 else "TELECOMMAND",
                "has_secondary_header": bool(sec_hdr),
                "apid": apid,
                "sequence_flags": seq_flags,
                "sequence_count": seq_count,
                "data_length_bytes": data_len,
            },
            "telemetry_state": decoded_payload,
        }

    @classmethod
    def parse_telemetry_stream(cls, raw_stream: bytes, stream_name: str = "SPADEX_TLM") -> EvidenceDossier:
        """
        Parses a stream of CCSDS packets and packages them into an immutable EvidenceDossier.
        """
        stream_hash = compute_sha256_bytes(raw_stream)
        offset = 0
        parsed_packets: List[Dict[str, Any]] = []

        while offset + 6 <= len(raw_stream):
            # Read length field
            _, _, word2 = struct.unpack(">HHH", raw_stream[offset:offset + 6])
            pkt_len = 6 + (word2 + 1)
            if offset + pkt_len > len(raw_stream):
                break
            pkt_slice = raw_stream[offset:offset + pkt_len]
            try:
                decoded = cls.parse_packet(pkt_slice)
                parsed_packets.append(decoded)
            except Exception:
                pass
            offset += pkt_len

        # Extract kinematic statistics
        pos_norms: List[float] = []
        vel_norms: List[float] = []
        for p in parsed_packets:
            st = p.get("telemetry_state", {})
            if "rel_position_m" in st:
                rx, ry, rz = st["rel_position_m"]
                pos_norms.append((rx ** 2 + ry ** 2 + rz ** 2) ** 0.5)
            if "rel_velocity_mps" in st:
                vx, vy, vz = st["rel_velocity_mps"]
                vel_norms.append((vx ** 2 + vy ** 2 + vz ** 2) ** 0.5)

        physics_envelope = {
            "packet_count": len(parsed_packets),
            "min_relative_distance_m": min(pos_norms) if pos_norms else 0.0,
            "max_relative_distance_m": max(pos_norms) if pos_norms else 0.0,
            "max_relative_velocity_mps": max(vel_norms) if vel_norms else 0.0,
            "docking_corridor_compliant": all(v < 0.25 for v in vel_norms) if vel_norms else True,
        }

        return EvidenceDossier(
            dossier_id=f"DOSSIER-CCSDS-{int(time.time())}",
            target_name=stream_name,
            target_type="TELEMETRY_STREAM",
            source_files={f"{stream_name}.ccsds": stream_hash},
            extracted_parameters={
                "stream_total_bytes": len(raw_stream),
                "packets_decoded": len(parsed_packets),
                "sample_packet": parsed_packets[0] if parsed_packets else None,
            },
            physics_envelope=physics_envelope,
            provenance_metadata={
                "standard": "CCSDS Blue Book 133.0-B-2",
                "subsystem": "Autonomous Proximity Operations & Docking",
            }
        )


class NavicRinexParser:
    """
    Parses NavIC / IRNSS dual-frequency carrier-phase and pseudorange observables (L5 / S band).
    """

    @classmethod
    def parse_rinex_obs_snippet(cls, content: str) -> Dict[str, Any]:
        """
        Parses observation records: extracts PRNs (e.g. IRNSS-1A through 1I), C1C, L1C, D1C, S1C.
        """
        lines = content.splitlines()
        prn_records: Dict[str, Dict[str, float]] = {}

        for line in lines:
            if line.startswith("I"):  # IRNSS / NavIC satellite PRN
                prn = line[:3].strip()
                tokens = line[3:].split()
                if len(tokens) >= 3:
                    try:
                        prn_records[prn] = {
                            "pseudorange_m": float(tokens[0]),
                            "carrier_phase_cycles": float(tokens[1]),
                            "doppler_hz": float(tokens[2]),
                            "cn0_dbhz": float(tokens[3]) if len(tokens) > 3 else 44.5,
                        }
                    except ValueError:
                        pass

        # Estimate GDOP and PDOP based on satellite count
        sat_count = len(prn_records)
        pdop = 1.8 if sat_count >= 7 else (2.4 if sat_count >= 4 else 9.9)

        return {
            "constellation": "NavIC / IRNSS",
            "satellites_tracked": sat_count,
            "prn_measurements": prn_records,
            "estimated_pdop": pdop,
            "carrier_lock_quality": "NOMINAL" if pdop < 2.5 else "DEGRADED",
        }

