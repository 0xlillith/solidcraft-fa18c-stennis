#!/usr/bin/env python3
"""Build or derive this original aircraft using exact released SolidCraft 0.40 RC3.

Python standard library only. No compilation, GUI changes, GPU or rendering.
All native document edits use public commands. The official Linux x86_64 CLI
is SHA256-pinned, and every deliverable must be solidcraft/51 and reopen cleanly
in a fresh process of the same executable.

Geometry/camera/slider inputs are metres; revolutes are degrees. motion_links
ratios and offsets use native deg/mm. inspection_variants entries contain name,
subset, hide_components/hide_bodies (exact names), hide_component_patterns and
hide_body_patterns (fnmatch), pose (joint to authored units), and view.
Closed-loop followers can use passive:true; linked followers are automatic.
"""

from __future__ import annotations

import argparse
import copy
import fnmatch
import hashlib
import json
import math
import os
from pathlib import Path
import queue
import re
import shutil
import signal
import subprocess
import sys
import threading
import time
import zipfile
from collections import defaultdict
from typing import Any


class BuildError(RuntimeError):
    """A source, protocol, native validation or geometry check failed."""


def stamp() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def progress(event: str, **fields: Any) -> None:
    print(json.dumps({"at": stamp(), "event": event, **fields}, ensure_ascii=False), flush=True)


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + ".writing")
    temp.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")
    temp.replace(path)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def number(value: Any, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (float, int)) or not math.isfinite(value):
        raise BuildError(f"{label} must be a finite number")
    return float(value)


def point3(value: Any, label: str, scale: float = 1.0) -> list[float]:
    if not isinstance(value, (list, tuple)) or len(value) != 3:
        raise BuildError(f"{label} must contain three numbers")
    return [number(item, label) * scale for item in value]


def safe_slug(name: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "_", name).strip("._")[:100] or "view"


def chunks(values: list[Any], size: int = 1000):
    for offset in range(0, len(values), size):
        yield values[offset:offset + size]


def journal_safe(value: Any) -> Any:
    """Keep text receipts, never duplicate image payloads in a JSON journal."""
    if isinstance(value, dict):
        if value.get("type") in {"image", "audio"} and isinstance(value.get("data"), str):
            return {key: val for key, val in value.items() if key != "data"} | {"encoded_bytes": len(value["data"])}
        return {key: journal_safe(val) for key, val in value.items()}
    if isinstance(value, list):
        return [journal_safe(val) for val in value]
    return value


class MCP:
    """Synchronous client with a draining reader and visible long-call heartbeat."""

    def __init__(self, cli: Path, allowed: list[Path], receipts: Path,
                 timeout: float, threads: int, niceness: int, enable_gpu: bool = False):
        self.timeout = timeout
        self.receipts = receipts
        self.count = 0
        self.next_id = 1
        self.pending: queue.Queue[Any] = queue.Queue()
        self.live = True
        self.command_history: list[dict[str, Any]] = []
        self.journal = (receipts / "commands.jsonl").open("w", encoding="utf-8")
        self.stderr = (receipts / "solidcraft-stderr.log").open("w", encoding="utf-8")
        recovery = receipts / "recovery"
        recovery.mkdir(parents=True, exist_ok=True)
        env = os.environ.copy()
        env["SOLIDCRAFT_RECOVERY_DIR"] = str(recovery)
        env["RAYON_NUM_THREADS"] = str(threads)
        env["OMP_NUM_THREADS"] = str(threads)
        command = [str(cli), "mcp", "--headless", "--compact"]
        if enable_gpu:
            command.append("--render-gpu")
        for folder in dict.fromkeys(str(path.resolve()) for path in allowed):
            command.extend(["--allow-path", folder])
        if os.name == "posix" and niceness and shutil.which("nice"):
            command = [shutil.which("nice") or "nice", "-n", str(niceness), *command]
        self.process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                        stderr=self.stderr, text=True, encoding="utf-8", bufsize=1,
                                        env=env, start_new_session=(os.name == "posix"))
        threading.Thread(target=self._read, name="solidcraft-mcp-reader", daemon=True).start()
        try:
            self.server = self.request("initialize", {
                "protocolVersion": "2025-06-18", "capabilities": {},
                "clientInfo": {"name": "fa18c-official-rc3-builder", "version": "2.0"},
            }, label="initialize headless SolidCraft")
            self.notify("notifications/initialized", {})
        except Exception:
            self.close()
            raise

    def _read(self) -> None:
        assert self.process.stdout is not None
        try:
            for line in self.process.stdout:
                self.pending.put(line)
        finally:
            self.pending.put(None)

    def notify(self, method: str, params: dict[str, Any]) -> None:
        if not self.live or self.process.poll() is not None or self.process.stdin is None:
            raise BuildError("headless SolidCraft process is no longer available")
        self.process.stdin.write(json.dumps({"jsonrpc": "2.0", "method": method, "params": params}, allow_nan=False) + "\n")
        self.process.stdin.flush()

    def request(self, method: str, params: dict[str, Any], label: str) -> Any:
        if not self.live or self.process.poll() is not None or self.process.stdin is None:
            raise BuildError("headless SolidCraft process is no longer available")
        identifier = self.next_id
        self.next_id += 1
        started = time.monotonic()
        message = {"jsonrpc": "2.0", "id": identifier, "method": method, "params": params}
        self.process.stdin.write(json.dumps(message, allow_nan=False) + "\n")
        self.process.stdin.flush()
        self.journal.write(json.dumps({"at": stamp(), "request": message}, ensure_ascii=False) + "\n")
        self.journal.flush()
        heartbeat = started
        while True:
            elapsed = time.monotonic() - started
            if elapsed > self.timeout:
                self.live = False
                raise BuildError(f"native operation timed out after {elapsed:.1f}s: {label}; it was not retried")
            try:
                line = self.pending.get(timeout=min(5.0, max(0.01, self.timeout - elapsed)))
            except queue.Empty:
                if time.monotonic() - heartbeat >= 20:
                    progress("native_wait", operation=label, seconds=round(elapsed, 1))
                    heartbeat = time.monotonic()
                continue
            if line is None:
                self.live = False
                raise BuildError(f"SolidCraft exited during {label}; inspect solidcraft-stderr.log")
            try:
                reply = json.loads(line)
            except json.JSONDecodeError as exc:
                raise BuildError(f"non-JSON stdout from SolidCraft during {label}: {line[:300]!r}") from exc
            if reply.get("id") != identifier:
                if "method" in reply and "id" not in reply:
                    self.journal.write(json.dumps({"at": stamp(), "notification": journal_safe(reply)}, ensure_ascii=False) + "\n")
                    continue
                raise BuildError(f"unexpected MCP reply ID during {label}: {reply.get('id')!r}")
            elapsed = time.monotonic() - started
            self.journal.write(json.dumps({"at": stamp(), "seconds": round(elapsed, 3), "reply": journal_safe(reply)}, ensure_ascii=False) + "\n")
            self.journal.flush()
            self.count += 1
            self.command_history.append({"operation": label, "seconds": round(elapsed, 3), "rpc_id": identifier})
            if "error" in reply:
                raise BuildError(f"{label}: {json.dumps(reply['error'], ensure_ascii=False)}")
            return reply.get("result")

    def tool(self, name: str, arguments: dict[str, Any]) -> Any:
        label = arguments.get("command", name)
        raw = self.request("tools/call", {"name": name, "arguments": arguments}, str(label))
        if not isinstance(raw, dict):
            raise BuildError(f"MCP {label} did not return an object")
        texts = [part.get("text", "") for part in raw.get("content", []) if part.get("type") == "text"]
        if raw.get("isError"):
            raise BuildError(f"{label}: {' '.join(texts)[:6000]}")
        if raw.get("structuredContent") is not None:
            return raw["structuredContent"]
        if len(texts) == 1:
            try:
                return json.loads(texts[0])
            except json.JSONDecodeError:
                return {"text": texts[0]}
        return {"texts": texts}

    def execute(self, command: str, params: dict[str, Any] | None = None) -> Any:
        return self.tool("execute", {"command": command, "params": params or {}, "verbose": False})

    def close(self) -> None:
        if getattr(self, "process", None) is not None:
            if self.process.stdin is not None:
                try:
                    self.process.stdin.close()
                except OSError:
                    pass
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                if os.name == "posix":
                    os.killpg(self.process.pid, signal.SIGTERM)
                else:
                    self.process.terminate()
                try:
                    self.process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    if os.name == "posix":
                        os.killpg(self.process.pid, signal.SIGKILL)
                    else:
                        self.process.kill()
                    self.process.wait(timeout=5)
        self.live = False
        self.journal.close()
        self.stderr.close()


def category(component: dict[str, Any]) -> str:
    explicit = str(component.get("category", "")).lower()
    if explicit:
        if any(word in explicit for word in ("carrier", "deck", "environment", "crew", "ship")):
            return "carrier"
        return "aircraft"
    name = component["name"].lower()
    return "carrier" if name.startswith(("carrier", "jbd", "catapult", "deck", "island", "stennis", "ocean", "sea ", "crew")) else "aircraft"


def validate_manifest(manifest: dict[str, Any], folder: Path, subset: str) -> dict[str, Any]:
    if manifest.get("geometry_units", "m") not in {"m", "metres", "meters"}:
        raise BuildError("scene_manifest geometry_units must be m; hinge/camera positions are metres")
    all_components = manifest.get("components", [])
    components = [item for item in all_components if subset == "all" or category(item) == subset]
    if not components:
        raise BuildError(f"manifest contains no components in subset {subset}")
    names = [item["name"] for item in components]
    if len(set(names)) != len(names):
        raise BuildError("component names must be unique")
    selected = set(names)
    bodies = [item for item in manifest.get("bodies", []) if item["component"] in selected]
    body_names = [item["name"] for item in bodies]
    if len(set(body_names)) != len(body_names):
        raise BuildError("body names must be globally unique")
    materials = manifest.get("materials", {})
    for body in bodies:
        if body["material"] not in materials:
            raise BuildError(f"unknown material key {body['material']!r} on {body['name']}")
    by_component: dict[str, list[str]] = defaultdict(list)
    for body in bodies:
        by_component[body["component"]].append(body["name"])
    imports = []
    for component in components:
        expected = component.get("bodies", by_component[component["name"]])
        if set(expected) != set(by_component[component["name"]]) or len(expected) != len(by_component[component["name"]]):
            raise BuildError(f"component/body manifest disagreement for {component['name']}")
        if not expected:
            raise BuildError(f"empty component cannot be imported: {component['name']}")
        source = (folder / component["file"]).resolve()
        if not source.is_relative_to(folder.resolve()) or source.suffix.lower() != ".obj" or not source.is_file():
            raise BuildError(f"missing or out-of-project OBJ for {component['name']}: {source}")
        imports.append({**component, "source": str(source), "bodies": expected})
    joints = [item for item in manifest.get("joints", []) if item["parent"] in selected and item["child"] in selected]
    if len({item["name"] for item in joints}) != len(joints):
        raise BuildError("joint names must be unique")
    for joint in joints:
        kind = joint.get("kind", "revolute")
        if kind not in {"revolute", "slider", "rigid"}:
            raise BuildError(f"unsupported joint kind {kind!r}: {joint['name']}")
        joint["kind"] = kind
        point3(joint.get("origin", [0, 0, 0]), joint["name"] + " origin")
        axis = point3(joint.get("axis", [0, 0, 1]), joint["name"] + " axis")
        norm = math.sqrt(sum(value * value for value in axis))
        if norm < 1e-12:
            raise BuildError(f"zero joint axis: {joint['name']}")
        if kind in {"revolute", "slider"}:
            limits = joint.get("limits")
            if not isinstance(limits, list) or len(limits) != 2:
                raise BuildError(f"two finite limits required: {joint['name']}")
            low, high = (number(value, joint["name"] + " limits") for value in limits)
            if low > high or not low <= 0 <= high:
                raise BuildError(f"joint limits must include authored neutral zero: {joint['name']}")
            default = number(joint.get("default", 0), joint["name"] + " default")
            if not low <= default <= high:
                raise BuildError(f"default outside limits: {joint['name']}")
    for key in {body["material"] for body in bodies}:
        material = materials[key]
        color = material.get("color")
        if not isinstance(color, list) or len(color) != 3 or any(isinstance(v, bool) or not isinstance(v, int) or not 0 <= v <= 255 for v in color):
            raise BuildError(f"material {key} must have an integer RGB colour")
        opacity = number(material.get("opacity", 1), key + " opacity")
        if not 0 <= opacity <= 1:
            raise BuildError(f"material {key} opacity outside 0..1")
        if opacity == 1:
            for field, default, low, high in (("metallic", 0, 0, 1), ("roughness", 0.5, 0.045, 1), ("ior", 1.5, 1, 3)):
                value = number(material.get(field, default), key + " " + field)
                if not low <= value <= high:
                    raise BuildError(f"material {key} {field} outside {low}..{high}")
    return {"components": imports, "bodies": bodies, "materials": materials, "joints": joints,
            "subset": subset, "body_count": len(bodies), "component_count": len(imports),
            "triangles": sum(int(body.get("triangles", 0)) for body in bodies)}


def native_camera(camera: dict[str, Any]) -> dict[str, Any]:
    return {"target": point3(camera["target"], "camera target", 1000),
            "distance": number(camera["distance"], "camera distance") * 1000,
            "yaw": number(camera["yaw"], "camera yaw"),
            "pitch": number(camera["pitch"], "camera pitch"),
            "fov": number(camera.get("fov", 0.6), "camera fov")}


def joint_units(joint: dict[str, Any], value: float) -> float:
    return value * (1000 if joint["kind"] == "slider" else 1)


def probe_value(joint: dict[str, Any]) -> float | None:
    low, high = joint["limits"]
    default = joint.get("default", 0)
    if high - low < 1e-9:
        return None
    distance = min((high - low) * 0.35, 20 if joint["kind"] == "revolute" else 0.2)
    return default + distance if high - default >= distance else default - distance


def require_solution(result: Any, label: str) -> None:
    if isinstance(result, dict) and (result.get("errors") or result.get("conflicts")):
        raise BuildError(f"assembly problem after {label}: {json.dumps(result, ensure_ascii=False)[:3000]}")



RELEASE = {
    "tag": "v0.40.0-rc.3",
    "commit": "7001949c49e211a430fe4747221589b2b9384f2c",
    "url": "https://github.com/tangency-labs/solidcraft/releases/tag/v0.40.0-rc.3",
    "archive": "solidcraft-0.40.0-rc.3-linux-x86_64.tar.gz",
    "archive_sha256": "75bafe8b13ae9b120ccc5487ba9f0745b942b4f794d2c4c87cd6c1151089a32b",
    "cli_sha256": "3f29f4cc262601f9b2e029745a9b56de6f959e14bec74003693d36be12c9f45a",
    "version": "solidcraft-cli 0.40.0-rc.3",
    "format": "solidcraft/51",
}


def verify_release(cli):
    if not cli.is_file() or not os.access(cli, os.X_OK):
        raise BuildError(f"official CLI unavailable: {cli}")
    actual = sha256(cli)
    if actual != RELEASE["cli_sha256"]:
        raise BuildError(f"CLI is not the verified official Linux x86_64 RC3 executable: {actual}")
    version = subprocess.run([str(cli), "--version"], capture_output=True, text=True,
                             check=True, timeout=30).stdout.strip()
    if version != RELEASE["version"]:
        raise BuildError(f"unexpected CLI version: {version!r}")
    return {**RELEASE, "cli_path": str(cli), "verified_cli_sha256": actual, "verified_version": version}


def native_container(path):
    # Read-only inspection of the public-command save, never native JSON authoring.
    with zipfile.ZipFile(path) as archive:
        document = json.loads(archive.read("document.json"))
        container = json.loads(archive.read("container.json"))
        entries = archive.namelist()
    if document.get("format") != RELEASE["format"]:
        raise BuildError(f"native format is {document.get('format')!r}, expected {RELEASE['format']}")
    if container.get("format") != "solidcraft-container/1":
        raise BuildError(f"unexpected native container: {container.get('format')!r}")
    return {"format": document["format"], "container": container["format"],
            "mesh_blobs": sum(name.endswith(".mesh") for name in entries), "entries": len(entries)}


def save_native(client, path):
    reply = client.execute("file.save_as", {"path": str(path), "compression": "compact", "cache": False, "overwrite": True})
    if not path.is_file() or not path.stat().st_size:
        raise BuildError(f"native save did not produce a nonempty file: {path}")
    return {"path": str(path), "bytes": path.stat().st_size, "sha256": sha256(path),
            "cache": False, "native_reply": reply, **native_container(path)}


def links_for(manifest, plan):
    joints = {joint["name"]: joint for joint in plan["joints"]}
    known = {joint["name"] for joint in manifest["joints"]}
    links = []
    driven = set()
    for raw in manifest.get("motion_links", []):
        link = dict(raw)
        if link.get("a") not in known or link.get("b") not in known:
            raise BuildError(f"motion link names an unknown joint: {link}")
        if link["a"] not in joints or link["b"] not in joints:
            continue
        if link["a"] == link["b"] or link["b"] in driven:
            raise BuildError(f"scalar follower needs exactly one distinct driver: {link}")
        a, b = joints[link["a"]], joints[link["b"]]
        if a["kind"] not in {"revolute", "slider"} or b["kind"] not in {"revolute", "slider"}:
            raise BuildError(f"rigid joint in motion link: {link}")
        link["ratio"] = number(link["ratio"], "motion link ratio")
        link["offset"] = number(link.get("offset", 0), "motion link offset")
        if abs(link["ratio"]) < 1e-12:
            raise BuildError(f"zero-ratio link would lock its follower: {link}")
        expected = link["ratio"] * joint_units(a, a.get("default", 0)) + link["offset"]
        declared = joint_units(b, b.get("default", 0))
        if abs(expected - declared) > 1e-6:
            raise BuildError(f"inconsistent linked default {b['name']}: relation {expected}, manifest {declared}")
        driven.add(link["b"])
        links.append(link)
    parents = {link["b"]: link["a"] for link in links}
    for name in parents:
        seen = set()
        while name in parents:
            if name in seen:
                raise BuildError("motion-link dependency cycle")
            seen.add(name)
            name = parents[name]
    return links


def independent_joints(plan, links):
    followers = {link["b"] for link in links}
    return [joint for joint in plan["joints"] if joint["kind"] != "rigid"
            and joint["name"] not in followers and not joint.get("passive", False)]


def joint_values(reply):
    return {joint["name"]: joint["values"][0]["value"]
            for joint in reply.get("joints", []) if joint.get("values")}


def check_links(reply, links):
    values = joint_values(reply)
    for link in links:
        expected = values[link["a"]] * link["ratio"] + link["offset"]
        if abs(values[link["b"]] - expected) > 1e-6:
            raise BuildError(f"motion-link follower did not follow: {link['b']}")


def check_default_pose(reply, plan, links):
    require_solution(reply, "saved pose")
    if reply.get("floating"):
        raise BuildError(f"floating assembly chains remain: {reply['floating']}")
    values = joint_values(reply)
    for joint in plan["joints"]:
        if joint["kind"] == "rigid" or joint.get("passive", False):
            continue
        expected = joint_units(joint, joint.get("default", 0))
        if abs(values.get(joint["name"], math.inf) - expected) > 1e-6:
            raise BuildError(f"default mismatch for {joint['name']}: {values.get(joint['name'])}, expected {expected}")
    check_links(reply, links)


def linked_probe(joint, plan, links):
    # Restrict the driver's test to the intersection of all linked follower limits.
    by_name = {entry["name"]: entry for entry in plan["joints"]}
    relations = {joint["name"]: (1.0, 0.0)}
    changed = True
    while changed:
        changed = False
        for link in links:
            if link["a"] in relations and link["b"] not in relations:
                a, b = relations[link["a"]]
                relations[link["b"]] = (link["ratio"] * a, link["ratio"] * b + link["offset"])
                changed = True
    low, high = [joint_units(joint, value) for value in joint["limits"]]
    for name, (a, b) in relations.items():
        follower = by_name[name]
        lo, hi = [joint_units(follower, value) for value in follower["limits"]]
        ends = sorted(((lo-b)/a, (hi-b)/a))
        low, high = max(low, ends[0]), min(high, ends[1])
    default = joint_units(joint, joint.get("default", 0))
    if low > high + 1e-8 or not low-1e-8 <= default <= high+1e-8:
        raise BuildError(f"inconsistent linked limits for {joint['name']}")
    if high-low < 1e-8:
        return None
    delta = min((high-low) * 0.2, 20 if joint["kind"] == "revolute" else 200)
    value = default + delta if high-default >= delta else default-delta
    return value / (1000 if joint["kind"] == "slider" else 1)


def native_state(client):
    joints = client.execute("joint.list")
    require_solution(joints, "native inspection")
    if joints.get("floating"):
        raise BuildError("native inspection found floating joint chains")
    return {"joints": joints,
            "components": client.execute("component.list", {"compact": True, "bodies": True}),
            "views": client.execute("view.list"), "motion": client.execute("motion.list"),
            "document": client.execute("document.inspect", {"measure": False})}


def stable_state(state):
    def rounded(value):
        if isinstance(value, float):
            return round(value, 7)
        if isinstance(value, dict):
            return {key: rounded(item) for key, item in value.items()}
        if isinstance(value, list):
            return [rounded(item) for item in value]
        return value
    doc = state["document"]
    return rounded({"joints": state["joints"], "components": state["components"],
                    "views": state["views"], "motion": state["motion"],
                    "bodies": doc.get("bodies"), "hidden_origin": doc.get("hidden_origin"),
                    "metadata": doc.get("metadata"), "name": doc.get("name")})


def verify_body_set(state, plan, hidden):
    expected = {body["name"] for body in plan["bodies"]}
    actual = {body["name"] for body in state["document"].get("bodies", [])}
    if actual != expected:
        raise BuildError(f"body set mismatch: missing {sorted(expected-actual)[:20]}, extra {sorted(actual-expected)[:20]}")
    actual_hidden = {body["name"] for body in state["document"]["bodies"] if body.get("visible") is False}
    if actual_hidden != hidden:
        raise BuildError(f"visibility mismatch: expected {len(hidden)} hidden, found {len(actual_hidden)}")
    return {"stored_bodies": len(actual), "visible_bodies": len(actual-hidden), "hidden_bodies": len(hidden),
            "native_joints": len(state["joints"].get("joints", [])),
            "motion_links": len(state["joints"].get("links", [])),
            "named_views": len(state["views"].get("views", [])),
            "motion_studies": len(state["motion"].get("studies", [])),
            "floating_chains": 0, "joint_conflicts": 0}


def fresh_reopen(cli, output, receipts, before, plan, hidden, args):
    folder = receipts / "fresh-reopen"
    folder.mkdir(parents=True, exist_ok=True)
    digest = sha256(output)
    reader = MCP(cli, [output.parent, folder], folder, args.timeout, args.threads, args.nice)
    try:
        opened = reader.execute("doc.open", {"path": str(output), "read_only": True})
        if opened.get("read_only") is not True or opened.get("errors") or opened.get("newer_file") or opened.get("warnings"):
            raise BuildError(f"official RC3 reopen failed compatibility gate: {opened}")
        after = native_state(reader)
        checks = verify_body_set(after, plan, hidden)
        if stable_state(before) != stable_state(after):
            write_json(folder / "before.json", stable_state(before))
            write_json(folder / "after.json", stable_state(after))
            raise BuildError("fresh RC3 process did not retain bodies, poses, links, views, studies and visibility")
        if sha256(output) != digest:
            raise BuildError("native file changed during read-only reopen")
        write_json(folder / "native-state.json", after)
        return {"open": opened, "exact_persisted_state_match": True, "file_unchanged": True, **checks}
    finally:
        reader.close()


def create_assembly(client, plan, links, occurrences, receipt, args):
    grounded = {item["name"] for item in plan["components"]
                if item.get("grounded", item["name"] in {"Airframe", "Carrier structure"})}
    if not grounded:
        raise BuildError("mark at least one selected component grounded=true")
    for name, occurrence in occurrences.items():
        client.execute("occurrence.ground", {"occurrence": occurrence, "grounded": name in grounded})
    for index, joint in enumerate(plan["joints"], 1):
        progress("joint_create", index=index, total=len(plan["joints"]), joint=joint["name"])
        params = {"type": joint["kind"], "a": occurrences[joint["parent"]], "b": occurrences[joint["child"]],
                  "at": {"occurrence": occurrences[joint["parent"]],
                         "point": point3(joint.get("origin", [0, 0, 0]), "joint origin", 1000),
                         "z": point3(joint.get("axis", [0, 0, 1]), "joint axis")},
                  "name": joint["name"], "quiet": True}
        if joint["kind"] in {"revolute", "slider"}:
            params["limits"] = [[joint_units(joint, value) for value in joint["limits"]]]
        require_solution(client.execute("joint.as_built", params), joint["name"])
    adjacency = {name: set() for name in occurrences}
    for joint in plan["joints"]:
        adjacency[joint["parent"]].add(joint["child"])
        adjacency[joint["child"]].add(joint["parent"])
    reached = set()

    def visit(seed):
        stack = [seed]
        while stack:
            current = stack.pop()
            if current not in reached:
                reached.add(current)
                stack.extend(adjacency[current] - reached)

    for name in grounded:
        visit(name)
    receipt["automatic_rigid_joints"] = []
    if args.auto_rigid:
        for component in plan["components"]:
            child = component["name"]
            if child in reached:
                continue
            base = "Carrier structure" if category(component) == "carrier" else "Airframe"
            if base not in grounded:
                base = sorted(grounded)[0]
            name = "Fixed detail - " + child
            result = client.execute("joint.as_built", {"type": "rigid", "a": occurrences[base],
                                      "b": occurrences[child], "name": name, "quiet": True})
            require_solution(result, name)
            receipt["automatic_rigid_joints"].append({"name": name, "parent": base, "child": child})
            visit(child)
    for link in links:
        result = client.execute("joint.motion_link", {key: link[key] for key in ("a", "b", "ratio", "offset")})
        require_solution(result, "motion link " + link["b"])
    for joint in independent_joints(plan, links):
        value = joint_units(joint, joint.get("default", 0))
        # Even a zero input must be pinned explicitly after nonzero-offset
        # links are created: loop projection may otherwise redistribute DOFs.
        result = client.execute("joint.drive", {"joint": joint["name"], "value": value, "quiet": True})
        require_solution(result, joint["name"])
    check_default_pose(client.execute("joint.list"), plan, links)


def verify_articulation(client, plan, links, occurrences, receipt):
    independent = independent_joints(plan, links)
    linked_drivers = {link["a"] for link in links}
    for index, joint in enumerate(independent, 1):
        probe = linked_probe(joint, plan, links)
        if probe is None:
            receipt["joint_probes"].append({"joint": joint["name"], "locked_limits": True})
            continue
        progress("joint_probe", index=index, total=len(independent), joint=joint["name"])
        before = client.execute("occurrence.properties", {"occurrence": occurrences[joint["child"]], "descendants": False})
        moved = client.execute("joint.drive", {"joint": joint["name"], "value": joint_units(joint, probe), "quiet": True})
        require_solution(moved, joint["name"] + " probe")
        after = client.execute("occurrence.properties", {"occurrence": occurrences[joint["child"]], "descendants": False})
        current = client.execute("joint.list") if joint["name"] in linked_drivers else None
        if current:
            check_links(current, links)
        restored = client.execute("joint.drive", {"joint": joint["name"],
                                  "value": joint_units(joint, joint.get("default", 0)), "quiet": True})
        require_solution(restored, joint["name"] + " restore")
        if moved.get("moved") is not True:
            raise BuildError(f"independent joint probe moved nothing: {joint['name']}: {moved}")
        if moved.get("held") or moved.get("stopped_by_loop") or moved.get("stopped_by_contact"):
            raise BuildError(f"joint probe stopped before its declared target: {joint['name']}: {moved}")
        record = {"joint": joint["name"], "probe": probe, "moved": True, "restore_report": restored,
                  "bbox_before_mm": before.get("total", {}).get("bbox"),
                  "bbox_after_mm": after.get("total", {}).get("bbox")}
        if current:
            followers = {link["b"] for link in links}
            record["linked_values_native"] = {name: value for name, value in joint_values(current).items() if name in followers}
        receipt["joint_probes"].append(record)
    check_default_pose(client.execute("joint.list"), plan, links)


def save_studies_views(client, manifest, plan, links):
    independent = independent_joints(plan, links)
    by_name = {joint["name"]: joint for joint in independent}
    keys = [{"joint": joint["name"], "points": [[0, joint_units(joint, joint.get("default", 0))],
                                                [100, joint_units(joint, joint.get("default", 0))]]} for joint in independent]
    if keys:
        client.execute("motion.study", {"name": "Launch pose", "steps": 100, "keys": keys})
        steps = max(100, len(independent) * 20)
        inspection = []
        for index, joint in enumerate(independent):
            probe = linked_probe(joint, plan, links)
            if probe is None:
                continue
            default = joint_units(joint, joint.get("default", 0))
            inspection.append({"joint": joint["name"], "points": [[0, default], [index*20+2, default],
                               [index*20+10, joint_units(joint, probe)], [index*20+18, default], [steps, default]]})
        if inspection:
            client.execute("motion.study", {"name": "Articulation inspection", "steps": steps, "keys": inspection})
    for study in manifest.get("motion_studies", manifest.get("studies", [])):
        study_keys = []
        for key in study.get("keys", []):
            joint = by_name.get(key["joint"])
            if joint:
                study_keys.append({"joint": joint["name"], "points": [[step, joint_units(joint, value)] for step, value in key["points"]]})
        if study_keys:
            client.execute("motion.study", {"name": study["name"], "steps": study.get("steps", 100), "keys": study_keys})
    for name, camera in manifest.get("cameras", {}).items():
        client.execute("view.save", {"name": name, "camera": native_camera(camera)})


def variant_definition(manifest, name):
    if not name:
        return {}
    variants = manifest.get("inspection_variants", [])
    if isinstance(variants, dict):
        variants = [{"name": key, **value} for key, value in variants.items()]
    matches = [variant for variant in variants if variant.get("name") == name]
    if len(matches) != 1:
        raise BuildError(f"inspection variant must identify one manifest entry: {name!r}")
    return matches[0]


def matched_patterns(names, patterns, label):
    result = set()
    for pattern in patterns:
        matches = {name for name in names if fnmatch.fnmatchcase(name, pattern)}
        if not matches:
            raise BuildError(f"{label} pattern matched no retained item: {pattern!r}")
        result.update(matches)
    return result


def apply_variant(client, manifest, plan, variant, links, receipt):
    kept = {component["name"] for component in plan["components"]}
    receipt["removed_components"] = []
    for component in manifest["components"]:
        if component["name"] not in kept:
            client.execute("component.delete", {"component": component["name"]})
            receipt["removed_components"].append(component["name"])
    studies = client.execute("motion.list")
    if any(study.get("name") == "Launch pose" for study in studies.get("studies", [])):
        result = client.execute("motion.play", {"study": "Launch pose", "step": 0, "quiet": True})
        require_solution(result, "variant launch reset")
    joints = {joint["name"]: joint for joint in plan["joints"]}
    followers = {link["b"] for link in links}
    receipt["pose_changes"] = []
    for name, value in variant.get("pose", {}).items():
        if name not in joints or name in followers or joints[name].get("passive", False):
            raise BuildError(f"variant pose must drive a retained independent joint: {name}")
        value = number(value, name + " variant pose")
        result = client.execute("joint.drive", {"joint": name, "value": joint_units(joints[name], value), "quiet": True})
        require_solution(result, name)
        if result.get("held") or result.get("stopped_by_loop") or result.get("stopped_by_contact"):
            raise BuildError(f"variant pose did not reach its requested value: {name}: {result}")
        receipt["pose_changes"].append({"joint": name, "value": value, "moved": result.get("moved")})
    final_joints = client.execute("joint.list")
    values = joint_values(final_joints)
    for name, value in variant.get("pose", {}).items():
        if abs(values[name] - joint_units(joints[name], value)) > 1e-6:
            raise BuildError(f"variant pose value mismatch: {name}")
    check_links(final_joints, links)
    wanted_components = set(variant.get("hide_components", []))
    wanted_components.update(matched_patterns(kept, variant.get("hide_component_patterns", []), "component"))
    if wanted_components - kept:
        raise BuildError(f"variant hides unknown/removed components: {sorted(wanted_components-kept)}")
    all_bodies = {body["name"] for body in plan["bodies"]}
    hidden = set(variant.get("hide_bodies", []))
    hidden.update(matched_patterns(all_bodies, variant.get("hide_body_patterns", []), "body"))
    if hidden - all_bodies:
        raise BuildError(f"variant hides unknown bodies: {sorted(hidden-all_bodies)[:20]}")
    hidden.update(body["name"] for body in plan["bodies"] if body["component"] in wanted_components)
    for group in chunks(sorted(all_bodies-hidden)):
        client.execute("browser.visibility", {"items": group, "visible": True})
    for group in chunks(sorted(hidden)):
        client.execute("browser.visibility", {"items": group, "visible": False})
    if variant.get("view"):
        client.execute("view.apply", {"view": variant["view"]})
    independent = {joint["name"] for joint in independent_joints(plan, links)}
    if independent:
        client.execute("motion.study", {"name": variant.get("name", "Inspection") + " saved pose", "steps": 100,
                       "keys": [{"joint": name, "points": [[0, values[name]], [100, values[name]]]} for name in sorted(independent)]})
    receipt["hidden_body_names"] = sorted(hidden)
    return hidden


def build(args):
    manifest_path = Path(args.manifest).expanduser().resolve()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    root = manifest_path.parent
    variant = variant_definition(manifest, args.variant)
    subset = variant.get("subset", args.subset)
    if subset not in {"all", "aircraft", "carrier"}:
        raise BuildError(f"unknown subset: {subset}")
    plan = validate_manifest(copy.deepcopy(manifest), root, subset)
    links = links_for(manifest, plan)
    source = Path(args.input).expanduser().resolve() if args.input else None
    output = Path(args.output).expanduser().resolve()
    if source == output:
        raise BuildError("a variant must have a distinct output file")
    if variant and source is None:
        raise BuildError("--variant requires --input master.sc")
    if output.exists() and not args.force and not args.dry_run:
        raise BuildError(f"output exists; use --force to replace this generated file: {output}")
    if output.suffix.lower() not in {".sc", ".solidcraft"}:
        raise BuildError("native output must have .sc or .solidcraft extension")
    output.parent.mkdir(parents=True, exist_ok=True)
    receipts = output.with_name(output.stem + "-receipts")
    receipts.mkdir(parents=True, exist_ok=True)
    receipt = {"status": "planned", "started": stamp(), "output": str(output),
        "manifest": str(manifest_path), "manifest_sha256": sha256(manifest_path), "subset": subset,
        "components": plan["component_count"], "bodies": plan["body_count"], "source_triangles": plan["triangles"],
        "articulated_joints": sum(joint["kind"] != "rigid" for joint in plan["joints"]),
        "independent_drivers": len(independent_joints(plan, links)), "motion_links": links,
        "obj_units": manifest.get("obj_units", "mm"), "stages": [], "joint_probes": [], "source_imports": [],
        "threads": args.threads, "niceness": args.nice, "no_rendering": True}
    write_json(receipts / "build-receipt.json", receipt)
    if args.dry_run:
        write_json(receipts / "validated-plan.json", plan)
        progress("dry_run_complete", components=plan["component_count"], bodies=plan["body_count"],
                 joints=len(plan["joints"]), links=len(links), receipt=str(receipts / "build-receipt.json"))
        return 0
    cli = Path(args.cli).expanduser().resolve() if args.cli else Path("")
    receipt["release_proof"] = verify_release(cli)
    client = None
    started = time.monotonic()

    def stage(name):
        receipt["stages"].append({"name": name, "started": stamp()})
        receipt["status"] = "running"
        write_json(receipts / "build-receipt.json", receipt)
        progress("stage", name=name)

    try:
        allowed = [root, output.parent, receipts] + ([source.parent] if source else [])
        client = MCP(cli, allowed, receipts, args.timeout, args.threads, args.nice)
        receipt["server"] = client.server
        hidden = set()
        if source:
            stage("Open exact RC3 master read-only and derive inspection copy")
            receipt["source"] = {"path": str(source), "sha256": sha256(source), **native_container(source)}
            opened = client.execute("doc.open", {"path": str(source), "read_only": True})
            if opened.get("read_only") is not True or opened.get("errors") or opened.get("newer_file") or opened.get("warnings"):
                raise BuildError(f"source does not open cleanly in official RC3: {opened}")
            hidden = apply_variant(client, manifest, plan, variant, links, receipt)
        else:
            stage("Import original component geometry")
            client.execute("file.new", {"name": manifest.get("name", manifest.get("title", "F/A-18C - Stennis - official RC3"))})
            client.execute("document.metadata.set", {"values": {
                "project": "F/A-18C / CVN-74 original detailed showcase",
                "description": "Reference-led visual assembly with native articulation, authored for released SolidCraft 0.40 RC3.",
                "com.showcase.provenance": {"manifest_sha256": receipt["manifest_sha256"], "geometry_units": "m",
                                           "obj_units": receipt["obj_units"], "subset": subset, "release": RELEASE},
            }})
            occurrences = {}
            for index, component in enumerate(plan["components"], 1):
                progress("import", index=index, total=len(plan["components"]), component=component["name"])
                client.execute("component.activate", {"component": "root"})
                result = client.execute("file.insert_mesh", {"path": component["source"], "name": component["name"],
                                         "units": receipt["obj_units"], "origin": False})
                made = result.get("created_bodies", result.get("bodies", []))
                if set(made) != set(component["bodies"]) or len(made) != len(component["bodies"]):
                    raise BuildError(f"imported body names do not match {component['name']}")
                if result.get("warnings"):
                    raise BuildError(f"import warnings on {component['name']}: {result['warnings']}")
                occurrences[component["name"]] = result["occurrence"]
                receipt["source_imports"].append({"component": component["name"], "file": component["file"],
                                                 "bodies": len(made), "occurrence": result["occurrence"]})
            stage("Assign closest available physical materials and appearances")
            native_materials = {entry["name"] for entry in client.execute("material.list")["materials"]}
            physical = defaultdict(list)
            appearances = defaultdict(list)
            for body in plan["bodies"]:
                material = plan["materials"][body["material"]]
                physical[material.get("physical", "Aluminum")].append(body["name"])
                appearances[body["material"]].append(body["name"])
            if set(physical) - native_materials:
                raise BuildError(f"materials unavailable in official RC3: {sorted(set(physical)-native_materials)}")
            for name, bodies in physical.items():
                for group in chunks(bodies):
                    client.execute("material.assign", {"bodies": group, "material": name})
            for key, bodies in appearances.items():
                material = plan["materials"][key]
                look = {"name": material.get("name", key), "color": material["color"], "opacity": material.get("opacity", 1)}
                if look["opacity"] == 1:
                    look["pbr"] = {"metallic": material.get("metallic", 0), "roughness": material.get("roughness", 0.5),
                                   "dielectric_ior": material.get("ior", 1.5)}
                for group in chunks(bodies):
                    client.execute("appearance.assign", {"bodies": group, **look})
            receipt["physical_materials"] = {name: len(bodies) for name, bodies in physical.items()}
            stage("Create native joints, coupled mechanisms and launch pose")
            create_assembly(client, plan, links, occurrences, receipt, args)
            if args.checkpoint:
                receipt["assembly_checkpoint"] = save_native(client, receipts / "assembly-checkpoint.sc")
            if args.verify_joints:
                stage("Drive every independent mechanism and restore launch pose")
                verify_articulation(client, plan, links, occurrences, receipt)
            stage("Persist native motion studies and named inspection views")
            save_studies_views(client, manifest, plan, links)
        client.execute("browser.visibility", {"folder": "origin", "visible": False})
        client.execute("browser.visibility", {"folder": "joints", "visible": False})
        if args.view:
            client.execute("view.apply", {"view": args.view})
        stage("Validate native contents and save format 51")
        state = native_state(client)
        check_links(state["joints"], links)
        receipt["verification"] = verify_body_set(state, plan, hidden)
        write_json(receipts / "native-state.json", state)
        receipt["saved_native"] = save_native(client, output)
        # RC3 Save As from a read-only source names its new document after the file.
        # Account for that public-command title change, while comparing every part.
        saved_name = receipt["saved_native"]["native_reply"].get("name", state["document"].get("name"))
        if saved_name != state["document"].get("name"):
            receipt["save_name_change"] = {"before": state["document"].get("name"), "after": saved_name}
            state["document"]["name"] = saved_name
            for component in state["components"]["components"]:
                if component["id"] == 0:
                    component["name"] = saved_name
        write_json(receipts / "native-state.json", state)
        write_json(receipts / "command-timings.json", client.command_history)
        client.close()
        client = None
        stage("Reopen in a fresh official RC3 process and verify retained state")
        receipt["fresh_reopen"] = fresh_reopen(cli, output, receipts, state, plan, hidden, args)
        if source and sha256(source) != receipt["source"]["sha256"]:
            raise BuildError("source master changed while deriving inspection copy")
        receipt.update(status="complete", finished=stamp(), elapsed_seconds=round(time.monotonic()-started, 2))
        progress("complete", output=str(output), bytes=output.stat().st_size, **receipt["verification"])
        return 0
    except Exception as error:
        receipt.update(status="failed", error=str(error), finished=stamp(), elapsed_seconds=round(time.monotonic()-started, 2))
        progress("failed", error=str(error), receipt=str(receipts / "build-receipt.json"))
        return 1
    finally:
        if client is not None:
            write_json(receipts / "command-timings.json", client.command_history)
            client.close()
        write_json(receipts / "build-receipt.json", receipt)


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--cli", help="verified official Linux x86_64 RC3 CLI executable")
    parser.add_argument("--manifest", default="scene_manifest.json")
    parser.add_argument("--output", default="native/FA18C-Stennis-RC3.sc")
    parser.add_argument("--input", help="format51 master, opened read-only for an inspection copy")
    parser.add_argument("--variant", help="name of a manifest inspection_variants entry")
    parser.add_argument("--subset", choices=["all", "aircraft", "carrier"], default="all")
    parser.add_argument("--view", help="apply a saved named view; view.apply itself is transient in RC3")
    parser.add_argument("--threads", type=int, default=2)
    parser.add_argument("--nice", type=int, default=10)
    parser.add_argument("--timeout", type=float, default=900)
    parser.add_argument("--force", action="store_true", help="replace this generated output if present")
    parser.add_argument("--dry-run", action="store_true", help="validate manifest without launching SolidCraft")
    parser.add_argument("--checkpoint", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--auto-rigid", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--verify-joints", action=argparse.BooleanOptionalAction, default=True)
    args = parser.parse_args()
    if not 1 <= args.threads <= 64 or not 0 <= args.nice <= 19 or args.timeout <= 0:
        parser.error("threads must be 1..64, nice 0..19 and timeout positive")
    return args


if __name__ == "__main__":
    try:
        raise SystemExit(build(parse_args()))
    except (BuildError, OSError, ValueError, KeyError, subprocess.SubprocessError) as error:
        progress("failed", error=str(error))
        raise SystemExit(1)
