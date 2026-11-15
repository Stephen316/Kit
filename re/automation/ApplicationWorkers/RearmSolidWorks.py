import argparse
import json
import os
from pathlib import Path
import re
import sys
import time

from ApplicationProtocol import (
    ACKNOWLEDGEMENT, check_spool, committed_bytes, configuration, directory, encoded, file_bytes, identity,
    owner_lock, pin, record, request_link, require, sync_directory, validate_request,
)
from SolidWorksReadbackWorker import OPERATION, PROVIDER, plan_hash, verify_native_ticket, verify_sources

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from ApplicationHolds import commit_rearm, parked_timeout, rearm_history
from Artifacts import Artifacts
from Ledger import Ledger
from Records import digest, label
from RecoveryFence import check_owner, owner_digest


REARM = "re/automation/ApplicationWorkers/RearmSolidWorks.py"


def claim_from_stdin():
    content = sys.stdin.buffer.read(2049)
    require(len(content) <= 2048, "application rearm request exceeds its byte limit")
    value = json.loads(content)
    require(isinstance(value, dict) and set(value) == {"owner", "job_id", "generation", "fingerprint", "attempt", "session"}
            and all(type(value[key]) is int and value[key] > 0 for key in ("generation", "attempt"))
            and isinstance(value["fingerprint"], str) and re.fullmatch("[0-9a-f]{64}", value["fingerprint"])
            and isinstance(value["session"], str) and re.fullmatch("[0-9a-f]+-[0-9a-f]{8}", value["session"]),
            "invalid application rearm claim")
    label(value["job_id"])
    return value


def terminal_timeout(spool, config, timeout):
    request = record(spool / "native-timeout-request.json")
    validate_request(request, config, timeout["queue_job_id"], "phase")
    link = request_link(request)
    require(all(link[key] == timeout[key] for key in link)
            and request["body"] == {"phase": OPERATION, "plan_sha256": plan_hash(config)}
            and not os.path.lexists(spool / "phase.running") and not os.path.lexists(spool / "phase.request")
            and not os.path.lexists(spool / "pending-acceptance.json"),
            "terminal spool does not contain the exact timed-out request")
    if file_bytes(spool / "native-timeout-request.json") != encoded(request):
        raise ValueError("retained timeout request changed")
    disposition = record(spool / "native-recovery.json")
    terminal = record(spool / "phase.done")
    listener = disposition["listener"]
    expected = {"installation": config["installation"], "source_revision": config["source_revision"]}
    require(disposition["version"] == 2 and disposition["trigger"] == "collector_timeout"
            and disposition["status"] in ("already_exited", "terminated_owned_process")
            and all(disposition[key] == value for key, value in {**expected, **link}.items())
            and terminal["status"] == "expired" and terminal["provider"] == PROVIDER and terminal["host"] == listener
            and terminal["files"] == {} and terminal["proof"] is None and terminal["finished_at"] >= request["deadline"]
            and all(terminal[key] == value for key, value in {
                **expected, "request_sha256": link["request_sha256"], "nonce": link["nonce"],
            }.items()), "listener did not confirm cleanup of the same failed request")
    launch = record(spool / "readback/native-launch.json")
    require(launch["request_sha256"] == link["request_sha256"] and launch["source_revision"] == config["source_revision"]
            and launch["pid"] == disposition["pid"] and launch["created"] == disposition["created"]
            and verify_native_ticket(spool / "readback/native-owner.json", launch) == disposition["owner_ticket_sha256"],
            "confirmed exit does not match the exact native owner ticket")
    require(identity(listener["pid"]) == listener, "SOLIDWORKS timeout listener was replaced")
    return listener


def stage_spool(store, spool):
    check_spool(spool)
    objects = Artifacts(store)
    files = {}
    for path in sorted(spool.rglob("*")):
        if path.is_dir():
            continue
        relative = path.relative_to(spool).as_posix()
        item = pin(path, relative)
        require(objects.put_file(path) == item["sha256"], "failed spool changed during archival")
        files[relative] = {"sha256": item["sha256"], "size_bytes": item["size_bytes"]}
    require({path.relative_to(spool).as_posix() for path in spool.rglob("*") if not path.is_dir()} == files.keys()
            and all(pin(spool / name, name) == {"path": name, **item} for name, item in files.items()),
            "archived failure spool differs from its immutable manifest")
    return files


def read_hold(store, claim, owner, owner_pin):
    with Ledger(store) as ledger:
        check_owner(ledger.db, owner)
        prior = rearm_history(ledger, claim)
        if prior is not None:
            require(prior["claim_hash"] == digest({"claim": claim, "owner": owner_pin}),
                    "recorded rearm belongs to a different supervisor owner or attempt")
            ledger.verify_object(prior["archive"])
            return {"status": "already_rearmed", "archive": prior["archive"]}
        ledger.refresh()
        hold, _, _, timeout = parked_timeout(ledger, claim, owner_pin)
        return {"hold": dict(hold), "timeout": timeout}


def rearm(config, store, claim, owner):
    root = directory(config["endpoint"])
    owner_pin = owner_digest(owner)
    with owner_lock(root / "dispatch.lock"):
        parked = read_hold(store, claim, owner, owner_pin)
        if "status" in parked:
            return parked
        timeout = parked["timeout"]
        require(timeout["installation"] == config["installation"] and timeout["source_revision"] == config["source_revision"]
                and not os.path.lexists(root / ACKNOWLEDGEMENT),
                "parked attempt does not belong to this installation or another acknowledgement is pending")
        jobs = directory(root / "jobs")
        queue_job_id = timeout["queue_job_id"]
        active = jobs / queue_job_id
        failed = root / "failed-spools"
        archive = failed / queue_job_id
        in_archive = os.path.lexists(archive)
        if in_archive:
            directory(failed)
        spool = directory(archive if in_archive else active)
        require(list(jobs.iterdir()) == ([] if in_archive else [active]), "another application spool is pending")
        if not in_archive and not os.path.lexists(spool / "phase.done") and not os.path.lexists(spool / "phase.request"):
            return {"status": "pending_terminal"}
        fence_path = root / "fence.json"
        try:
            fence = record(fence_path)
        except FileNotFoundError:
            fence = None
        listener = terminal_timeout(spool, config, timeout)
        require((fence is None and in_archive) or (
                    isinstance(fence, dict) and fence["reason"] == "quarantined" and fence["job_id"] == queue_job_id
                    and fence["installation"] == config["installation"] and fence["host"] in (None, listener)
                ), "installation no longer holds the exact failed timeout fence")
        files = stage_spool(store, spool)
        with Ledger(store) as ledger:
            check_owner(ledger.db, owner)
            ledger.refresh()
            hold, receipt, spec, current = parked_timeout(ledger, claim, owner_pin)
            require(dict(hold) == parked["hold"] and current == timeout,
                    "controller hold changed while the failed spool was staged")
            require(terminal_timeout(spool, config, timeout) == listener,
                    "terminal timeout changed while the failed spool was staged")
            if fence is not None:
                require(record(fence_path) == fence, "application fence changed during archival")
            else:
                require(not os.path.lexists(fence_path), "a new application fence appeared")
            if not in_archive:
                directory(failed, True)
                os.rename(spool, archive)
                sync_directory(jobs)
                sync_directory(failed)
            archive_sha256 = ledger.objects.put_record({
                "version": 1, "claim": claim, "receipt": hold["receipt"], "result": hold["result"], "resource": hold["resource"],
                "epoch": hold["epoch"], "request_sha256": timeout["request_sha256"], "queue_job_id": queue_job_id,
                "fence": fence, "files": files,
            })
            commit_rearm(ledger, claim, owner_pin, hold, receipt, spec, archive_sha256)
            require(identity(listener["pid"]) == listener and not any(jobs.iterdir()),
                    "application listener or queue changed during archival")
            if fence is not None:
                require(record(fence_path) == fence, "application fence changed during archival")
                fence_path.unlink()
                sync_directory(root)
            return {"status": "rearmed", "archive": archive_sha256}


def main():
    parser = argparse.ArgumentParser(description="Rearm an exact, confirmed SOLIDWORKS timeout")
    parser.add_argument("--installation", type=Path, required=True)
    parser.add_argument("--store", type=Path, required=True)
    args = parser.parse_args()
    try:
        require(os.name == "nt", "SOLIDWORKS rearm requires Windows")
        claim = claim_from_stdin()
        owner = claim.pop("owner")
        config = configuration(directory(args.installation.parent) / args.installation.name)
        require(config["application"] == "solidworks", "installation does not own SOLIDWORKS")
        verify_sources(config)
        require(file_bytes(Path(__file__)) == committed_bytes(config, REARM),
                "running rearm source differs from the installed revision")
        store = directory(args.store)
        deadline = time.monotonic() + 15
        while True:
            response = rearm(config, store, claim, owner)
            if response["status"] != "pending_terminal":
                break
            require(time.monotonic() < deadline, "listener did not finalize the failed SOLIDWORKS request")
            time.sleep(0.15)
        print(json.dumps(response, sort_keys=True))
        return 0
    except (OSError, ValueError, KeyError, TypeError, RecursionError) as error:
        print(f"application rearm refused: {type(error).__name__}: {error}"[:2048], file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
