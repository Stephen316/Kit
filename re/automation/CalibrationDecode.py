import hashlib
import os
import sys
import time
from pathlib import Path

from Records import canonical
from Sessions import read_bounded, write_private

ROOT = Path(__file__).resolve().parents[2]
SOURCE = str(ROOT / "src")


def decode(content, kind, options):
    if SOURCE not in sys.path:
        sys.path.insert(0, SOURCE)
    if kind == "decode.solidworks":
        from convert.adapters.solidworks.core.Adapter import ReadSldprt

        return ReadSldprt(content, Config=options.get("configuration"))
    if kind != "decode.fusion":
        raise ValueError("only fixed offline decoder kinds are supported")
    from convert.adapters.base.ReadOptions import ReadOptions
    from convert.adapters.Fusion.Adapter import FusionReader

    reader = FusionReader()
    try:
        return reader.Read(content, ReadOptions(strict=True))
    except ValueError:
        if not options.get("allow_partial", False):
            raise
        return reader.Read(content, ReadOptions(strict=False))


def run(session):
    session = Path(session).resolve()
    path = session / "group.json"
    if not path.exists() and not path.is_symlink():
        decode_member(session, read_bounded(session / "job.json"))
        return
    if path.is_symlink() or (session / "job.json").exists():
        raise ValueError("group must have one distinct private manifest")
    group = read_bounded(path)
    if (
        not isinstance(group, dict)
        or set(group)
        != {"group_session_version", "session", "pool", "members", "stop_at"}
        or type(group["group_session_version"]) is not int
        or group["group_session_version"] != 1
        or group["session"] != session.name
    ):
        raise ValueError("decoder group manifest does not match protocol 1")
    members = group["members"]
    if (
        not isinstance(members, list)
        or not 2 <= len(members) <= 20
        or members != [f"jobs/{index:02d}/job.json" for index in range(len(members))]
    ):
        raise ValueError("decoder group must contain 2–20 ordered private members")
    packets, identities = [], set()
    for name in members:
        member = session / name
        if member.resolve() != member:
            raise ValueError("decoder group member is aliased")
        packet = read_bounded(member)
        if (
            type(packet["session_version"]) is not int
            or packet["session_version"] != 1
            or packet["session"] != group["session"]
            or packet["pool"] != group["pool"]
            or packet["stop_at"] != group["stop_at"]
            or packet["result"] != "result.json"
            or packet["job"]["id"] in identities
        ):
            raise ValueError("decoder member does not match the private group")
        identities.add(packet["job"]["id"])
        packets.append((member.parent, packet))
    for directory, packet in packets:
        decode_member(directory, packet)


def decode_member(session, packet):
    job = packet["job"]
    source = packet["inputs"]["source"]
    path = (session / source["path"]).resolve()
    if not path.is_relative_to(session / "inputs"):
        raise ValueError("calibration source must remain inside private session inputs")
    if path.stat().st_size > 256 * 1048576:
        raise ValueError("calibration source exceeds 256 MiB")
    content = path.read_bytes()
    if hashlib.sha256(content).hexdigest() != source["sha256"]:
        raise ValueError("calibration source digest changed")
    started = time.monotonic_ns()
    cpu_started = time.process_time_ns()
    try:
        document = decode(content, job["kind"], job["options"])
        document.assert_valid()
        encoded = document.to_json(indent=None).encode("utf-8")
        if len(encoded) > 64 * 1048576:
            raise ValueError("calibration neutral serialization exceeds 64 MiB")
        outcome, reason = (
            "completed",
            "offline decode and model serialization completed",
        )
        neutral = hashlib.sha256(encoded).hexdigest()
        counts = {
            "features": len(document.feature_timeline),
            "sketches": len(document.sketches),
            "bodies": len(document.bodies),
        }
    except Exception as error:
        outcome, reason = "rejected", f"{type(error).__name__}: {error}"[:2048]
        neutral, counts = None, None
    ended = time.monotonic_ns()
    cpu_ended = time.process_time_ns()
    user_seconds, system_seconds = process_cpu_seconds()
    records = {
        "calibration_version": 1,
        "job_id": job["id"],
        "kind": job["kind"],
        "input_sha256": source["sha256"],
        "decode_started_ns": started,
        "decode_ended_ns": ended,
        "decode_wall_seconds": (ended - started) / 1e9,
        "decode_cpu_seconds": (cpu_ended - cpu_started) / 1e9,
        "process_user_cpu_seconds": user_seconds,
        "process_system_cpu_seconds": system_seconds,
        "neutral_sha256": neutral,
        "counts": counts,
        "measurement_scope": "offline_reader_import_decode_validation_serialization",
        "native_acceptance": "not_established",
    }
    if sys.platform == "win32":
        from CalibrationWindowsMemory import worker_peak_working_set

        records["worker_peak_working_set_bytes"] = worker_peak_working_set()
    write_private(
        session / "result.json",
        {"outcome": outcome, "reason": reason, "records": records},
    )


def process_cpu_seconds():
    if sys.platform == "win32":
        usage = os.times()
        return usage.user, usage.system
    if sys.platform not in ("linux", "darwin"):
        raise ValueError("offline calibration CPU measurements are unavailable")
    import resource

    usage = resource.getrusage(resource.RUSAGE_SELF)
    return usage.ru_utime, usage.ru_stime


if __name__ == "__main__":
    try:
        if len(sys.argv) != 2:
            raise ValueError("one private session path is required")
        run(sys.argv[1])
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(canonical({"error": str(error)[:2048]}), file=sys.stderr)
        sys.exit(1)
