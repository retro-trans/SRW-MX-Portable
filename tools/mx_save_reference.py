"""Known PS2 MX integrity/extension behavior; NOT a PS2/PSP converter.

Pure byte operations only. Callers must identify the game/build/profile first:
size and these additive checksums do not authenticate a save's identity.
"""
import struct

SIZES = (54272, 138240)
BASE = 0x78945612
MAGIC = 0x4442584D  # ASCII MXBD in little endian
VERSION = 1


def checksum_words(payload):
    if len(payload) not in SIZES:
        raise ValueError("Unsupported PS2 payload size")
    words = struct.unpack(f"<{len(payload) // 4}I", payload)
    return ((BASE + sum(words[-256:-2])) & 0xFFFFFFFF,
            (BASE + sum(words[:-256])) & 0xFFFFFFFF)


def validate_ps2(payload):
    expected = checksum_words(payload)
    stored = struct.unpack_from("<2I", payload, len(payload) - 8)
    if stored != expected:
        raise ValueError("PS2 integrity check failed")
    return expected


def inspect_balance(payload):
    validate_ps2(payload)
    marker = struct.unpack_from("<3I", payload, len(payload) - 32)
    if marker == (0, 0, 0):
        return {"status": "absent", "native_mode": 0}
    if marker[0] == MAGIC and marker[1] == VERSION and marker[2] in (0, 1):
        return {"status": "valid", "native_mode": marker[2]}
    # Native code falls back to Original; a converter must refuse to edit it.
    return {"status": "unsupported", "native_mode": 0,
            "raw_words": list(marker)}


def _replace_marker(payload, marker):
    if inspect_balance(payload)["status"] == "unsupported":
        raise ValueError("Unknown extension/padding; refusing to overwrite")
    result = bytearray(payload)
    struct.pack_into("<3I", result, len(result) - 32, *marker)
    struct.pack_into("<2I", result, len(result) - 8, *checksum_words(result))
    validate_ps2(result)
    return bytes(result)


def with_balance(payload, mode):
    """Stamp an already identified supported PS2 save; preserve other bytes."""
    if type(mode) is not int or mode not in (0, 1):
        raise ValueError("Mode must be integer 0 (Original) or 1 (PSP Harder)")
    return _replace_marker(payload, (MAGIC, VERSION, mode))


def without_balance(payload):
    """Clear only a recognized extension (not a cross-platform conversion)."""
    return _replace_marker(payload, (0, 0, 0))
