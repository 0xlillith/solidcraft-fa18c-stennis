"""Deterministic cockpit-to-assembly demonstration links for official RC3.

Original geometric couplings, not an F/A-18 flight-control or avionics simulation.
Source slider limits/key points are metres; motion-link ratios/offsets use native
millimetres/degrees. See CONTROL_COUPLINGS.md and the rejected coaxial smoke trace.
"""
from __future__ import annotations
import math

ROLL_MODE = "direct bounded aileron demonstration; automatic flap mixing omitted"
DRIVERS = {
    "pitch": "Control stick pitch",
    "roll": "Control stick roll",
    "yaw": "Left rudder input",
    "flap": "Flap selector cockpit handle motion",
    "gear": "Landing gear cockpit handle motion",
    "hook": "Arresting hook cockpit handle motion",
    "fold": "Wing fold cockpit handle motion",
}


def _joints(scene):
    result = {j["name"]: j for j in scene.joints}
    if len(result) != len(scene.joints):
        raise ValueError("Duplicate joint name before connecting cockpit controls")
    return result


def _require(joints, name):
    if name not in joints:
        raise ValueError("Cockpit coupling requires joint: " + name)
    return joints[name]


def _native(joint, value):
    return value * (1000.0 if joint["kind"] == "slider" else 1.0)


def _link(scene, joints, driver, follower, ratio, offset=0.0):
    a, b = _require(joints, driver), _require(joints, follower)
    if a.get("passive") or b.get("passive"):
        raise ValueError("Cannot link a passive linkage endpoint: " + follower)
    if a["kind"] not in ("revolute", "slider") or b["kind"] not in ("revolute", "slider"):
        raise ValueError("Demonstration links require scalar mechanical joints")
    record = {"a": driver, "b": follower, "ratio": float(ratio), "offset": float(offset)}
    old = [x for x in scene.motion_links if x["b"] == follower]
    if old:
        if len(old) == 1 and all(abs(old[0].get(k, 0)-record[k]) < 1e-12 for k in ("ratio", "offset")) and old[0]["a"] == driver:
            return
        raise ValueError("Follower already has a driver: " + follower)
    lo, hi = sorted(ratio * _native(a, v) + offset for v in a["limits"])
    blo, bhi = (_native(b, v) for v in b["limits"])
    if lo < blo - 1e-7 or hi > bhi + 1e-7:
        raise ValueError(f"Coupling exceeds {follower} limits: {lo}..{hi}, permitted {blo}..{bhi}")
    expected = ratio * _native(a, a.get("default", 0)) + offset
    if abs(expected - _native(b, b.get("default", 0))) > 1e-7:
        raise ValueError("Coupling changes declared default: " + follower)
    scene.motion_links.append(record)


def connect(scene):
    """Add checked one-driver links. Call after aircraft, cockpit and internals."""
    if getattr(scene, "_cockpit_couplings_connected", False):
        return scene
    joints = _joints(scene)
    for name in DRIVERS.values():
        _require(joints, name)
    # Range choices are display-model inputs. They preserve every follower limit.
    joints[DRIVERS["flap"]]["limits"] = [-30, 15]
    joints[DRIVERS["gear"]]["limits"] = [-55, 0]
    joints[DRIVERS["hook"]]["limits"] = [-50, 0]
    joints[DRIVERS["fold"]]["limits"] = [0, 90]
    for name in ("flap", "gear", "hook", "fold"):
        joints[DRIVERS[name]]["default"] = 0

    for side in ("Port", "Starboard"):
        _link(scene, joints, DRIVERS["pitch"], side + " stabilator pitch", 1, -4)
    # Slider source units are m; a link sees its native value in mm.
    _link(scene, joints, DRIVERS["yaw"], "Right rudder input", -1)
    for side in ("Port", "Starboard"):
        _link(scene, joints, DRIVERS["yaw"], side + " rudder", 2/3)
    steering = "Nosewheel steering" if "Nosewheel steering" in joints else "Nose wheel steering"
    _link(scene, joints, DRIVERS["yaw"], steering, .9)

    # RC3's redundant coaxial total-stop loop was tested and rejected: it moves
    # the other free cockpit input. A direct bounded link retains independence.
    # Positive stick roll about +X moves the grip to port: port aileron rises.
    _link(scene, joints, DRIVERS["roll"], "Port aileron droop", -.8, 30)
    _link(scene, joints, DRIVERS["roll"], "Starboard aileron droop", .8, 30)
    for side in ("Port", "Starboard"):
        _link(scene, joints, DRIVERS["flap"], side + " TE flap", 1, 30)
        for part in ("inner", "outer"):
            _link(scene, joints, DRIVERS["flap"], side + " " + part + " LE flap", .4, 12)

    for name in ("Nose gear retract", "Port main gear retract", "Starboard main gear retract"):
        joint = _require(joints, name)
        if abs(joint.get("default", 0)) > 1e-9:
            raise ValueError("Gear coupling expects neutral down pose: " + name)
        endpoints = [v for v in joint["limits"] if abs(v) > 1e-9]
        if len(endpoints) != 1:
            raise ValueError("Gear root needs one nonzero stowed endpoint: " + name)
        _link(scene, joints, DRIVERS["gear"], name, endpoints[0]/-55)
    _link(scene, joints, DRIVERS["hook"], "Arresting hook lower", -42/50)
    for side in ("Port", "Starboard"):
        _link(scene, joints, DRIVERS["fold"], side + " wing fold", 100/90)

    # Dependency graph must remain a forest: one follower, no feedback cycle.
    parents = {x["b"]: x["a"] for x in scene.motion_links}
    if len(parents) != len(scene.motion_links):
        raise ValueError("A mechanical follower has multiple drivers")
    for node in parents:
        seen = set()
        while node in parents:
            if node in seen:
                raise ValueError("Motion-link dependency cycle")
            seen.add(node)
            node = parents[node]
    scene.notes.append(
        "Cockpit links are geometric demonstration couplings, not F/A-18 FLCS, "
        "avionics or engine-control simulation. Stick pitch drives both stabilators; "
        "left pedal counter-drives the right pedal and drives rudders/NWS; "
        "flap selector drives TE/LE only; gear, hook and wingfold handles drive their "
        "assemblies. Ailerons follow stick roll around the 30-degree launch droop, "
        "within 15.6..44.4 degrees. Automatic aileron/flap mixing is intentionally "
        "omitted because the tested RC3 coaxial stop loop displaced the other input. "
        "Engine shaft/nozzle/variable-geometry motions remain separately inspectable."
    )
    scene._cockpit_couplings_connected = True
    return scene


def studies(scene):
    """Return authored-unit motion-study definitions; no rendering is requested."""
    joints = _joints(scene)
    followers = {link["b"] for link in scene.motion_links}
    available = {name: j for name, j in joints.items()
                 if j["kind"] in ("revolute", "slider") and not j.get("passive") and name not in followers}
    result = []
    bar = available.get("Launch bar lift")
    bar_stow = getattr(scene, "gear_retract_pose", {}).get(
        "Launch bar lift", max(bar["limits"], key=abs) if bar else 0)

    def add(name, rows, steps=100):
        keys = []
        for joint_name, points in rows:
            if joint_name not in available:
                continue
            joint = available[joint_name]
            low, high = joint["limits"]
            points = [[int(step), float(value)] for step, value in points]
            if any(not math.isfinite(value) or value < low-1e-9 or value > high+1e-9 or step < 0 or step > steps for step, value in points):
                raise ValueError("Study key exceeds joint/step range: " + joint_name)
            if [p[0] for p in points] != sorted(set(p[0] for p in points)):
                raise ValueError("Study key steps must increase: " + joint_name)
            keys.append({"joint": joint_name, "points": points})
        if keys:
            result.append({"name": name, "steps": steps, "keys": keys})

    def constant(name):
        if name not in available:
            return (name, [])
        return name, [[0, available[name].get("default", 0)], [100, available[name].get("default", 0)]]

    add("Cockpit access - slide then hinge", [
        ("Canopy manual lock lever", [[0,0],[5,-35],[90,-35],[100,0]]),
        ("Canopy unlatch slide", [[0,0],[10,.0381],[90,.0381],[100,0]]),
        ("Canopy open", [[0,0],[10,0],[35,68],[75,68],[90,0],[100,0]]),
        ("Boarding ladder deploy", [[0,0],[35,90],[75,90],[100,0]]),
    ])
    add("Cockpit flight controls - linked surfaces", [
        (DRIVERS["pitch"], [[0,0],[15,15],[30,-15],[45,0],[100,0]]),
        (DRIVERS["roll"], [[0,0],[45,0],[55,18],[65,-18],[75,0],[100,0]]),
        (DRIVERS["yaw"], [[0,0],[75,0],[83,.045],[92,-.045],[100,0]]),
        ("Left toe brake", [[0,0],[82,0],[87,15],[92,0],[100,0]]),
        ("Right toe brake", [[0,0],[87,0],[92,15],[97,0],[100,0]]),
        constant(DRIVERS["flap"]),
    ])
    add("Flap selector - AUTO HALF FULL geometry", [
        (DRIVERS["flap"], [[0,0],[20,-30],[40,-30],[60,0],[80,15],[90,15],[100,0]]),
        constant(DRIVERS["roll"]),
    ])
    add("Wing fold - cockpit handle", [
        (DRIVERS["flap"], [[0,0],[15,-30],[85,-30],[100,0]]),
        (DRIVERS["fold"], [[0,0],[15,0],[40,90],[65,90],[85,0],[100,0]]),
        constant(DRIVERS["roll"]),
    ])

    gear_rows = [
        (DRIVERS["gear"], [[0,0],[20,0],[45,-55],[65,-55],[75,-55],[95,0],[100,0]]),
        ("Launch bar lift", [[0,0],[8,0],[18,bar_stow],[95,bar_stow],[100,0]]),
        constant(DRIVERS["yaw"]),
    ]
    for name in ("Nose Port door", "Nose Starboard door", "Port main bay door", "Starboard main bay door"):
        if name in available:
            j = available[name]
            opened, default = j["limits"][1], j.get("default", 0)
            gear_rows.append((name, [[0,default],[8,opened],[45,opened],[55,0],[65,0],[75,opened],[95,opened],[100,default]]))
    add("Landing gear - cockpit lever and doors", gear_rows)
    add("Arresting hook - cockpit handle", [
        (DRIVERS["hook"], [[0,0],[35,-50],[70,-50],[100,0]]),
    ])
    add("Speedbrake and launch bar", [
        ("Dorsal speedbrake", [[0,0],[30,60],[65,60],[100,0]]),
        ("Launch bar lift", [[0,0],[30,bar_stow],[65,bar_stow],[100,0]]),
    ])
    add("Refuelling probe and door", [
        ("Probe door open", [[0,0],[15,95],[85,95],[100,0]]),
        ("Refuelling probe extend", [[0,0],[15,0],[40,65],[65,65],[85,0],[100,0]]),
    ])
    add("Radar service and gimbals", [
        ("Radome service opening", [[0,0],[20,95],[80,95],[100,0]]),
        ("Radar azimuth", [[0,0],[20,0],[35,35],[50,-35],[65,0],[100,0]]),
        ("Radar elevation", [[0,0],[35,0],[50,22],[65,-22],[80,0],[100,0]]),
    ])

    trays = []
    for name, j in available.items():
        if "avionics tray withdrawal" in name or (name.endswith(" lift") and "lid" in name.lower()):
            extent = min(j["limits"][1], .25 if j["kind"] == "slider" else j["limits"][1])
            trays.append((name, [[0,0],[35,extent],[65,extent],[100,0]]))
    add("Avionics trays and removable covers", trays)

    spool_rows = []
    for side in ("Port", "Starboard"):
        for spool, turns in (("N1",10),("N2",15)):
            name = side + " F404 " + spool + " shaft rotation"
            spool_rows.append((name, [[0,0],[240,360*turns]]))
    add("F404 independent two-spool rotation", spool_rows, 240)

    engine_rows = []
    for side in ("Port", "Starboard"):
        engine_rows.extend([
            (side+" F404 nozzle actuator travel", [[0,0],[25,.025],[50,0],[75,-.025],[100,0]]),
            (side+" F404 fan variable guide control drive", [[0,0],[25,.75],[50,0],[75,-.75],[100,0]]),
            (side+" F404 HPC variable guide control drive", [[0,0],[25,-.75],[50,0],[75,.75],[100,0]]),
        ])
    add("F404 nozzle and variable guide mechanisms", engine_rows)
    add("Throttle and HOTAS grip travel", [
        ("Left throttle travel", [[0,0],[25,35],[50,-20],[75,0],[100,0]]),
        ("Right throttle travel", [[0,0],[25,35],[50,-20],[75,0],[100,0]]),
        ("Stick trigger", [[0,0],[75,0],[85,12],[100,0]]),
        ("Stick paddle disconnect", [[0,0],[85,0],[92,10],[100,0]]),
    ])
    return result
