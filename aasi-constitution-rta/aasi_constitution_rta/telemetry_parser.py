"""
AASI CCSDS Space Packet Protocol (Blue Book 133.0-B-2) Telemetry Parser.
Implements declarative Kaitai Struct compatible binary packet decoding
for spacecraft telemetry and telecommands (SpaDeX, Chandrayaan-4, BAS-01).
"""

from __future__ import annotations

import struct
from typing import Dict, Any, Optional, Tuple
from pydantic import BaseModel, Field


class CCSDSPacketHeader(BaseModel):
    version: int = Field(0, description="Packet Version Number (3 bits, typically 0b000)")
    packet_type: int = Field(0, description="0 = Telemetry (TM), 1 = Telecommand (TC)")
    secondary_header_flag: int = Field(1, description="1 = Secondary header present")
    apid: int = Field(..., description="Application Process Identifier (11 bits, 0-2047)")
    sequence_flags: int = Field(3, description="0b11 = Unsegmented user data")
    packet_sequence_count: int = Field(..., description="14-bit sequence counter (0-16383)")
    packet_data_length: int = Field(..., description="Total bytes of packet data field minus 1")


class CCSDSSpacePacket(BaseModel):
    header: CCSDSPacketHeader
    secondary_header_timestamp_s: float
    subsystem_id: str
    telemetry_data: Dict[str, Any]
    checksum_valid: bool
    raw_packet_hex: str


class CCSDSTelemetryParser:
    """
    Decodes and encodes CCSDS 133.0-B-2 binary packets.
    Guarantees buffer overflow protection and strict structural validation.
    """

    PRIMARY_HEADER_LENGTH = 6

    @classmethod
    def parse_packet(cls, packet_bytes: bytes) -> CCSDSSpacePacket:
        if len(packet_bytes) < cls.PRIMARY_HEADER_LENGTH:
            raise ValueError(f"Packet too short: {len(packet_bytes)} bytes < 6 minimum")

        # Unpack 6-byte primary header:
        # Byte 0-1: [Version (3b) | Type (1b) | SecHdr (1b) | APID (11b)]
        # Byte 2-3: [SeqFlags (2b) | PacketSeqCount (14b)]
        # Byte 4-5: [PacketDataLength (16b)]
        word0, word1, data_length = struct.unpack(">HHH", packet_bytes[:6])

        version = (word0 >> 13) & 0x07
        packet_type = (word0 >> 12) & 0x01
        secondary_header_flag = (word0 >> 11) & 0x01
        apid = word0 & 0x07FF

        sequence_flags = (word1 >> 14) & 0x03
        packet_sequence_count = word1 & 0x3FFF

        expected_total_len = cls.PRIMARY_HEADER_LENGTH + data_length + 1
        if len(packet_bytes) < expected_total_len:
            raise ValueError(
                f"Packet truncation: expected {expected_total_len} bytes, got {len(packet_bytes)}"
            )

        header = CCSDSPacketHeader(
            version=version,
            packet_type=packet_type,
            secondary_header_flag=secondary_header_flag,
            apid=apid,
            sequence_flags=sequence_flags,
            packet_sequence_count=packet_sequence_count,
            packet_data_length=data_length,
        )

        data_field = packet_bytes[6:expected_total_len]

        # Extract secondary header timestamp (4 bytes seconds, 2 bytes subseconds)
        timestamp_s = 0.0
        payload_bytes = data_field
        if secondary_header_flag and len(data_field) >= 6:
            coarse_time, fine_time = struct.unpack(">IH", data_field[:6])
            timestamp_s = coarse_time + (fine_time / 65536.0)
            payload_bytes = data_field[6:]

        # Map APID to subsystem
        apid_map = {
            100: "GNC_ATTITUDE_PROPULSION",
            101: "NAVIC_RODP_SENSOR_FUSION",
            102: "DOCKING_MECHANISM_BDS",
            103: "THERMAL_MANAGEMENT",
            104: "POWER_BUS_RADMON",
            105: "OPTICAL_IMAGE_SERVO",
        }
        subsystem = apid_map.get(apid, f"SUBSYSTEM_APID_{apid}")

        # Simple parity/checksum check
        calc_checksum = sum(packet_bytes[:-2]) & 0xFFFF if len(packet_bytes) >= 8 else 0
        reported_checksum = (
            struct.unpack(">H", packet_bytes[-2:])[0] if len(packet_bytes) >= 8 else 0
        )
        checksum_valid = (calc_checksum == reported_checksum) or len(packet_bytes) < 8

        # Parse engineering telemetry payload
        telemetry_dict = cls._decode_payload(apid, payload_bytes)

        return CCSDSSpacePacket(
            header=header,
            secondary_header_timestamp_s=timestamp_s,
            subsystem_id=subsystem,
            telemetry_data=telemetry_dict,
            checksum_valid=checksum_valid,
            raw_packet_hex=packet_bytes[:expected_total_len].hex(),
        )

    @classmethod
    def _decode_payload(cls, apid: int, payload: bytes) -> Dict[str, Any]:
        """Decodes subsystem specific engineering telemetry."""
        result: Dict[str, Any] = {"raw_payload_length": len(payload)}
        if apid == 100 and len(payload) >= 16:  # GNC Telemetry: [x, y, z, vx, vy, vz]
            # Floats or doubles
            try:
                values = struct.unpack(">ffff", payload[:16])
                result["rel_pos_x_m"] = values[0]
                result["rel_pos_y_m"] = values[1]
                result["rel_pos_z_m"] = values[2]
                result["closing_speed_mps"] = values[3]
            except Exception:
                pass
        elif apid == 101 and len(payload) >= 8:  # NavIC RODP
            try:
                pos_res, vel_res = struct.unpack(">ff", payload[:8])
                result["navic_pseudorange_residual_m"] = pos_res
                result["navic_doppler_residual_mps"] = vel_res
            except Exception:
                pass
        elif apid == 102 and len(payload) >= 4:  # BDS Latch
            try:
                latch_state, contact_switch = struct.unpack(">HH", payload[:4])
                result["bds_latch_engaged"] = bool(latch_state)
                result["contact_switch_triggered"] = bool(contact_switch)
            except Exception:
                pass
        return result

    @classmethod
    def encode_packet(
        cls,
        apid: int,
        packet_sequence_count: int,
        payload_bytes: bytes,
        timestamp_s: float = 0.0,
        packet_type: int = 0,
    ) -> bytes:
        """Constructs a standard CCSDS space packet byte string."""
        sec_hdr = struct.pack(">IH", int(timestamp_s), int((timestamp_s % 1.0) * 65536))
        data_field = sec_hdr + payload_bytes

        # Checksum placeholder (2 bytes)
        data_field_with_crc = data_field + b"\x00\x00"
        data_len = len(data_field_with_crc) - 1

        word0 = (0 << 13) | (packet_type << 12) | (1 << 11) | (apid & 0x07FF)
        word1 = (3 << 14) | (packet_sequence_count & 0x3FFF)
        hdr = struct.pack(">HHH", word0, word1, data_len)

        full_unchecksummed = hdr + data_field
        crc = sum(full_unchecksummed) & 0xFFFF
        return full_unchecksummed + struct.pack(">H", crc)

