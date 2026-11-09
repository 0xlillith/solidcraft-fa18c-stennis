#!/usr/bin/env python3
"""Package only the completed F/A-18C Stennis RC3 realism project.

Run after the final native scenes, documentation and receipts are ready:

    python3 source/package_project.py --plan
    python3 source/package_project.py
    python3 source/package_project.py --verify ../FA18C-Stennis-RC3-Realism-20261109.tar.xz

The standard-library LZMA compressor uses one thread. The default dictionary is
128 MiB to retain substantial repeated mesh data across neighboring native scenes.
No Solidcraft process is started, no downloads occur, and no rendering occurs.
Existing research files remain unchanged; portable reference views are staged.
Use --compression-level 1 or 2 for faster compression while preserving the dictionary.

The archive contains an embedded FILE_INDEX.json and SHA256SUMS.txt. Its own
checksum and verification receipt are external sidecars, avoiding circular hashes.
SOURCE_DATE_EPOCH or --epoch can fix metadata timestamps for repeatable packaging.
"""
from __future__ import annotations

import argparse
import errno
import hashlib
import json
import lzma
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import stat
import sys
import tarfile
import tempfile
import time
from datetime import datetime, timezone

MIB = 1024 * 1024
CHUNK = 4 * MIB
PACKAGE_VERSION = 1
NATIVE_PREFIX = "FA18C_Stennis_RC3_"
MASTER_NAME = NATIVE_PREFIX + "Master.sc"
FINAL_NATIVE_NAMES = {
    MASTER_NAME, "FA18C_RC3_Aircraft.sc", "FA18C_RC3_Cockpit.sc",
    "FA18C_RC3_Internal_Systems.sc", "FA18C_RC3_Structure.sc",
    "F404_RC3_Engines.sc",
}
OBSOLETE_SOURCE = {
    "native_build.py", "native_preview.py",
    "native_presentation.py", "native_variants.py",
}
BASELINE_REPORTS = {
    "F404_INTEGRATION_CLEARANCE.json",
    "INTERNAL_EQUIPMENT_CLEARANCE_AUDIT.json",
}
EXCLUDED_RECEIPTS = {
    "scene_manifest.json", "native-state.json", "command-timings.json",
    "before.json", "after.json", "events.json", "calls.json",
    "mcp-log.json", "mcp-transcript.json", "FILE_INDEX.json",
    "PACKAGE_VALIDATION.json",
}
BLOCKED_DIRS = {
    "runtime", "development", "dev", "__pycache__", ".git", ".venv",
    "venv", "node_modules", "logs", "log", "cache", ".cache",
    "scratch", "tmp", "backup", "backups",
}
METADATA_NAMES = {"FILE_INDEX.json", "SHA256SUMS.txt"}
ROOT_DOC_SUFFIXES = {".md", ".txt", ".pdf", ".html"}
ALLOWED_TREES = {
    "native", "source", "obj", "research", "references",
    "verification", "validation",
}


def emit(stage, **values):
    print(json.dumps({"stage": stage, **values}, ensure_ascii=False), flush=True)


def sha256_file(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(CHUNK), b""):
            digest.update(block)
    return digest.hexdigest()


def safe_relative(value):
    """Accept a normalized portable relative file path, never traversal."""
    if not isinstance(value, str) or not value:
        raise ValueError("Empty or non-string package path")
    if any(ch in value for ch in ("\0", "\n", "\r", "\t", "\\")):
        raise ValueError("Unsafe characters in package path: " + repr(value))
    p = PurePosixPath(value)
    if not p.parts or p.is_absolute() or any(part in ("", ".", "..") for part in p.parts):
        raise ValueError("Unsafe package path: " + value)
    if str(p) != value or ":" in p.parts[0]:
        raise ValueError("Non-normalized package path: " + value)
    return value


def blocked_path(relative):
    p = PurePosixPath(relative)
    for part in p.parts[:-1]:
        lowered = part.lower()
        if lowered in BLOCKED_DIRS or "smoke" in lowered or "fixture" in lowered:
            return True
        if lowered.startswith(("fa18c-stennis-showcase", "fa18c_stennis_showcase",
                               "fa18c-stennis-chat-files")):
            return True
    return False


def validate_member_policy(relative):
    """Reject excluded trees, legacy helpers, fixtures, or nested projects."""
    safe_relative(relative)
    p = PurePosixPath(relative)
    if blocked_path(relative):
        raise ValueError("Excluded path in archive: " + relative)
    if len(p.parts) > 1 and p.parts[0] not in ALLOWED_TREES:
        raise ValueError("Unexpected project subtree: " + relative)
    if p.suffix.lower() == ".sc":
        if len(p.parts) != 2 or p.parts[0] != "native":
            raise ValueError("A nonfinal native scene was selected: " + relative)
        if any(word in p.name.lower() for word in ("smoke", "fixture", "test", "probe")):
            raise ValueError("A native fixture was selected: " + relative)
    if p.parts[0] == "source" and p.name in OBSOLETE_SOURCE:
        raise ValueError("Obsolete source helper was selected: " + relative)
    if p.suffix.lower() == ".pdf" and p.parts[0] in {"research", "references"} and relative not in PUBLIC_DOMAIN_NASA_PDFS:
        raise ValueError("This reference is link-only in the portable archive: " + relative)
    if p.suffix.lower() in {".log", ".jsonl", ".pyc", ".pyo", ".xz", ".gz", ".zip", ".zst"}:
        raise ValueError("Log, runtime archive or cache selected: " + relative)


def atomic_write(path, contents):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix="." + path.name + ".", dir=path.parent)
    tmp = Path(name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(contents)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp, path)
    finally:
        if tmp.exists():
            tmp.unlink()


PUBLIC_DOMAIN_NASA_PDFS = {
    "research/primary/nasa-fa18-reference.pdf",
    "research/primary/nasa-tm88273-f404-survey.pdf",
    "research/primary/nasa-tm4140-f404-measurement.pdf",
    "research/primary/nasa-tm87132-materials.pdf",
}
SOURCE_TITLES = {
    "nasa-fa18-reference.pdf": "NASA F/A-18 mission-support aircraft fact sheet",
    "nasa-tm88273-f404-survey.pdf": "NASA TM 88273: F404 exhaust-gas survey",
    "nasa-tm4140-f404-measurement.pdf": "NASA TM 4140: F404 in-flight thrust measurement",
    "nasa-tm87132-materials.pdf": "NASA TM 87132: aircraft engine composite materials",
    "nasa-19830025689-wing-structure.pdf": "Garbo / McDonnell: composite wing structure, NASA record 19830025689",
    "nasa-cr182228-duct-development.pdf": "GE / NASA CR-182228: PMR graphite engine duct development",
    "ge-f404-family-2020.pdf": "GE Aerospace F404 family datasheet",
    "ge-icas1984-f404.pdf": "GE authors, ICAS 1984: F404 new standards for fighter aircraft engines",
    "martin-baker-naces-2025.pdf": "Martin-Baker NACES manufacturer datasheet",
    "dcs-fa18c-official-guide.pdf": "Eagle Dynamics DCS F/A-18C official guide",
}


def reference_records(project):
    path = project / "research" / "PRIMARY_SOURCE_DOWNLOADS.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    rows = data.get("sources", []) if isinstance(data, dict) else data
    result = []
    for row in rows:
        url = row.get("url") or row.get("source_url")
        name = row.get("reference_filename") or PurePosixPath(row.get("file", row.get("archive_file", ""))).name
        if not name or not isinstance(url, str) or not url.startswith(("https://", "http://")):
            continue
        result.append({
            "reference_filename": name,
            "title": row.get("title") or SOURCE_TITLES.get(name, name),
            "source_url": url,
            "reference_path": "research/primary/" + name,
            "accessed": row.get("accessed", "2026-11-09"),
        })
    return result


def prepare_portable_references(project, chosen, stage):
    """Stage portable reference views without modifying original research files."""
    records = reference_records(project)
    staged_links = []
    for relative in sorted(PUBLIC_DOMAIN_NASA_PDFS & chosen.keys()):
        original = chosen[relative]
        if original.is_symlink():
            target = original.resolve(strict=True)
            staged = stage / relative
            staged.parent.mkdir(parents=True, exist_ok=True)
            try:
                os.link(target, staged, follow_symlinks=True)
                method = "staged hardlink"
            except OSError as error:
                if error.errno not in {
                    errno.EXDEV, errno.EPERM, errno.EACCES,
                    errno.ENOTSUP, errno.EOPNOTSUPP, errno.EMLINK,
                }:
                    raise
                shutil.copy2(target, staged)
                method = "staged copy"
            if sha256_file(original) != sha256_file(staged):
                raise ValueError("Staged NASA PDF failed its content check: " + relative)
            chosen[relative] = staged
            staged_links.append({"path": relative, "method": method, "original_left_unchanged": True})

    included = []
    link_only = []
    inventory = []
    for record in records:
        relative = record["reference_path"]
        portable = {k: record[k] for k in ("reference_filename", "title", "source_url", "accessed")}
        if relative in PUBLIC_DOMAIN_NASA_PDFS and relative in chosen:
            path = chosen[relative]
            portable.update({
                "archive_status": "included public-domain NASA reference PDF",
                "archive_file": relative,
                "bytes": path.stat().st_size,
                "sha256": sha256_file(path),
            })
            included.append(portable)
        else:
            reason = "Copyrighted manufacturer, simulator, or conference work retained as a source URL."
            if record["reference_filename"].startswith("nasa-"):
                reason = "Externally authored NASA-hosted or unavailable paper retained as a source URL without asserting public-domain status."
            portable.update({"archive_status": "link only; full PDF is not included", "reason": reason})
            link_only.append(portable)
        inventory.append(portable)

    intro = (
        "> Portable archive source availability: only the NASA PDFs explicitly listed in "
        "REFERENCE_LINKS.md are included. Manufacturer, simulator, conference and "
        "externally authored NASA-hosted works are supplied as source links. "
        "The original Galactica research files were not changed.\n\n"
    )
    by_name = {r["reference_filename"]: r for r in records}
    transformed_docs = []
    for relative, original in list(chosen.items()):
        if original.suffix.lower() != ".md":
            continue
        content = original.read_text(encoding="utf-8")
        rewritten = content
        def link_replace(match):
            label, target = match.groups()
            if target.startswith(("https://", "http://", "#", "mailto:")):
                return match.group(0)
            name = PurePosixPath(target).name
            if name not in by_name:
                return match.group(0)
            record = by_name[name]
            if record["reference_path"] in PUBLIC_DOMAIN_NASA_PDFS and record["reference_path"] in chosen:
                local = os.path.relpath(record["reference_path"], str(PurePosixPath(relative).parent)).replace(os.sep, "/")
                return "[Included NASA PDF](" + local + ")"
            return "[Source URL — link only](" + record["source_url"] + ")"
        rewritten = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", link_replace, rewritten)
        rewritten = re.sub(
            r"Seven selected public PDFs are saved.*?(?=\n\n|\Z)",
            "The portable reference inventory is recorded in [PRIMARY_SOURCE_DOWNLOADS.json](" +
            os.path.relpath("research/PRIMARY_SOURCE_DOWNLOADS.json", str(PurePosixPath(relative).parent)).replace(os.sep, "/") + "). "
            "Only the selected NASA PDFs are included as complete documents. Other works remain source links; "
            "no adjacent project folder or external symbolic link is required to use this archive.",
            rewritten, flags=re.DOTALL,
        )
        rewritten = rewritten.replace(
            "The archived primary PDFs are reference material; no third-party model geometry is embedded.",
            "The included NASA PDFs and link-only source list are reference material; no third-party model geometry is embedded."
        )
        if relative in {"README.md", "REFERENCES.md", "research/PRIMARY_SOURCE_INDEX.md"} and not rewritten.startswith(intro):
            rewritten = intro + rewritten
        if rewritten != content:
            staged = stage / relative
            staged.parent.mkdir(parents=True, exist_ok=True)
            staged.write_text(rewritten, encoding="utf-8")
            chosen[relative] = staged
            transformed_docs.append(relative)

    portable_inventory = {
        "scope": "Portable archive inventory; archive_file is present only for a PDF actually included",
        "research_originals_untouched": True,
        "included_pdf_count": len(included),
        "link_only_source_count": len(link_only),
        "sources": inventory,
    }
    inventory_rel = "research/PRIMARY_SOURCE_DOWNLOADS.json"
    staged_inventory = stage / inventory_rel
    staged_inventory.parent.mkdir(parents=True, exist_ok=True)
    staged_inventory.write_text(json.dumps(portable_inventory, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    chosen[inventory_rel] = staged_inventory

    lines = [
        "# Reference links and included NASA documents", "",
        "This portable deliverable reproduces only the selected NASA government publications below. "
        "Manufacturer, simulator, conference and externally authored NASA-hosted references remain available through source URLs. "
        "Their full PDFs are not reproduced in the archive.", "",
        "All original modeling code and geometry are included. Reference PDFs are optional reading; "
        "rebuilding the geometry does not require downloading the link-only sources.", "",
        "## Included NASA PDFs", "",
        "| Publication | Included file | Source URL |", "|---|---|---|",
    ]
    for r in included:
        lines.append("| " + r["title"] + " | [" + PurePosixPath(r["archive_file"]).name + "](" + r["archive_file"] + ") | [NASA source](" + r["source_url"] + ") |")
    lines.extend(["", "## Link-only sources", "",
                  "| Publication | Source URL | Archive status |", "|---|---|---|"])
    for r in link_only:
        lines.append("| " + r["title"] + " | [Open source](" + r["source_url"] + ") | Full PDF not included |")
    lines.extend(["", "The portable source index and download inventory reflect this selection. "
                  "A reference filename on a link-only record is an identifier, not a promised archive member. "
                  "No original local research file was deleted, replaced or edited.", ""])
    links_path = stage / "REFERENCE_LINKS.md"
    links_path.write_text("\n".join(lines), encoding="utf-8")
    chosen["REFERENCE_LINKS.md"] = links_path
    return {
        "included_nasa_pdf_files": [r["archive_file"] for r in included],
        "link_only_sources": [{"title": r["title"], "url": r["source_url"]} for r in link_only],
        "staged_pdf_links": staged_links,
        "archive_only_document_adjustments": transformed_docs + [inventory_rel],
        "existing_research_files_untouched": True,
    }


def file_role(relative):
    p = PurePosixPath(relative)
    if p.parts[0] == "native":
        return "Native Solidcraft 0.40.0-rc.3 scene"
    if p.parts[0] == "source":
        return "Original rebuild source"
    if p.parts[0] == "obj":
        return "Manifest-referenced geometry"
    if p.suffix.lower() == ".pdf" and p.parts[0] in {"research", "references"}:
        return "Included public-domain NASA reference PDF"
    if p.parts[0] in {"verification", "validation"} or p.suffix.lower() == ".json":
        return "Compact reference or verification receipt"
    return "User documentation and reference notes"


def collect_files(project, require_ready=True, max_receipt_bytes=4 * MIB):
    """Strict selection: no recursive project-folder archive operation."""
    chosen = {}
    notes = {"omitted_large_receipts": [], "unreferenced_obj_files_omitted": [],
             "link_only_pdf_files_omitted": [], "readiness_problems": []}
    def choose(path):
        if not path.is_file():
            return
        relative = safe_relative(str(path.relative_to(project)))
        validate_member_policy(relative)
        chosen[relative] = path

    for path in sorted(project.iterdir()):
        if not path.is_file() or path.name in METADATA_NAMES:
            continue
        if path.suffix.lower() in ROOT_DOC_SUFFIXES:
            if not any(word in path.stem.lower() for word in ("debug", "mcp-log", "transcript")):
                choose(path)
        elif path.suffix.lower() == ".json" and path.name != "scene_manifest.json":
            if any(word in path.stem.lower() for word in ("final", "verification", "validation", "receipt")):
                if path.stat().st_size <= max_receipt_bytes:
                    choose(path)

    source = project / "source"
    if source.exists():
        for path in sorted(source.glob("*.py")):
            if path.name not in OBSOLETE_SOURCE:
                choose(path)
    required_sources = ("generate.py", "scene_api.py", "native_build_rc3.py",
                        "aircraft.py", "carrier.py", "cockpit.py", "engines.py",
                        "internals.py", "package_project.py")
    for name in required_sources:
        if "source/" + name not in chosen:
            notes["readiness_problems"].append("Missing source/" + name)

    native_files = []
    native = project / "native"
    if native.exists():
        for path in sorted(native.glob("*.sc")):
            if any(word in path.name.lower() for word in ("smoke", "fixture", "test", "probe")):
                continue
            choose(path)
            native_files.append(path)
    for required in sorted(FINAL_NATIVE_NAMES):
        if not (native / required).is_file():
            notes["readiness_problems"].append("Missing native/" + required)
    for path in native_files:
        if path.stat().st_size < 1024:
            notes["readiness_problems"].append("Implausibly small native scene: " + path.name)

    manifest_path = project / "scene_manifest.json"
    referenced_obj = set()
    if manifest_path.is_file():
        choose(manifest_path)
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        for component in manifest.get("components", []):
            relative = safe_relative(component.get("file", ""))
            if not relative.startswith("obj/") or not relative.endswith(".obj"):
                raise ValueError("Unexpected component geometry path: " + relative)
            referenced_obj.add(relative)
            path = project / relative
            if path.is_file():
                choose(path)
            else:
                notes["readiness_problems"].append("Missing manifest geometry: " + relative)
        if not referenced_obj:
            notes["readiness_problems"].append("The scene manifest contains no component OBJ files")
    else:
        notes["readiness_problems"].append("Missing scene_manifest.json")
    obj_dir = project / "obj"
    if obj_dir.exists():
        for path in sorted(obj_dir.rglob("*.obj")):
            relative = str(path.relative_to(project))
            if relative not in referenced_obj:
                notes["unreferenced_obj_files_omitted"].append(relative)

    for tree in ("research", "references"):
        folder = project / tree
        if not folder.exists():
            continue
        for path in sorted(folder.rglob("*")):
            if not path.is_file():
                continue
            relative = str(path.relative_to(project))
            if blocked_path(relative) or path.name in BASELINE_REPORTS:
                continue
            suffix = path.suffix.lower()
            if suffix == ".md":
                choose(path)
            elif suffix == ".pdf":
                if relative in PUBLIC_DOMAIN_NASA_PDFS:
                    choose(path)
                else:
                    notes["link_only_pdf_files_omitted"].append(relative)
            elif suffix == ".json" and path.name not in EXCLUDED_RECEIPTS:
                if any(word in path.stem.lower() for word in (
                        "final", "validation", "receipt", "primary_source", "source_index")):
                    if path.stat().st_size <= max_receipt_bytes:
                        choose(path)
                    else:
                        notes["omitted_large_receipts"].append(relative)

    for tree in ("verification", "validation"):
        folder = project / tree
        if not folder.exists():
            continue
        for path in sorted(folder.rglob("*")):
            if not path.is_file():
                continue
            relative = str(path.relative_to(project))
            if blocked_path(relative) or path.name in EXCLUDED_RECEIPTS:
                continue
            if path.suffix.lower() not in {".json", ".md"}:
                continue
            if any(word in path.stem.lower() for word in (
                    "transcript", "mcp-log", "command-timing", "native-state", "tool-calls",
                    "package-validation", "package_validation")):
                continue
            if path.stat().st_size <= max_receipt_bytes:
                choose(path)
            else:
                notes["omitted_large_receipts"].append(relative)

    for required in ("README.md", "MATERIALS.md", "REFERENCES.md", "verification/FINAL_VALIDATION.json"):
        if not (project / required).is_file():
            notes["readiness_problems"].append("Missing final delivery file: " + required)
    final_receipt = project / "verification" / "FINAL_VALIDATION.json"
    if final_receipt.is_file():
        receipt = json.loads(final_receipt.read_text(encoding="utf-8"))
        native_records = receipt.get("native_files", [])
        passed = {PurePosixPath(r.get("file", "")).name for r in native_records
                  if r.get("fresh_reopen", {}).get("exact_persisted_state_match") is True}
        if len(native_records) != 6 or passed != FINAL_NATIVE_NAMES:
            notes["readiness_problems"].append("The six exact persisted native-state matches are not all verified")
    if require_ready and notes["readiness_problems"]:
        raise ValueError("Final project is not ready:\n" + "\n".join(notes["readiness_problems"]))
    return chosen, notes


def snapshot_files(chosen, project, stage):
    entries = []
    fingerprints = {}
    last_progress = time.monotonic()
    for index, (relative, path) in enumerate(sorted(chosen.items()), 1):
        if path.is_symlink():
            raise ValueError("Selected file is still a symlink: " + relative)
        resolved = path.resolve(strict=True)
        if not (resolved.is_relative_to(project) or resolved.is_relative_to(stage)):
            raise ValueError("Selected file resolves outside the project: " + relative)
        before = path.stat()
        digest = sha256_file(path)
        after = path.stat()
        fingerprint = (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns)
        if fingerprint != (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns):
            raise ValueError("File changed while being hashed: " + relative)
        fingerprints[relative] = fingerprint
        entries.append({"path": relative, "bytes": after.st_size,
                        "sha256": digest, "role": file_role(relative)})
        if time.monotonic() - last_progress > 20:
            emit("hashing", completed=index, files=len(chosen))
            last_progress = time.monotonic()
    return entries, fingerprints


def assert_unchanged(chosen, fingerprints):
    for relative, expected in fingerprints.items():
        s = chosen[relative].stat()
        actual = (s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns)
        if actual != expected:
            raise ValueError("Payload changed during packaging: " + relative)


def archive_order(relative):
    # Adjacent native scenes maximize opportunities for repeated-mesh compression.
    p = PurePosixPath(relative)
    if p.parts[0] == "native":
        return (0, 0 if p.name == MASTER_NAME else 1, relative)
    if p.parts[0] == "obj":
        return (1, 0, relative)
    if p.parts[0] == "source":
        return (2, 0, relative)
    return (3, 0, relative)


def parse_checksum_manifest(content):
    result = {}
    for line in content.decode("utf-8").splitlines():
        match = re.fullmatch(r"([0-9a-f]{64})  (.+)", line)
        if not match:
            raise ValueError("Malformed SHA256SUMS line")
        digest, relative = match.groups()
        safe_relative(relative)
        if relative in result:
            raise ValueError("Duplicate checksum path: " + relative)
        result[relative] = digest
    return result


def verify_archive(archive, expected_files=None):
    """Stream every regular member and validate both embedded integrity manifests."""
    actual = {}
    metadata = {}
    project_name = None
    last_progress = time.monotonic()
    with lzma.LZMAFile(archive, "rb") as decoded, tarfile.open(fileobj=decoded, mode="r|") as tar:
        for member in tar:
            if not member.isreg():
                raise ValueError("Nonregular archive member: " + member.name)
            name = safe_relative(member.name)
            parts = PurePosixPath(name).parts
            if len(parts) < 2:
                raise ValueError("Archive member is not under one project folder: " + name)
            if project_name is None:
                project_name = parts[0]
            if parts[0] != project_name:
                raise ValueError("Multiple project roots found in archive")
            relative = "/".join(parts[1:])
            validate_member_policy(relative)
            if relative in actual:
                raise ValueError("Duplicate archive member: " + relative)
            digest = hashlib.sha256()
            count = 0
            captured = bytearray() if relative in METADATA_NAMES else None
            stream = tar.extractfile(member)
            if stream is None:
                raise ValueError("Could not read archive member: " + relative)
            for block in iter(lambda: stream.read(CHUNK), b""):
                digest.update(block)
                count += len(block)
                if captured is not None:
                    if len(captured) + len(block) > 32 * MIB:
                        raise ValueError("Integrity metadata is unexpectedly large")
                    captured.extend(block)
            if count != member.size:
                raise ValueError("Truncated archive member: " + relative)
            actual[relative] = {"bytes": count, "sha256": digest.hexdigest()}
            if captured is not None:
                metadata[relative] = bytes(captured)
            if time.monotonic() - last_progress > 20:
                emit("verifying_archive", files=len(actual))
                last_progress = time.monotonic()
        # Consume the XZ trailer as well as all tar members, forcing CRC64 and
        # truncation checks even when the tar reader stops at its end markers.
        while decoded.read(CHUNK):
            pass

    if set(metadata) != METADATA_NAMES:
        raise ValueError("Archive is missing its integrity metadata")
    index = json.loads(metadata["FILE_INDEX.json"].decode("utf-8"))
    indexed = {}
    for entry in index.get("files", []):
        relative = safe_relative(entry["path"])
        if relative in indexed:
            raise ValueError("Duplicate FILE_INDEX entry: " + relative)
        indexed[relative] = entry
    if set(indexed) != set(actual) - METADATA_NAMES:
        raise ValueError("FILE_INDEX file set does not match archive payload")
    checksums = parse_checksum_manifest(metadata["SHA256SUMS.txt"])
    if set(checksums) != set(actual) - {"SHA256SUMS.txt"}:
        raise ValueError("SHA256SUMS file set does not match the archive")
    for relative, observed in actual.items():
        if relative != "SHA256SUMS.txt" and checksums[relative] != observed["sha256"]:
            raise ValueError("Checksum mismatch: " + relative)
        if relative in indexed:
            expected = indexed[relative]
            if expected["bytes"] != observed["bytes"] or expected["sha256"] != observed["sha256"]:
                raise ValueError("FILE_INDEX mismatch: " + relative)
    if expected_files is not None:
        if set(expected_files) != set(actual):
            raise ValueError("Archive member set differs from the selected snapshot")
        for relative, expected in expected_files.items():
            if expected["bytes"] != actual[relative]["bytes"] or expected["sha256"] != actual[relative]["sha256"]:
                raise ValueError("Archive content differs from the source snapshot: " + relative)
    return {
        "status": "passed",
        "project_folder": project_name,
        "regular_file_members": len(actual),
        "payload_files": len(indexed),
        "native_scenes": sum(p.startswith("native/") for p in actual),
        "obj_files": sum(p.startswith("obj/") and p.endswith(".obj") for p in actual),
        "primary_pdfs": sum(p.endswith(".pdf") and p.split("/")[0] in {"research", "references"} for p in actual),
        "uncompressed_member_bytes": sum(v["bytes"] for v in actual.values()),
        "all_members_regular": True,
        "xz_integrity_checked": True,
        "all_member_hashes_match": True,
        "embedded_index_and_checksum_sets_match": True,
        "excluded_runtime_logs_fixtures_or_nested_projects": True,
    }


def _package_prepared(project, output, dictionary_mib=128, epoch=None, max_receipt_bytes=4*MIB, compression_level=6, stage=None):
    project = project.resolve(strict=True)
    output = output.resolve()
    if output == project or output.is_relative_to(project):
        raise ValueError("Write the deliverable beside the project, not inside its payload tree")
    if not output.name.endswith(".tar.xz"):
        raise ValueError("The output filename must end in .tar.xz")
    output.parent.mkdir(parents=True, exist_ok=True)
    # Check readiness before mutating reference links or generating integrity files.
    collect_files(project, require_ready=True, max_receipt_bytes=max_receipt_bytes)
    chosen, notes = collect_files(project, require_ready=True, max_receipt_bytes=max_receipt_bytes)
    reference_preparation = prepare_portable_references(project, chosen, stage)
    emit("snapshot", files=len(chosen), dictionary_mib=dictionary_mib,
         compression_level=compression_level, included_nasa_pdfs=len(reference_preparation["included_nasa_pdf_files"]))
    entries, fingerprints = snapshot_files(chosen, project, stage)
    final_receipt = json.loads((project / "verification" / "FINAL_VALIDATION.json").read_text(encoding="utf-8"))
    verified_native_hashes = {r["file"]: r["sha256"] for r in final_receipt["native_files"]}
    for entry in entries:
        if entry["path"].startswith("native/") and verified_native_hashes.get(entry["path"]) != entry["sha256"]:
            raise ValueError("Native file differs from its final RC3 verification receipt: " + entry["path"])
    if epoch is None:
        epoch = int(os.environ.get("SOURCE_DATE_EPOCH", str(int(time.time()))))
    created = datetime.fromtimestamp(epoch, timezone.utc).isoformat()
    index = {
        "schema_version": PACKAGE_VERSION,
        "project": "F/A-18C / USS John C. Stennis - Solidcraft 0.40.0-rc.3 realism",
        "project_folder": project.name,
        "created_utc": created,
        "payload_files": len(entries),
        "payload_bytes": sum(e["bytes"] for e in entries),
        "integrity_scope": "Portable archive contents only. files lists payload; SHA256SUMS covers payload plus FILE_INDEX.json and intentionally does not hash itself. Archive-only reference views preserve unchanged local research.",
        "compression": {"container": "tar.xz", "threads": 1,
                        "lzma2_dictionary_mib": dictionary_mib, "preset": compression_level},
        "portable_reference_preparation": reference_preparation,
        "selection": {
            "native": "Final RC3 master and inspection scenes only",
            "source": "Top-level current Python source; obsolete v1 native helpers excluded",
            "geometry": "Every component OBJ referenced by scene_manifest.json",
            "references": "Selected public-domain NASA PDFs; other works as source URLs, with archive-specific inventory wording",
            "receipts": "Compact JSON/Markdown verification receipts, excluding smoke fixtures and full tool logs",
            "excluded": ["runtime", "development", "smoke/fixture trees", "logs", "pycache",
                         "older projects", "obsolete native helpers", "superseded baseline interference reports"],
        },
        "selection_notes": notes,
        "files": entries,
    }
    index_path = stage / "FILE_INDEX.json"
    atomic_write(index_path, json.dumps(index, indent=2, ensure_ascii=False) + "\n")
    expected = {e["path"]: {"bytes": e["bytes"], "sha256": e["sha256"]} for e in entries}
    expected["FILE_INDEX.json"] = {"bytes": index_path.stat().st_size, "sha256": sha256_file(index_path)}
    sums = "".join(expected[p]["sha256"] + "  " + p + "\n" for p in sorted(expected))
    sums_path = stage / "SHA256SUMS.txt"
    atomic_write(sums_path, sums)
    expected["SHA256SUMS.txt"] = {"bytes": sums_path.stat().st_size, "sha256": sha256_file(sums_path)}
    chosen.update({"FILE_INDEX.json": index_path, "SHA256SUMS.txt": sums_path})
    assert_unchanged(chosen, fingerprints)

    fd, name = tempfile.mkstemp(prefix="." + output.name + ".", suffix=".partial", dir=output.parent)
    os.close(fd)
    temporary = Path(name)
    started = time.monotonic()
    last_progress = started
    try:
        filters = [{"id": lzma.FILTER_LZMA2, "preset": compression_level, "dict_size": dictionary_mib * MIB}]
        with temporary.open("wb") as raw:
            with lzma.LZMAFile(raw, "w", format=lzma.FORMAT_XZ,
                             check=lzma.CHECK_CRC64, filters=filters) as compressed:
                with tarfile.open(fileobj=compressed, mode="w|",
                                  format=tarfile.PAX_FORMAT, dereference=True) as tar:
                    for number, relative in enumerate(sorted(chosen, key=archive_order), 1):
                        path = chosen[relative]
                        info = tar.gettarinfo(str(path), arcname=project.name + "/" + relative)
                        # Always store actual regular bytes, including local hardlinked PDFs.
                        info.type = tarfile.REGTYPE
                        info.linkname = ""
                        info.size = expected[relative]["bytes"]
                        info.uid = info.gid = 0
                        info.uname = info.gname = ""
                        info.mtime = epoch
                        info.mode = 0o755 if relative.startswith("source/") and path.stat().st_mode & stat.S_IXUSR else 0o644
                        info.pax_headers = {}
                        with path.open("rb") as handle:
                            tar.addfile(info, handle)
                        if time.monotonic() - last_progress > 20:
                            emit("compressing", completed=number, files=len(chosen),
                                 compressed_bytes=raw.tell())
                            last_progress = time.monotonic()
            raw.flush()
            os.fsync(raw.fileno())
        assert_unchanged(chosen, fingerprints)
        verification = verify_archive(temporary, expected)
        archive_digest = sha256_file(temporary)
        archive_bytes = temporary.stat().st_size
        os.replace(temporary, output)
        sidecar = output.with_name(output.name + ".sha256")
        atomic_write(sidecar, archive_digest + "  " + output.name + "\n")
        receipt = {
            **verification,
            "archive": output.name,
            "archive_bytes": archive_bytes,
            "archive_sha256": archive_digest,
            "created_utc": created,
            "compression": index["compression"],
            "portable_reference_preparation": reference_preparation,
            "elapsed_seconds": round(time.monotonic() - started, 3),
            "sidecar_note": "This receipt and the archive checksum are external to the archive to avoid self-referential hashes.",
        }
        receipt_path = output.with_name(output.name + ".verification.json")
        atomic_write(receipt_path, json.dumps(receipt, indent=2, ensure_ascii=False) + "\n")
        emit("complete", output=str(output), checksum=str(sidecar),
             verification_receipt=str(receipt_path), **receipt)
        return receipt
    finally:
        if temporary.exists():
            temporary.unlink()


def package_project(project, output, dictionary_mib=128, epoch=None, max_receipt_bytes=4*MIB, compression_level=6):
    project = project.resolve(strict=True)
    output = output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".rc3-portable-staging.", dir=output.parent) as folder:
        return _package_prepared(project, output, dictionary_mib, epoch, max_receipt_bytes, compression_level, Path(folder))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--project", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output", type=Path, help="Destination beside the project; default PROJECT.tar.xz")
    parser.add_argument("--dict-mib", type=int, choices=(64, 128), default=128)
    parser.add_argument("--compression-level", type=int, choices=range(10), default=6,
                        help="XZ preset 0-9; 1 or 2 is faster, while --dict-mib remains unchanged")
    parser.add_argument("--epoch", type=int, help="Fixed UTC epoch for deterministic metadata")
    parser.add_argument("--max-receipt-mib", type=int, default=4)
    parser.add_argument("--plan", action="store_true", help="Read-only selection/readiness report; writes nothing")
    parser.add_argument("--verify", type=Path, help="Verify an existing archive using its embedded manifests")
    args = parser.parse_args(argv)
    if args.max_receipt_mib < 1:
        parser.error("--max-receipt-mib must be at least 1")
    try:
        if args.verify:
            emit("verified", archive=str(args.verify), **verify_archive(args.verify))
            return 0
        project = args.project.resolve(strict=True)
        output = args.output or project.parent / (project.name + ".tar.xz")
        if args.plan:
            chosen, notes = collect_files(project, require_ready=False,
                                          max_receipt_bytes=args.max_receipt_mib * MIB)
            links = [p for p in chosen.values() if p.is_symlink()]
            plan_notes = dict(notes)
            omitted = plan_notes.pop("unreferenced_obj_files_omitted", [])
            plan_notes["unreferenced_obj_files_omitted_count"] = len(omitted)
            plan_notes["unreferenced_obj_files_omitted_sample"] = omitted[:8]
            emit("plan", project=str(project), output=str(output), files=len(chosen),
                 bytes=sum(p.stat().st_size for p in chosen.values()),
                 native_scenes=[p for p in chosen if p.startswith("native/")],
                 sources=[p for p in chosen if p.startswith("source/")],
                 nasa_pdf_symlinks_to_stage_without_modifying=[str(p.relative_to(project)) for p in links if p.suffix.lower()==".pdf"],
                 dictionary_mib=args.dict_mib, compression_level=args.compression_level, threads=1, notes=plan_notes)
            return 0
        package_project(project, output, args.dict_mib, args.epoch, args.max_receipt_mib * MIB, args.compression_level)
        return 0
    except (OSError, ValueError, KeyError, json.JSONDecodeError, tarfile.TarError, lzma.LZMAError) as error:
        emit("error", message=str(error))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
