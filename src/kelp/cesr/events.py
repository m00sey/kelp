"""Event and attachment dataclasses for CESR parsing."""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Attachment:
    """Represents a CESR attachment (signatures, receipts, etc.)."""

    code: str  # The CESR counter code (e.g., "-A")
    count: int  # Number of items
    name: str  # Human-readable name
    raw: str  # Raw CESR-encoded data
    materials: list[dict] = field(default_factory=list)  # Parsed materials

    @property
    def type_label(self) -> str:
        """Human-readable label for the attachment type."""
        return self.name


@dataclass
class Event:
    """Represents a KERI event extracted from a CESR stream."""

    raw: str  # Raw JSON string
    data: dict[str, Any]  # Parsed JSON data
    attachments: list[Attachment] = field(default_factory=list)

    @property
    def version(self) -> str:
        """Event version string."""
        return self.data.get("v", "")

    @property
    def type(self) -> str:
        """Event type (icp, rot, ixn, dip, drt, etc.)."""
        return self.data.get("t", "")

    @property
    def digest(self) -> str:
        """Event SAID/digest."""
        return self.data.get("d", "")

    @property
    def identifier(self) -> str:
        """AID/identifier for this event."""
        return self.data.get("i", "")

    @property
    def sequence(self) -> int:
        """Sequence number as integer."""
        s = self.data.get("s", 0)
        if isinstance(s, int):
            return s
        # Fallback for string (KERI uses hex strings)
        try:
            return int(s, 16)
        except ValueError:
            return 0

    @property
    def sequence_hex(self) -> str:
        """Sequence number as hex string."""
        s = self.data.get("s", 0)
        if isinstance(s, int):
            return format(s, "x")
        return str(s)

    @property
    def prior(self) -> str:
        """Prior event digest."""
        return self.data.get("p", "")

    @property
    def anchors(self) -> list[dict]:
        """Anchor seals if present."""
        return self.data.get("a", [])

    @property
    def type_label(self) -> str:
        """Human-readable event type label."""
        labels = {
            "icp": "Inception",
            "rot": "Rotation",
            "ixn": "Interaction",
            "dip": "Delegated Inception",
            "drt": "Delegated Rotation",
            "rct": "Receipt",
            "qry": "Query",
            "rpy": "Reply",
            "pro": "Prod",
            "bar": "Bare",
            "exn": "Exchange",
            "vcp": "VC Registry Inception",
            "vrt": "VC Registry Rotation",
            "iss": "VC Issuance",
            "rev": "VC Revocation",
            "bis": "Backer VC Issuance",
            "brv": "Backer VC Revocation",
        }
        return labels.get(self.type, self.type.upper())

    @property
    def short_digest(self) -> str:
        """Truncated digest for display."""
        d = self.digest
        return f"{d[:12]}..." if len(d) > 12 else d

    @property
    def short_identifier(self) -> str:
        """Truncated identifier for display."""
        i = self.identifier
        return f"{i[:16]}..." if len(i) > 16 else i

    @property
    def protocol(self) -> str:
        """Protocol identifier (KERI, ACDC, etc.)."""
        v = self.version
        return v[:4] if len(v) >= 4 else ""

    @property
    def cesr_version(self) -> str:
        """CESR version as 'major.minor' (e.g., '1.0', '2.0')."""
        v = self.version
        if len(v) >= 6:
            major = v[4:5]
            minor = v[5:6]
            return f"{major}.{minor}"
        return ""

    @property
    def cesr_major_version(self) -> str:
        """CESR major version number (e.g., '1', '2')."""
        v = self.version
        return v[4:5] if len(v) >= 5 else ""

    @property
    def serialization(self) -> str:
        """Serialization format (JSON, CBOR, MGPK)."""
        v = self.version
        return v[6:10] if len(v) >= 10 else ""
