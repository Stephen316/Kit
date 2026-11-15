import hashlib
import json
import sys
import time
from pathlib import Path

from Records import canonical
from Sessions import read_bounded, write_private

ROOT = Path(__file__).resolve().parents[2]


def decode(content, kind, options):
    sys.path.insert(0, str(ROOT / "src"))
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
    if sys.platform not in ("linux", "darwin"):
        raise ValueError("offline calibration CPU measurements require Linux or macOS")
    import resource

    session = Path(session).resolve()
    packet = read_bounded(session / "job.json")
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
    usage = resource.getrusage(resource.RUSAGE_SELF)
    records = {
        "calibration_version": 1,
        "job_id": job["id"],
        "kind": job["kind"],
        "input_sha256": source["sha256"],
        "decode_started_ns": started,
        "decode_ended_ns": ended,
        "decode_wall_seconds": (ended - started) / 1e9,
        "decode_cpu_seconds": (cpu_ended - cpu_started) / 1e9,
        "process_user_cpu_seconds": usage.ru_utime,
        "process_system_cpu_seconds": usage.ru_stime,
        "neutral_sha256": neutral,
        "counts": counts,
        "measurement_scope": "offline_reader_import_decode_validation_serialization",
        "native_acceptance": "not_established",
    }
    write_private(
        session / "result.json",
        {"outcome": outcome, "reason": reason, "records": records},
    )


if __name__ == "__main__":
    try:
        if len(sys.argv) != 2:
            raise ValueError("one private session path is required")
        run(sys.argv[1])
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(canonical({"error": str(error)[:2048]}), file=sys.stderr)
        sys.exit(1)
