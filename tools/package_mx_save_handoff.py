"""Package public engineering evidence, never private saves or ROMs."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import zipfile

import mx_save_reference as mx

ROOT = Path(__file__).resolve().parents[1]
VERSION = "0.1.0"
BUILD = "0.1.14"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def write(path, data):
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main():
    stage = ROOT / "work/build/handoff" / f"mx_save_converter_{VERSION}"
    archive = ROOT / "work/output" / f"SRWMX_SaveConverter_Handoff_{VERSION}.zip"
    if stage.exists() or archive.exists():
        raise RuntimeError("Handoff output already exists; preserve it or choose a new version")
    metadata = ROOT / "work/build/ps2" / f"setup_save_{BUILD}"
    difficulty = read(metadata / "difficulty.json")
    stage30 = read(metadata / "stage30.json")
    prologue = read(metadata / "prologue.json")
    comparison = read(ROOT / "work/output/ps2_psp_save_comparison.json")
    validation = []
    for pair in comparison["pairs"]:
        directory = pair["ps2"]["directory"]
        source = ROOT / "work/source/save_compare/ps2" / directory / directory
        original_hash = digest(source)
        if original_hash != pair["ps2"]["sha256"]:
            raise RuntimeError("Private reference fixture changed")
        payload = source.read_bytes()
        mx.validate_ps2(payload)
        for mode in (0, 1):
            edited = mx.with_balance(payload, mode)
            assert mx.inspect_balance(edited)["native_mode"] == mode
            assert mx.without_balance(edited) == payload
        assert digest(source) == original_hash
        validation.append({"kind": pair["type"], "sha256": original_hash,
                           "checksum_pass": True, "balance_0_and_1_pass": True,
                           "clear_roundtrip_pass": True, "source_unchanged": True,
                           "note": "In-memory marker edits only; not emulator acceptance"})

    sources = {
        "README.md": "docs/retro_trans_tools_mx_save_handoff.md",
        "reference/mx_save_reference.py": "tools/mx_save_reference.py",
        "reference/ps2_memcard_read.py": "tools/ps2_memcard_read.py",
        "tests/test_mx_save_reference.py": "tools/test_mx_save_reference.py",
        "context/save_conversion_assessment.md": "docs/save_conversion_assessment.md",
        "context/ps2_difficulty.md": "docs/ps2_difficulty.md",
        "context/ps2_stage30_port.md": "docs/ps2_stage30_port.md",
        "context/ps2_prologue_fixes.md": "docs/ps2_prologue_fixes.md",
    }
    for dest, source in sources.items():
        target = stage / dest
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / source, target)

    pairs = []
    for pair in comparison["pairs"]:
        pairs.append({"kind": pair["type"], "ps2": pair["ps2"],
                      "psp": {k: v for k, v in pair["psp"].items()
                              if k not in ("detail", "zero_bytes")}})
        pairs[-1]["ps2"].pop("zero_bytes", None)
    facts = {
        "handoff_version": VERSION, "date": "2026-10-06",
        "source_game_build": BUILD,
        "target_repository": "https://github.com/retro-trans/retro-trans-tools",
        "target_inspected_commit": "64d4deec88e045d5cddef2d008d0c3df2ad193af",
        "conversion_implemented": False, "cross_platform_emulator_acceptance": False,
        "matched_checkpoint_pairs_available": False,
        "observed_containers": pairs,
        "ps2_checksum": {"endianness": "little", "word_bits": 32,
                         "seed": "0x78945612", "overflow": "modulo 2^32",
                         "tail_checksum_stored": "N-8", "tail_region": "[N-1024,N-8)",
                         "main_checksum_stored": "N-4", "main_region": "[0,N-1024)"},
        "ps2_difficulty_extension": {
            "offset": "N-32", "struct": "<3I", "magic_ascii": "MXBD",
            "magic": "0x4442584d", "format_version": 1,
            "modes": {"0": "PS2 Original", "1": "PSP Harder"},
            "scenario_offset": "0xd3e0", "system_offset": "0x21be0",
            "native_invalid_marker_fallback": 0,
            "converter_unknown_marker_policy": "reject editing",
            "stock_ps2_honors_marker": False, "psp_honors_marker": False,
            "companion_consistency": "Only pair saves after confirming same campaign",
        },
        "ui_policy": {
            "patched_ps2_choices": ["Keep source balance", "PS2 Original", "PSP Harder"],
            "keep_from_psp": 1, "keep_from_valid_ps2": "preserve marker",
            "keep_from_legacy_ps2": 0,
            "stock_ps2": "Original only; disable PSP Harder",
            "psp_output": "Native PSP balance only",
            "new_game_prompt": "After protagonist/unit setup, choose Finish Setup, then game balance",
            "imported_save": "Restore stamped mode on load; no New Game prompt needed",
        },
        "balance_lookup": {"file": "balance_changes.json", "records": len(difficulty["balance_changes"]),
                           "changed_enemy_hp": difficulty["enemy_hp_changes"],
                           "changed_rewards": difficulty["reward_changes"],
                           "stored_funds": "preserve; do not rescale",
                           "battle_current_hp_conversion": "unmapped; not supported"},
        "campaign_port": {
            "prologue_scenario_ids": prologue["scenario_ids"],
            "prologue_location_ids": prologue["location_ids"],
            "first_chapter_group_order": [4, 0, 2],
            "stage30_scenario_id": stage30["scenario_id"],
            "stage30_location_id": stage30["location_id"], "chapter": stage30["chapter"],
            "chapter7_locations": stage30["location_order"],
            "chapter7_groups": [0, 2, 4, 6, 8, 12, 10],
            "story_order": stage30["story_order"],
            "added_unit": stage30["added_unit"],
            "added_pilot_ids": [431, 432, 433],
            "existing_save_migration": stage30["existing_save_migration"],
            "file_offsets_for_progression": "unmapped",
            "psp_exclusive_to_stock_ps2": "block until a verified checkpoint mapping exists",
        },
        "psp_crypto": {"observed_mode": 3, "header_bytes": 16,
                       "sample_file_mac_verified": True,
                       "encrypted_writer_implemented": False,
                       "sfo_writer_implemented": False,
                       "game_key_in_bundle": False,
                       "analysis_key_location": comparison["psp_game_key_location"],
                       "implementation_license": "Review PPSSPP GPL-2.0-or-later and dependencies before reuse"},
        "unknowns": ["Scenario field offsets and record ID mapping", "All slot naming rules",
                     "Matched campaign progression/history/clear flags", "Native string encoding and user names",
                     "System data and battle suspend scope", "PSP three favorites versus PS2 one",
                     "Validated writable PS2 import container and ECC", "PSP encryption and fresh SFO metadata"],
        "profile_identity": {
            "game_id": "SLPS-25345 (shared by stock and English port; insufficient alone)",
            "patched_iso_sha256": "92b871792cbb936d74b72394d9d97cd1e73022bc3574c2d113608e4ee8cde14f",
            "patched_elf_sha256": "beaf6cbd5d025b06dc358e757a4fbaa95414f9d35e2fdfabe2dc63a3184b5eee",
        },
    }
    write(stage / "facts.json", facts)
    write(stage / "balance_changes.json", {"game_build": BUILD,
          "scope": "Native lookup values, not serialized save field offsets",
          "records": difficulty["balance_changes"]})
    tests = subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"],
                           cwd=stage, capture_output=True, text=True)
    if tests.returncode:
        raise RuntimeError(tests.stdout + tests.stderr)
    write(stage / "validation.json", {"synthetic_tests_pass": True, "test_output": tests.stderr,
                                     "private_fixture_checks": validation,
                                     "conversion_or_in_game_acceptance": False})
    # Exclude interpreter caches; only explicit public source/evidence files enter the ZIP.
    files = sorted(p for p in stage.rglob("*") if p.is_file() and "__pycache__" not in p.parts)
    manifest = [{"path": p.relative_to(stage).as_posix(), "bytes": p.stat().st_size,
                 "sha256": digest(p)} for p in files]
    write(stage / "manifest.json", {"handoff_version": VERSION, "files": manifest})
    files.append(stage / "manifest.json")
    archive.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(archive, "x", zipfile.ZIP_DEFLATED) as out:
        for path in files:
            out.write(path, path.relative_to(stage).as_posix())
    with zipfile.ZipFile(archive) as out:
        assert out.testzip() is None
        for entry in manifest:
            assert hashlib.sha256(out.read(entry["path"])).hexdigest() == entry["sha256"]
    print(json.dumps({"archive": str(archive), "sha256": digest(archive),
                      "files": len(files), "tests_pass": True}, indent=2))


if __name__ == "__main__":
    main()
