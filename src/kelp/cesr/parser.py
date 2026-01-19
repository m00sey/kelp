"""CESR stream parser using keripy for proper CESR 1.0 parsing."""

from keri.core.coring import Matter, Seqner
from keri.core.counting import Counter
from keri.core.indexing import Siger
from keri.core.serdering import Serder

from .events import Attachment, Event

# Counter code names from CESR 1.0 spec
COUNTER_NAMES = {
    "-A": "Controller Indexed Sigs",
    "-B": "Witness Indexed Sigs",
    "-C": "Nontransferable Receipt Couples",
    "-D": "Transferable Receipt Quadruples",
    "-E": "First Seen Replay Couples",
    "-F": "Trans Indexed Sig Groups",
    "-G": "Seal Source Couples",
    "-H": "Trans Last Indexed Sig Groups",
    "-I": "Seal Source Triples",
    "-J": "SAD Path Sig Groups",
    "-K": "Root SAD Path Sig Groups",
    "-L": "Pathed Material Group",
    "-V": "Attachment Group",
    "-W": "Generic Group",
    "-Z": "ESSR Payload Group",
}


class CESRParser:
    """Parser for CESR-encoded streams using keripy."""

    def __init__(self):
        self.events: list[Event] = []

    def parse(self, data: bytes | str) -> list[Event]:
        """Parse a CESR stream and extract all events with attachments."""
        if isinstance(data, str):
            data = data.encode("utf-8")

        self.events = []
        offset = 0

        while offset < len(data):
            # Skip whitespace
            while offset < len(data) and data[offset : offset + 1] in b" \t\n\r":
                offset += 1

            if offset >= len(data):
                break

            # Look for JSON start
            if data[offset : offset + 1] != b"{":
                offset += 1
                continue

            try:
                # Parse as a KERI event using Serder
                serder = Serder(raw=data[offset:], strip=False)
                event_size = serder.size

                # Extract raw JSON
                raw_json = data[offset : offset + event_size].decode("utf-8")

                # Parse attachments after the event
                attach_offset = offset + event_size
                attachments, attach_end = self._parse_attachments(data, attach_offset)

                event = Event(
                    raw=raw_json,
                    data=serder.sad,
                    attachments=attachments,
                )
                self.events.append(event)

                offset = attach_end

            except Exception:
                # Not a valid event at this position, skip ahead
                offset += 1

        return self.events

    def _parse_attachments(self, data: bytes, offset: int) -> tuple[list[Attachment], int]:
        """Parse attachments following an event using keripy Counter."""
        attachments = []
        current = offset

        while current < len(data):
            # Skip whitespace
            while current < len(data) and data[current : current + 1] in b" \t\n\r":
                current += 1

            if current >= len(data):
                break

            # Check if we hit a new event (starts with '{')
            if data[current : current + 1] == b"{":
                break

            # Try to parse a counter code
            if data[current : current + 1] == b"-":
                try:
                    counter = Counter(qb64b=data[current:], strip=False)
                    code = counter.code
                    count = counter.count
                    counter_size = counter.fullSize

                    # Get the material that follows the counter
                    material_start = current + counter_size
                    materials, material_end = self._extract_counter_material(
                        data, material_start, code, count
                    )

                    # Get human-readable name
                    name = COUNTER_NAMES.get(code, f"Counter {code}")

                    raw_attachment = data[current:material_end].decode("utf-8", errors="replace")

                    attachments.append(
                        Attachment(
                            code=code,
                            count=count,
                            name=name,
                            raw=raw_attachment,
                            materials=materials,
                        )
                    )

                    current = material_end

                except Exception:
                    # Not a valid counter, skip this byte
                    current += 1
            else:
                # Not a counter, check if it's CESR primitive material
                char = data[current : current + 1]
                if char and (char[0:1].isalnum() or char in b"-_"):
                    # Collect raw CESR primitives until next event or counter
                    raw_start = current
                    while current < len(data):
                        if data[current : current + 1] == b"{":
                            break
                        if data[current : current + 1] == b"-":
                            # Check if it looks like a counter
                            try:
                                Counter(qb64b=data[current:], strip=False)
                                break  # It's a valid counter, stop here
                            except Exception:
                                pass
                        current += 1

                    if current > raw_start:
                        raw = data[raw_start:current].decode("utf-8", errors="replace")
                        if raw.strip():
                            attachments.append(
                                Attachment(
                                    code="RAW",
                                    count=0,
                                    name="Raw CESR Material",
                                    raw=raw,
                                    materials=[],
                                )
                            )
                else:
                    break

        return attachments, current

    def _extract_counter_material(
        self, data: bytes, offset: int, code: str, count: int
    ) -> tuple[list[dict], int]:
        """Extract the material following a counter code."""
        materials = []
        current = offset

        try:
            if code in ("-A", "-B"):  # Indexed Sigs (Controller or Witness)
                for _ in range(count):
                    if current >= len(data):
                        break
                    siger = Siger(qb64b=data[current:], strip=False)
                    materials.append(
                        {
                            "type": "indexed_sig",
                            "index": siger.index,
                            "ondex": getattr(siger, "ondex", None),
                            "code": siger.code,
                            "qb64": siger.qb64,
                        }
                    )
                    current += len(siger.qb64)

            elif code == "-C":  # Nontransferable Receipt Couples
                for _ in range(count):
                    if current >= len(data):
                        break
                    # Couple: prefixer + cigar
                    prefixer = Matter(qb64b=data[current:], strip=False)
                    current += len(prefixer.qb64)
                    cigar = Matter(qb64b=data[current:], strip=False)
                    current += len(cigar.qb64)
                    materials.append(
                        {
                            "type": "receipt_couple",
                            "prefix": prefixer.qb64,
                            "signature": cigar.qb64,
                        }
                    )

            elif code == "-G":  # Seal Source Couples
                for _ in range(count):
                    if current >= len(data):
                        break
                    # Couple: seqner + saider
                    seqner = Seqner(qb64b=data[current:], strip=False)
                    current += len(seqner.qb64)
                    saider = Matter(qb64b=data[current:], strip=False)
                    current += len(saider.qb64)
                    materials.append(
                        {
                            "type": "seal_source",
                            "sn": seqner.sn,
                            "said": saider.qb64,
                        }
                    )

            elif code == "-E":  # First Seen Replay Couples
                for _ in range(count):
                    if current >= len(data):
                        break
                    # Couple: seqner + dater
                    seqner = Seqner(qb64b=data[current:], strip=False)
                    current += len(seqner.qb64)
                    dater = Matter(qb64b=data[current:], strip=False)
                    current += len(dater.qb64)
                    materials.append(
                        {
                            "type": "first_seen",
                            "sn": seqner.sn,
                            "datetime": dater.qb64,
                        }
                    )

            else:
                # For other counter types, try to parse as generic Matter objects
                # This is a fallback that should work for most CESR primitives
                for _ in range(count):
                    if current >= len(data):
                        break
                    try:
                        matter = Matter(qb64b=data[current:], strip=False)
                        materials.append(
                            {
                                "type": "matter",
                                "code": matter.code,
                                "qb64": matter.qb64,
                            }
                        )
                        current += len(matter.qb64)
                    except Exception:
                        break

        except Exception:
            # If parsing fails, return what we have
            pass

        return materials, current


def parse_cesr(data: bytes | str) -> list[Event]:
    """Convenience function to parse CESR data."""
    parser = CESRParser()
    return parser.parse(data)
