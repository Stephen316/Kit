import argparse
import json
import signal
import subprocess
import sys
import time
from pathlib import Path

from Adapters import A03Adapter
from CalibrationManifest import ROOT, file_identity, load_manifest, source_identity
from CalibrationMetrics import jobs as measured_jobs
from CalibrationMetrics import recommendation, summarize
from CalibrationProcesses import (
    force_stop,
    sample_workers,
    settle_supervisor,
    start_supervisor,
)
from HostResources import host_resources
from Ledger import Ledger
from LogCapture import LogCapture
from Records import canonical, digest
from Runners import Registry
from Sessions import write_private

STEPS = (1, 2, 4, 8, 16)
DEFAULT_MAX_CONCURRENCY = 8
LOG_LIMIT = 4 * 1048576


class Calibration:
    def __init__(self):
        self.interrupted = False
        self.output = None

    def interrupt(self, number, frame):
        self.interrupted = True

    def prepare(self, directory, requested, manifest, specifications, bindings):
        directory.mkdir(mode=0o700)
        store = directory / "Controller"
        with Ledger(store, True, requested) as ledger:
            ledger.pool(manifest["pool"], [manifest["kind"]])
            for name, settings in manifest["resources"].items():
                ledger.resource(
                    name, available=settings["available"], capacity=settings["capacity"]
                )
            for name, source in bindings.items():
                if self.interrupted:
                    raise InterruptedError(
                        "calibration interrupted during private input preparation"
                    )
                expected = {
                    key: manifest["bindings"][name][key]
                    for key in ("size_bytes", "sha256")
                }
                if (
                    file_identity(source) != expected
                    or ledger.bind(name, source)["sha256"] != expected["sha256"]
                ):
                    raise ValueError(
                        "calibration input changed during private preparation"
                    )
            ledger.submit_many(specifications)
            write_private(
                directory / "Prepared.json",
                {
                    "controller_max_running": int(
                        ledger.db.execute(
                            "SELECT value FROM settings WHERE key='max_running'"
                        ).fetchone()[0]
                    ),
                    "pool": manifest["pool"],
                    "kind": manifest["kind"],
                    "resources": manifest["resources"],
                    "job_fingerprints": {
                        job["id"]: digest(job) for job in specifications
                    },
                },
            )
        registry = {
            "runners": {
                manifest["kind"]: {
                    "pool": manifest["pool"],
                    "argv": [
                        sys.executable,
                        str(Path(__file__).with_name("CalibrationDecode.py")),
                        "{session}",
                    ],
                    "result_schema": str(
                        Path(__file__).with_name("CalibrationResult.json")
                    ),
                    **manifest["runner"],
                }
            }
        }
        write_private(directory / "Runners.json", registry)
        interpreted = Registry(directory / "Runners.json", ROOT)
        if interpreted.runners[manifest["kind"]].get(
            "group_protocol"
        ) is not None or any(
            key.startswith("group_") for key in registry["runners"][manifest["kind"]]
        ):
            raise ValueError(
                "calibration requires an explicitly single-job runner interpretation"
            )
        if interpreted.argv(manifest["kind"], directory / "Probe") != [
            sys.executable,
            str(Path(__file__).with_name("CalibrationDecode.py")),
            str(directory / "Probe"),
        ]:
            raise ValueError(
                "deployed runner argument interpretation differs from calibration"
            )
        write_private(
            directory / "RegistryContract.json",
            {
                "sha256": file_identity(directory / "Runners.json")["sha256"],
                "declared_group_fields": [],
                "runtime_group_protocol": interpreted.runners[manifest["kind"]].get(
                    "group_protocol"
                ),
                "single_job_per_session": True,
            },
        )
        config = {
            "state": str(directory / "State"),
            "controller": {"adapter": "a03", "store": str(store)},
            "registry": str(directory / "Runners.json"),
            "worker": "calibration:offline",
            "pools": {manifest["pool"]: {"max_sessions": requested}},
            "resources": {
                name: value["capacity"] for name, value in manifest["resources"].items()
            },
            "reserved_cpus": manifest["reserved_cpus"],
            "reserved_memory_mib": manifest["reserved_memory_mib"],
            "adaptive_limits": False,
            "stop_grace_seconds": 2,
            "poll_seconds": 0.1,
            "max_log_bytes": 1048576,
        }
        write_private(directory / "Supervisor.json", config)
        return A03Adapter({"store": str(store)})

    def supervise(self, directory, manifest, requested):
        command = [
            sys.executable,
            str(Path(__file__).with_name("Supervisor.py")),
            "--config",
            str(directory / "Supervisor.json"),
            "run",
            "--idle-seconds",
            "1",
            "--max-seconds",
            str(manifest["max_seconds"]),
        ]
        logs = {
            name: LogCapture(directory / f"{name}.log", LOG_LIMIT)
            for name in ("stdout", "stderr")
        }
        process, reason, limited, observations = None, None, set(), []
        samples, minimum_memory, peak_groups = 0, None, 0
        group_samples = 0
        observed_cpus = set()
        identity, forced = None, []
        started, offset, pending = time.monotonic(), 0, b""
        stop_at = None

        def observe():
            nonlocal samples, group_samples, minimum_memory, peak_groups
            host = host_resources()
            current_groups = sample_workers(process, directory)
            if current_groups is not None:
                group_samples += 1
                peak_groups = max(peak_groups, current_groups)
            observation = {
                "at_monotonic_ns": time.monotonic_ns(),
                "active_group_rss_bytes": current_groups,
                **host,
            }
            samples += 1
            observed_cpus.add(host["logical_cpus"])
            minimum_memory = (
                host["available_memory_bytes"]
                if minimum_memory is None
                else min(minimum_memory, host["available_memory_bytes"])
            )
            if len(observations) < 256:
                observations.append(observation)
            else:
                observations[-1] = observation
            return host

        try:
            process, identity = start_supervisor(
                command,
                ROOT,
                directory,
                logs["stdout"].writer,
                logs["stderr"].writer,
                manifest["pool"],
            )
            for capture in logs.values():
                capture.close_writer()
            owner = {"pid": process.pid, "process_start": identity}
            if sys.platform == "win32":
                owner["job_object"] = process.job_name
            write_private(
                directory / "SupervisorProcess.json",
                owner,
            )
            while process.poll() is None:
                for capture in logs.values():
                    capture.drain()
                host = observe()
                if (
                    host["available_memory_bytes"]
                    < manifest["reserved_memory_mib"] * 1048576
                ):
                    reason = reason or "memory_reserve_lost"
                if self.interrupted:
                    reason = reason or "interrupted"
                if time.monotonic() - started >= manifest["max_seconds"]:
                    reason = reason or "trial_timeout"
                with (directory / "stdout.log").open("rb") as source:
                    source.seek(offset)
                    content = source.read(262144)
                    offset += len(content)
                pending += content
                while b"\n" in pending:
                    line, pending = pending.split(b"\n", 1)
                    event = json.loads(line)
                    if event.get("event") == "finished" and (
                        event.get("outcome") != "completed"
                        or event.get("stale") is not False
                    ):
                        reason = reason or "child_did_not_complete"
                    if event.get("event") in {
                        "setup_failed",
                        "resource_measurement_error",
                        "orphan",
                    }:
                        reason = reason or "supervisor_failure"
                    if (
                        event.get("event") == "admission"
                        and event["running"] < requested
                        and event.get("reason") in {"cpu headroom", "memory headroom"}
                    ):
                        limited.add(event["reason"].replace(" ", "_"))
                if len(pending) > 65536 or any(
                    value.seen > value.retained for value in logs.values()
                ):
                    reason = reason or "supervisor_log_truncated_or_invalid"
                if reason is not None and stop_at is None:
                    process.terminate()
                    stop_at = time.monotonic()
                if stop_at is not None and time.monotonic() - stop_at > 10:
                    forced = force_stop(process, identity)
                    break
                time.sleep(0.1)
            if (
                sys.platform == "win32"
                and process.returncode == 0
                and reason is None
                and group_samples
            ):
                observe()
        except (OSError, ValueError, KeyError, TypeError) as error:
            reason = (
                reason or f"measurement_or_supervision_error:{type(error).__name__}"
            )
        finally:
            try:
                if process is not None:
                    forced.extend(
                        settle_supervisor(process, identity, stop_at is not None)
                    )
            finally:
                for capture in logs.values():
                    capture.close()
        if process is None or process.returncode != 0:
            reason = reason or "supervisor_nonzero_exit"
        if forced and sys.platform == "win32":
            reason = reason or "supervisor_forced_cleanup"
        if group_samples == 0 and sys.platform == "win32":
            reason = reason or "worker_memory_observation_unavailable"
        if any(value.seen > value.retained for value in logs.values()):
            reason = reason or "supervisor_log_truncated_or_invalid"
        if process is not None and process.returncode != 0:
            self.recover(directory, manifest["pool"])
        sessions = directory / "State" / "sessions"
        claims = directory / "State" / "claims"
        if (sessions.is_dir() and any(sessions.iterdir())) or (
            claims.is_dir() and any(claims.iterdir())
        ):
            self.recover(directory, manifest["pool"])
            if any(sessions.iterdir()) or any(claims.iterdir()):
                raise OSError("private calibration session cleanup is incomplete")
        job_custody = {}
        measurement_source = {}
        if sys.platform == "win32" and process is not None:
            job_custody = {"job_object": process.job_name, "job_members_empty": True}
            measurement_source = {
                "active_group_rss_source": "windows:nested_job:WorkingSetSize",
                "active_group_samples": group_samples,
            }
        write_private(
            directory / "Cleanup.json",
            {
                "supervisor_pid": None if process is None else process.pid,
                "supervisor_exit": None if process is None else process.returncode,
                "forced_groups": forced,
                "sessions_empty": not sessions.is_dir() or not any(sessions.iterdir()),
                "claims_empty": not claims.is_dir() or not any(claims.iterdir()),
                **job_custody,
            },
        )
        return (
            time.monotonic() - started,
            reason,
            sorted(limited),
            {
                "retained": observations,
                "samples": samples,
                "minimum_available_memory_bytes": minimum_memory,
                "peak_sampled_active_group_rss_bytes": peak_groups,
                "logical_cpu_counts_observed": sorted(observed_cpus),
                **measurement_source,
            },
            {name: value.receipt() for name, value in logs.items()},
        )

    def recover(self, directory, pool):
        command = [
            sys.executable,
            str(Path(__file__).with_name("Supervisor.py")),
            "--config",
            str(directory / "Supervisor.json"),
            "run",
            "--max-seconds",
            "0",
        ]
        capture = LogCapture(directory / "Recovery.log", LOG_LIMIT)
        process, identity = None, None
        try:
            process, identity = start_supervisor(
                command,
                ROOT,
                directory,
                capture.writer,
                None,
                pool,
            )
            capture.close_writer()
            until = time.monotonic() + 30
            while process.poll() is None:
                capture.drain()
                if time.monotonic() >= until:
                    _ = force_stop(process, identity)
                    raise OSError("private supervisor recovery timed out")
                time.sleep(0.05)
        finally:
            try:
                if process is not None:
                    forced = settle_supervisor(process, identity)
                    if forced and sys.platform == "win32":
                        raise OSError(
                            "private Windows supervisor recovery required forced cleanup"
                        )
            finally:
                capture.close()
                write_private(directory / "RecoveryReceipt.json", capture.receipt())
        if process is None or process.returncode != 0:
            raise OSError("private supervisor recovery failed")
        if capture.seen > capture.retained:
            raise OSError("private recovery log exceeded its retained limit")

    def run(self, manifest_path, output, max_concurrency=DEFAULT_MAX_CONCURRENCY):
        if max_concurrency not in (DEFAULT_MAX_CONCURRENCY, STEPS[-1]):
            raise ValueError("calibration maximum concurrency must be 8 or 16")
        steps = tuple(step for step in STEPS if step <= max_concurrency)
        if sys.platform not in ("linux", "darwin", "win32"):
            raise ValueError("offline calibration requires Linux, macOS, or Windows")
        if sys.version_info < (3, 14):
            raise ValueError(
                "offline calibration uses the Python 3.14 SDK reader contract"
            )
        if sys.platform == "win32" and sys.getwindowsversion().major < 10:
            raise ValueError("offline calibration requires Windows 10 or newer")
        manifest, specifications, bindings, manifest_sha = load_manifest(manifest_path)
        output = Path(output).absolute()
        if output.exists() or output.is_symlink():
            raise ValueError("calibration requires an unused output directory")
        output.mkdir(mode=0o700, parents=True)
        self.output = output
        write_private(output / "Manifest.json", manifest)
        (output / "Manifest.json").chmod(0o400)
        initial_sources = source_identity()
        identity = {"manifest_sha256": manifest_sha, **initial_sources}
        trials, summary, stopped = [], [], None
        for requested in steps:
            if self.interrupted:
                stopped = "interrupted"
                break
            directory = output / f"Trial{requested}"
            try:
                adapter = self.prepare(
                    directory, requested, manifest, specifications, bindings
                )
                host = host_resources()
            except (OSError, ValueError, KeyError, TypeError) as error:
                stopped = (
                    "interrupted"
                    if self.interrupted
                    else f"preparation_error:{type(error).__name__}"
                )
                trial = summarize(
                    requested, manifest, specifications, [], 0.0, stopped, [], identity
                )
                trial["error"] = str(error)[:2048]
                write_private(directory / "Trial.json", trial)
                trials.append(trial)
                summary.append(
                    {key: value for key, value in trial.items() if key != "jobs"}
                    | {"path": str(directory.relative_to(output) / "Trial.json")}
                )
                break
            current_identity = {
                **identity,
                "host_topology": {
                    key: host[key] for key in ("logical_cpus", "memory_source")
                },
            }
            current_identity["registry_sha256"] = file_identity(
                directory / "Runners.json"
            )["sha256"]
            if (
                host["available_memory_bytes"]
                < manifest["reserved_memory_mib"] * 1048576
            ):
                wall, reason, limited, observations, logs = (
                    0.0,
                    "memory_reserve_lost",
                    [],
                    {
                        "retained": [host],
                        "samples": 1,
                        "minimum_available_memory_bytes": host[
                            "available_memory_bytes"
                        ],
                    },
                    {},
                )
                write_private(
                    directory / "Cleanup.json",
                    {
                        "supervisor_pid": None,
                        "supervisor_exit": None,
                        "forced_groups": [],
                        "sessions_empty": True,
                        "claims_empty": True,
                    },
                )
            else:
                wall, reason, limited, observations, logs = self.supervise(
                    directory, manifest, requested
                )
            if source_identity() != initial_sources:
                reason = "sources_changed"
            records = measured_jobs(adapter, directory / "Controller", specifications)
            if any(
                record["state"] in {"failed", "rejected"}
                or record["attempts"] > 1
                or record["stop_reason"] is not None
                for record in records
            ):
                reason = reason or "child_did_not_complete"
            if any(
                value != host["logical_cpus"]
                for value in observations.get(
                    "logical_cpu_counts_observed", [host["logical_cpus"]]
                )
            ):
                limited = [*limited, "cpu_topology_changed"]
            limited.extend(
                f"resource_capacity:{name}"
                for name, settings in manifest["resources"].items()
                if settings["capacity"] < requested
                and all(name in job["resources"] for job in specifications)
            )
            trial = summarize(
                requested,
                manifest,
                specifications,
                records,
                wall,
                reason,
                limited,
                current_identity,
            )
            trial.update(
                {
                    "observations": observations,
                    "logs": logs,
                    "resources": manifest["resources"],
                    "reserved_cpus": manifest["reserved_cpus"],
                    "reserved_memory_mib": manifest["reserved_memory_mib"],
                }
            )
            write_private(directory / "Trial.json", trial)
            trials.append(trial)
            summary.append(
                {
                    key: value
                    for key, value in trial.items()
                    if key not in {"jobs", "observations"}
                }
                | {"path": str(directory.relative_to(output) / "Trial.json")}
            )
            if reason is not None:
                stopped = reason
                break
        if self.interrupted:
            stopped = stopped or "interrupted"
        recommended, comparisons = recommendation(trials)
        report = {
            "calibration_version": 1,
            **identity,
            "adaptive_limits": False,
            "grouping": False,
            "requested_steps": list(steps),
            "trials": summary,
            "completed_sweep": len(trials) == len(steps) and stopped is None,
            "stop_reason": stopped,
            "recommended_concurrency": recommended if stopped is None else None,
            "comparisons": comparisons,
            "native_acceptance": "not_established",
        }
        write_private(output / "Calibration.json", report)
        return report


def main():
    parser = argparse.ArgumentParser(
        description="Calibrate an explicit immutable offline decode manifest in private supervisor stores"
    )
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--max-concurrency", type=int, choices=(DEFAULT_MAX_CONCURRENCY, STEPS[-1]),
        default=DEFAULT_MAX_CONCURRENCY, help="include concurrency 16 in the fixed sweep",
    )
    args = parser.parse_args()
    calibration = Calibration()
    signal.signal(signal.SIGTERM, calibration.interrupt)
    signal.signal(signal.SIGINT, calibration.interrupt)
    try:
        report = calibration.run(args.manifest, args.output, args.max_concurrency)
        print(
            canonical(
                {
                    "output": str(args.output),
                    "completed_sweep": report["completed_sweep"],
                    "recommended_concurrency": report["recommended_concurrency"],
                    "stop_reason": report["stop_reason"],
                }
            ),
            flush=True,
        )
        return 0 if report["completed_sweep"] else 2
    except (
        OSError,
        ValueError,
        KeyError,
        TypeError,
        subprocess.SubprocessError,
    ) as error:
        failure = {
            "calibration_version": 1,
            "error": f"{type(error).__name__}: {error}"[:2048],
            "completed_sweep": False,
            "recommended_concurrency": None,
            "stop_reason": (
                "interrupted" if calibration.interrupted else "calibration_error"
            ),
            "cleanup_verified": False,
            "native_acceptance": "not_established",
        }
        if calibration.output is not None:
            write_private(calibration.output / "Calibration.json", failure)
        print(canonical(failure), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
