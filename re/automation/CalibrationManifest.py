import hashlib
import importlib.metadata
import json
import sys
from pathlib import Path

from Records import bounded, canonical, label, read_record, specification

KINDS = {"decode.solidworks", "decode.fusion"}
FIELDS = {
    "calibration_version",
    "kind",
    "pool",
    "runner",
    "bindings",
    "resources",
    "jobs",
    "reserved_cpus",
    "reserved_memory_mib",
    "max_seconds",
}
ROOT = Path(__file__).resolve().parents[2]


def file_identity(path):
    path = Path(path)
    if not path.is_file():
        raise ValueError("calibration input must be a regular file")
    size, hasher = 0, hashlib.sha256()
    with path.open("rb") as source:
        while chunk := source.read(1048576):
            size += len(chunk)
            if size > 256 * 1048576:
                raise ValueError("calibration input exceeds 256 MiB")
            hasher.update(chunk)
    return {"size_bytes": size, "sha256": hasher.hexdigest()}


def source_identity():
    files = sorted(
        path
        for path in (ROOT / "src").rglob("*")
        if path.is_file() and path.suffix in {".py", ".json", ".sql"}
    )
    files += sorted(Path(__file__).parent.glob("*.py")) + sorted(
        Path(__file__).parent.glob("*.sql")
    )
    files += [
        Path(__file__).with_name("CalibrationResult.json"),
        ROOT / "pyproject.toml",
        ROOT / "uv.lock",
    ]
    values = {
        str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in files
        if path.is_file()
    }
    packages = sorted(
        (entry.metadata.get("Name", ""), entry.version)
        for entry in importlib.metadata.distributions()
    )
    return {
        "sources_sha256": hashlib.sha256(
            json.dumps(values, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest(),
        "python": sys.version,
        "python_executable": sys.executable,
        "packages_sha256": hashlib.sha256(
            json.dumps(packages, separators=(",", ":")).encode()
        ).hexdigest(),
    }


def load_manifest(path):
    path = Path(path).resolve()
    record = read_record(path)
    if (
        set(record) != FIELDS
        or type(record["calibration_version"]) is not int
        or record["calibration_version"] != 1
    ):
        raise ValueError("calibration manifest fields do not match version 1")
    if record["kind"] not in KINDS:
        raise ValueError("calibration accepts fixed offline decoder kinds only")
    label(record["pool"])
    runner = record["runner"]
    if not isinstance(runner, dict) or set(runner) != {
        "threads",
        "initial_peak_memory_mib",
        "max_memory_mib",
    }:
        raise ValueError(
            "calibration runner must declare threads and memory estimates/limits"
        )
    bounded(runner["threads"], 1, 8)
    for name in ("initial_peak_memory_mib", "max_memory_mib"):
        bounded(runner[name], 1, 16384)
    if runner["initial_peak_memory_mib"] > runner["max_memory_mib"]:
        raise ValueError("initial memory estimate exceeds the runner limit")
    bounded(record["reserved_cpus"], 1, 65536)
    bounded(record["reserved_memory_mib"], 1, 1048576)
    bounded(record["max_seconds"], 5, 3600)
    if not isinstance(record["resources"], dict) or len(record["resources"]) > 64:
        raise ValueError(
            "calibration resources must map at most 64 capacities and availability flags"
        )
    for name, settings in record["resources"].items():
        label(name)
        if (
            not isinstance(settings, dict)
            or set(settings) != {"capacity", "available"}
            or type(settings["available"]) is not bool
        ):
            raise ValueError("resource must declare capacity and actual availability")
        bounded(settings["capacity"], 1, 64)
    bindings = record["bindings"]
    if not isinstance(bindings, dict) or not 1 <= len(bindings) <= 256:
        raise ValueError("calibration requires 1–256 explicit input bindings")
    resolved, total = {}, 0
    for name, value in bindings.items():
        label(name)
        if (
            not isinstance(value, dict)
            or set(value) != {"path", "sha256", "size_bytes"}
            or not isinstance(value["path"], str)
            or not 1 <= len(value["path"]) <= 4096
        ):
            raise ValueError("binding must declare a bounded path, SHA-256 and size")
        bounded(value["size_bytes"], 1, 256 * 1048576)
        source = (path.parent / value["path"]).resolve()
        measured = file_identity(source)
        if measured != {key: value[key] for key in ("sha256", "size_bytes")}:
            raise ValueError(
                "calibration binding does not match its immutable digest/size"
            )
        total += measured["size_bytes"]
        if total > 512 * 1048576:
            raise ValueError("calibration input bindings exceed 512 MiB")
        resolved[name] = source
    if not isinstance(record["jobs"], list) or not 8 <= len(record["jobs"]) <= 256:
        raise ValueError("calibration requires 8–256 explicitly listed jobs")
    jobs = [specification(value) for value in record["jobs"]]
    if len({job["id"] for job in jobs}) != len(jobs):
        raise ValueError("calibration job IDs must be distinct")
    allowed = (
        {"configuration"}
        if record["kind"] == "decode.solidworks"
        else {"allow_partial"}
    )
    for job in jobs:
        if job["kind"] != record["kind"] or job["depends_on"]:
            raise ValueError(
                "calibration jobs must use the selected offline kind and have no dependencies"
            )
        if set(job["inputs"]) != {"source"} or job["inputs"]["source"] not in resolved:
            raise ValueError(
                "calibration jobs require exactly one explicit source binding"
            )
        if not set(job["resources"]) <= record["resources"].keys():
            raise ValueError(
                "calibration job resources must retain declared capacities"
            )
        options = job["options"]
        if options.keys() - allowed:
            raise ValueError("unsupported offline decoder options")
        if "allow_partial" in options and type(options["allow_partial"]) is not bool:
            raise ValueError("allow_partial must be a boolean")
        if "configuration" in options and (
            not isinstance(options["configuration"], str)
            or not 1 <= len(options["configuration"]) <= 256
        ):
            raise ValueError("configuration must contain 1–256 characters")
    return (
        record,
        jobs,
        resolved,
        hashlib.sha256(canonical(record).encode()).hexdigest(),
    )
