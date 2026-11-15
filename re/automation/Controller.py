import argparse
import json
import os
import sqlite3
import sys
from pathlib import Path

from GroupClaims import claim_group, read_group, renew_group, write_group
from GroupFinish import finish_group
from Ledger import Ledger
from OutputManifest import InvalidOutput
from Records import StaleLease, canonical, read_record
from RecoveryFence import StaleOwner, check_owner, rotate_owner


def main():
    parser = argparse.ArgumentParser(description="Local deterministic research job and evidence controller")
    parser.add_argument("--store", type=Path, required=True)
    parser.add_argument("--owner")
    commands = parser.add_subparsers(dest="command", required=True)
    initialize = commands.add_parser("init")
    initialize.add_argument("--max-running", type=int, default=4)
    ownership = commands.add_parser("rotate-owner")
    ownership.add_argument("--new-owner", required=True)
    binding = commands.add_parser("bind")
    binding.add_argument("name")
    binding.add_argument("file", type=Path)
    submit = commands.add_parser("submit")
    submit.add_argument("file", type=Path)
    batch = commands.add_parser("submit-batch")
    batch.add_argument("file", type=Path)
    resource = commands.add_parser("resource")
    resource.add_argument("name")
    availability = resource.add_mutually_exclusive_group()
    availability.add_argument("--available", action="store_true")
    availability.add_argument("--unavailable", action="store_true")
    resource.add_argument("--capacity", type=int)
    pool = commands.add_parser("pool")
    pool.add_argument("name")
    pool.add_argument("--kind", action="append", required=True)
    claim = commands.add_parser("claim")
    claim.add_argument("--worker", required=True)
    claim.add_argument("--pool")
    claim.add_argument("--claim-file", type=Path, required=True)
    grouped = commands.add_parser("claim-group")
    grouped.add_argument("--worker", required=True)
    grouped.add_argument("--pool", required=True)
    grouped.add_argument("--registry", type=Path, required=True)
    grouped.add_argument("--claim-dir", type=Path, required=True)
    renew = commands.add_parser("heartbeat-group")
    renew.add_argument("--lease", type=Path, required=True)
    grouped_finish = commands.add_parser("finish-group")
    grouped_finish.add_argument("--lease", type=Path, required=True)
    grouped_finish.add_argument("--result", type=Path, required=True)
    heartbeat = commands.add_parser("heartbeat")
    heartbeat.add_argument("--lease", type=Path, required=True)
    finish = commands.add_parser("finish")
    finish.add_argument("--lease", type=Path, required=True)
    finish.add_argument("--result", type=Path, required=True)
    finish.add_argument("--outcome", choices=("completed", "retry", "rejected", "waiting_evidence", "waiting_ci", "waiting_application"), required=True)
    finish.add_argument("--reason", required=True)
    finish.add_argument("--output-root", type=Path)
    status = commands.add_parser("status")
    status.add_argument("--job")
    status.add_argument("--after")
    commands.add_parser("events")
    artifact = commands.add_parser("artifact")
    artifact.add_argument("sha256")
    args = parser.parse_args()
    try:
        with Ledger(args.store, args.command == "init", getattr(args, "max_running", 4)) as ledger:
            if args.command != "rotate-owner":
                check_owner(ledger, args.owner)
            if args.command == "rotate-owner":
                if args.owner is not None:
                    raise ValueError("owner rotation must not reuse a supervised invocation")
                response = rotate_owner(ledger, args.new_owner)
            elif args.command == "init":
                response = {"store_version": 4, "max_running": ledger.db.execute("SELECT value FROM settings WHERE key='max_running'").fetchone()[0]}
            elif args.command == "bind":
                response = ledger.bind(args.name, args.file)
            elif args.command == "submit":
                response = ledger.submit(read_record(args.file))
            elif args.command == "submit-batch":
                record = read_record(args.file)
                if set(record) != {"jobs"}:
                    raise ValueError("batch record must contain only jobs")
                response = ledger.submit_many(record["jobs"])
            elif args.command == "resource":
                response = ledger.resource(args.name, True if args.available else False if args.unavailable else None, args.capacity)
            elif args.command == "pool":
                response = ledger.pool(args.name, args.kind)
            elif args.command == "claim-group":
                if args.claim_dir.exists() or args.claim_dir.is_symlink():
                    raise ValueError("group claim destination already exists")
                registry = read_record(args.registry)
                if set(registry) != {"group_registry_version", "kinds"} or type(registry["group_registry_version"]) is not int or registry["group_registry_version"] != 1:
                    raise ValueError("group registry must use version 1")
                claims = claim_group(ledger, args.worker, args.pool, registry["kinds"])
                if claims:
                    write_group(args.claim_dir, claims)
                response = {"count": len(claims)}
            elif args.command == "heartbeat-group":
                response = renew_group(ledger, read_group(args.lease))
            elif args.command == "finish-group":
                response = finish_group(ledger, args.lease, args.result)
            elif args.command == "claim":
                if args.claim_file.exists() or args.claim_file.is_symlink():
                    raise ValueError("claim destination already exists")
                leased = ledger.claim(args.worker, args.pool)
                if leased["job"] is not None:
                    content = canonical(leased) + "\n"
                    descriptor = os.open(args.claim_file, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
                    with os.fdopen(descriptor, "w", encoding="utf-8") as output:
                        output.write(content)
                        output.flush()
                        os.fsync(output.fileno())
                    response = {"job": leased["job"]["id"], "attempt": leased["attempt"], "claim_file": str(args.claim_file)}
                else:
                    response = leased
            elif args.command in ("heartbeat", "finish"):
                lease = read_record(args.lease)
                job_id = lease["job"]["id"]
                token = lease["lease_token"]
                if args.command == "heartbeat":
                    response = ledger.heartbeat(job_id, token)
                else:
                    response = ledger.finish(job_id, token, args.outcome, args.result, args.reason, args.output_root)
            elif args.command == "status":
                response = ledger.status(args.job, args.after)
            elif args.command == "events":
                response = ledger.events()
            else:
                response = {"sha256": args.sha256, "size_bytes": ledger.objects.verify(args.sha256), "path": str(ledger.objects.path(args.sha256))}
        print(canonical(response))
        return 0
    except StaleLease as error:
        print(f"controller stale lease: {error}", file=sys.stderr)
        return 3
    except StaleOwner as error:
        print(f"controller stale supervisor owner: {error}", file=sys.stderr)
        return 5
    except InvalidOutput as error:
        print(f"controller invalid output: {error}"[:4096], file=sys.stderr)
        return 4
    except ValueError as error:
        print(f"controller error: {error}", file=sys.stderr)
        return 1
    except (OSError, TypeError, KeyError, RecursionError, sqlite3.Error) as error:
        print(f"controller error: {type(error).__name__}; request not committed", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
