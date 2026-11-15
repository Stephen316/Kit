import argparse
import json
from pathlib import Path
import re
import shutil
import sys
from tempfile import TemporaryDirectory

from ApplicationProtocol import (
    ACKNOWLEDGEMENT, PROTOCOL, check_spool, configuration, directory, file_bytes,
    load_pinned, owner_lock, pin, record, require, sha256, sync_directory, write_record,
)

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from Adapters import A03Adapter
from OutputManifest import output_manifest


def stored_bytes(adapter, digest, target):
    require(isinstance(digest, str) and re.fullmatch("[0-9a-f]{64}", digest), "invalid accepted artifact digest")
    adapter.FetchInput(digest, target)
    return file_bytes(target)


def completed_job(adapter, job):
    rows = adapter.ReadStatus(job)["jobs"]
    require(len(rows) == 1 and rows[0]["id"] == job and rows[0]["state"] == "completed",
            "controller has no current completed attempt for this job")
    return rows[0]


def accepted_output(adapter, job, scratch):
    row = completed_job(adapter, job)
    receipt = json.loads(stored_bytes(adapter, row["receipt"], scratch / "receipt.json"))
    result = json.loads(stored_bytes(adapter, row["result"], scratch / "result.json"))
    require(receipt["receipt_version"] == 1 and receipt["job_id"] == job and receipt["outcome"] == "completed"
            and receipt["generation"] == row["generation"] and receipt["fingerprint"] == row["fingerprint"]
            and receipt["attempt"] == row["attempts"] and receipt["result_sha256"] == row["result"],
            "controller receipt does not bind the current completed attempt")
    native_receipt = result["receipt"]
    require(result["session_version"] == 1 and native_receipt["receipt_version"] == 1
            and native_receipt["job_id"] == job and native_receipt["attempt"] == receipt["attempt"]
            and native_receipt["orphan"] is False and native_receipt["stop_reason"] is None
            and native_receipt["exit_status"] == 0 and native_receipt["signal"] is None
            and result["result"]["outcome"] == "completed" and result["output_artifacts_version"] == 1,
            "accepted result is not a successful supervisor application attempt")
    manifest = output_manifest(result["output_artifacts"], paths=False)
    require(result["result"]["artifacts"] == manifest and "dispatch" in manifest,
            "accepted result lacks the durable dispatch artifact")
    require(manifest["dispatch"]["size_bytes"] <= 1024 * 1024, "durable dispatch exceeds its record limit")
    dispatch = stored_bytes(adapter, manifest["dispatch"]["sha256"], scratch / "dispatch.json")
    require(len(dispatch) == manifest["dispatch"]["size_bytes"], "durable dispatch size does not match the manifest")
    return row, manifest, dispatch


def retained_files(config, fence, manifest, content):
    require(fence["installation"] == config["installation"] and re.fullmatch("[0-9a-f]{32}", fence["job_id"]),
            "acceptance fence does not match the configured installation")
    files = output_manifest(fence["files"])
    refs = {role: {key: item[key] for key in ("sha256", "size_bytes")} for role, item in files.items()}
    require("dispatch" not in refs and {**refs, "dispatch": manifest["dispatch"]} == manifest,
            "accepted manifest does not match the complete retained output roster")
    dispatch = json.loads(content)
    require(isinstance(dispatch, dict) and isinstance(dispatch.get("proof"), dict)
            and dispatch["version"] == 1 and dispatch["installation"] == config["installation"]
            and dispatch["source_revision"] == config["source_revision"] and dispatch["status"] == "completed"
            and dispatch["host"] == fence["host"] and dispatch["files"] == files
            and dispatch["proof"].get("plan_sha256") == fence["plan_sha256"]
            and dispatch["proof"].get("restart_handoff") == fence["restart_handoff"],
            "durable dispatch does not match the retained completed phase")
    restart = fence["restart_handoff"]
    if restart is not None:
        require(restart["reason"] == "restart_required" and restart["installation"] == fence["installation"]
                and restart["job_id"] == fence["job_id"] and restart["host"] == fence["host"]
                and restart["plan_sha256"] == fence["plan_sha256"],
                "restart fence does not belong to the retained application process")
    return files


def spool_identity(spool, fence, files, dispatch, previous):
    identity = None
    if spool.exists() or spool.is_symlink():
        directory(spool)
        check_spool(spool)
        info = spool.stat()
        identity = [info.st_dev, info.st_ino]
        for name, expected in (
            ("phase.done", dispatch),
            ("pending-acceptance.json", fence),
            ("copied.json", {"status": "copied_pending_controller_acceptance", "artifacts": files}),
        ):
            path = spool / name
            if previous is None or path.exists():
                observed = file_bytes(path) if isinstance(expected, bytes) else record(path)
                require(observed == expected, f"retained {name} does not match the accepted phase")
        for item in files.values():
            path = spool / item["path"]
            if previous is None or path.exists():
                require(pin(path, item["path"]) == item, "retained output bytes changed")
    if previous is None:
        require(identity is not None, "retained spool is missing")
    elif identity is not None:
        require(identity == previous["spool_identity"], "retained spool was replaced after acknowledgement began")
    return identity


def read_optional(path):
    try:
        return record(path)
    except FileNotFoundError:
        return None


def finish_acknowledgement(root, fence_path, journal_path, spool, fence, state):
    require(record(fence_path) == fence, "application fence changed during acknowledgement")
    if spool.exists():
        shutil.rmtree(spool)
        sync_directory(spool.parent)
    require(record(fence_path) == fence, "application fence changed during acknowledgement")
    restart = fence["restart_handoff"]
    if restart is None:
        fence_path.unlink()
        sync_directory(root)
    else:
        write_record(fence_path, restart, replace=True)
    journal_path.unlink()
    sync_directory(root)
    return {**state, "status": "acknowledged", "restart_retained": restart is not None}


def reconcile(config, adapter, job, scratch):
    root = directory(config["endpoint"])
    fence_path = root / "fence.json"
    journal_path = root / ACKNOWLEDGEMENT
    with owner_lock(root / "dispatch.lock"):
        previous = read_optional(journal_path)
        fence = read_optional(fence_path)
        if fence is None or fence["reason"] != "acceptance_required":
            if previous is not None:
                saved = previous["fence"]
                require(previous["controller_job"] == job and saved["installation"] == config["installation"]
                        and re.fullmatch("[0-9a-f]{32}", saved["job_id"])
                        and (fence is None or fence == saved["restart_handoff"]),
                        "another acknowledgement or application recovery is pending")
                old_spool = root / "jobs" / saved["job_id"]
                require(not old_spool.exists() and not old_spool.is_symlink(), "acknowledged spool still needs recovery")
                journal_path.unlink()
                sync_directory(root)
            return {"status": "no_pending_acceptance"}
        row, manifest, dispatch = accepted_output(adapter, job, scratch)
        files = retained_files(config, fence, manifest, dispatch)
        spool = root / "jobs" / fence["job_id"]
        identity = spool_identity(spool, fence, files, dispatch, previous)
        state = {"version": 1, "controller_job": job, "result_sha256": row["result"],
                 "receipt_sha256": row["receipt"], "fence": fence, "dispatch_sha256": sha256(dispatch),
                 "spool_identity": identity if previous is None else previous["spool_identity"]}
        require(completed_job(adapter, job) == row and record(fence_path) == fence,
                "controller acceptance or the application fence changed during verification")
        if previous is None:
            write_record(journal_path, state)
        else:
            require(previous == state, "interrupted acknowledgement belongs to another accepted attempt")
        return finish_acknowledgement(root, fence_path, journal_path, spool, fence, state)


def main():
    parser = argparse.ArgumentParser(description="Acknowledge one application spool after verified A03 acceptance")
    parser.add_argument("--installation", type=Path, required=True)
    parser.add_argument("--store", type=Path, required=True)
    parser.add_argument("--job", required=True)
    args = parser.parse_args()
    try:
        config = configuration(args.installation)
        protocol_pin = load_pinned(config, PROTOCOL)["_source_pin"]
        installed_protocol = Path(__file__).with_name("ApplicationProtocol.py")
        require(sha256(file_bytes(installed_protocol)) == protocol_pin["sha256"],
                "acknowledgement protocol differs from the trusted installation")
        adapter = A03Adapter({"store": str(directory(args.store))})
        with TemporaryDirectory() as scratch:
            response = reconcile(config, adapter, args.job, Path(scratch))
        print(json.dumps(response, sort_keys=True))
        return 0
    except (OSError, ValueError, KeyError, TypeError, RecursionError) as error:
        print(f"application acknowledgement refused: {type(error).__name__}: {error}"[:2048], file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
