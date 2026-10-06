"""Synthetic tests only; no game saves or ROM bytes are distributed."""
import struct
import sys
from pathlib import Path
import unittest

# Works in the source tools directory and in the portable tests/reference layout.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "reference"))
import mx_save_reference as mx


def fixture(size):
    data = bytearray((i * 13 + 7) % 256 for i in range(size))
    data[-32:-20] = bytes(12)
    seal(data)
    return bytes(data)


def seal(data):
    # Deliberately independent region implementation for expected integrity.
    def total(start, end):
        return (0x78945612 + sum(int.from_bytes(data[i:i+4], "little")
                               for i in range(start, end, 4))) & 0xFFFFFFFF
    struct.pack_into("<II", data, len(data)-8,
                     total(len(data)-1024, len(data)-8), total(0, len(data)-1024))


class ReferenceTests(unittest.TestCase):
    def test_checksum_and_modes_preserve_unrelated_bytes(self):
        for size in mx.SIZES:
            with self.subTest(size=size):
                source = fixture(size)
                self.assertEqual(mx.inspect_balance(source)["status"], "absent")
                for mode in (0, 1):
                    result = mx.with_balance(source, mode)
                    self.assertEqual(len(result), size)
                    self.assertEqual(mx.inspect_balance(result),
                                     {"status": "valid", "native_mode": mode})
                    self.assertEqual(result[:size-32], source[:size-32])
                    self.assertEqual(result[size-20:size-8], source[size-20:size-8])
                    self.assertEqual(mx.without_balance(result), source)
                self.assertEqual(source, fixture(size))

    def test_corruption_in_every_integrity_region(self):
        for size in mx.SIZES:
            for offset in (0, size-1024, size-9, size-8, size-1):
                with self.subTest(size=size, offset=offset):
                    data = bytearray(fixture(size))
                    data[offset] ^= 1
                    with self.assertRaises(ValueError):
                        mx.with_balance(data, 1)

    def test_unknown_extensions_are_not_overwritten(self):
        for marker in ((mx.MAGIC, 2, 1), (mx.MAGIC, 1, 2), (1, 0, 0)):
            data = bytearray(fixture(mx.SIZES[0]))
            struct.pack_into("<3I", data, len(data)-32, *marker)
            seal(data)
            self.assertEqual(mx.inspect_balance(data)["native_mode"], 0)
            for fn in (lambda: mx.with_balance(data, 1), lambda: mx.without_balance(data)):
                with self.assertRaises(ValueError):
                    fn()

    def test_bad_lengths_and_modes(self):
        for data in (b"", bytes(54271), bytes(54288)):
            with self.assertRaises(ValueError):
                mx.validate_ps2(data)
        for mode in (-1, 2, True, "1", None):
            with self.assertRaises(ValueError):
                mx.with_balance(fixture(mx.SIZES[0]), mode)


if __name__ == "__main__":
    unittest.main()
