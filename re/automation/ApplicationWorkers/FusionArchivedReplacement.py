import json
import os
import subprocess
import time
from contextlib import contextmanager
from functools import partial
from pathlib import Path
from tempfile import TemporaryDirectory

from ApplicationProtocol import (
    encoded,
    file_bytes,
    identity,
    owner_lock,
    require,
    sha256,
    write_new,
)
from ArchiveFusionProbe import current_probe
from FusionArchiveReplacementRecords import (
    optional_receipt,
    read_peer_receipt,
    startup_proof,
)
from FusionExitRecords import read_pinned
from FusionOwnerRecovery import retain_recovery
from FusionProbeArchiveCustody import authorize_archive
from FusionQueueReceipt import owned_bytes
from FusionRecoveryBasis import archived_request
from FusionReplacementLaunch import bundle_pins, replacement_source
from FusionTimeoutAudit import inspect_archive
from MacApplicationBundle import pinned_bundle
from MacBundleLaunch import MacLaunchError, launch_bundle
from QueueFusionPhases import queue_configuration
from RetryFusionProbe import require_idle
from StoreRead import read_store


# reading the already released archive must allow a legitimate new host to own the host lock
@contextmanager
def retained_archive(owner, path, queue, kind, raw):
    store, config, _ = queue_configuration(owner.args.config, kind, queue["resource"])
    require(store == owner.store, "Fusion archive replacement store changed")
    require_idle(owner.root)
    require(
        not os.path.lexists(owner.root / "fusion-lifecycle-active.json"),
        "Fusion owner is already rotating another process",
    )
    with (
        read_store(store / "ledger.sqlite3", None, (4,)) as database,
        TemporaryDirectory(prefix="kit-fusion-replacement-archive-") as temporary,
    ):
        timeout = current_probe(database, store, queue, kind, Path(temporary))
        authorize = authorize_archive(
            owner, path, queue, raw, database, config, timeout
        )
        archive = inspect_archive(owner.root, config, timeout)
        require(
            archive["status"] == "archived" and archive["fence_status"] == "absent",
            "Fusion archive replacement requires a released probe archive",
        )
        archive_sha = archive["archive_manifest_sha256"]
        manifest, request = archived_request(owner.root, config, timeout, archive_sha)
        authorize(request["client"], manifest["fence"]["at"])
        saved = {
            "archive_manifest_sha256": archive_sha,
            **retain_recovery(owner, queue, raw, database, config, timeout, archive),
        }
        yield saved, timeout


# the source rechecks the current parked archive immediately before the native submission
@contextmanager
def launch_gate(snapshot, expected, path, request_raw, old):
    with exact_archive(snapshot, expected, path, request_raw):
        require(identity(old["pid"]) is None, "prior Fusion process ID is still in use")
        yield


# no provider reply can be trusted after the controller or request loses custody
@contextmanager
def exact_archive(snapshot, expected, path, request_raw):
    with snapshot() as (current, _):
        require(
            current == expected and owned_bytes(path) == request_raw,
            "Fusion archive launch admission changed",
        )
        yield


# existing launch bindings are replayable only as evidence and never resend the native effect
def reconcile_replacement(owner, path, queue, kind, raw):
    snapshot = partial(retained_archive, owner, path, queue, kind, raw)
    with owner_lock(owner.root / "dispatch.lock"):
        with snapshot() as (archive, timeout):
            if archive.get("replacement_preflight_status") != "sealed":
                return archive
            prepared = prepare_launch(owner, archive, timeout)
        result = observe_launch(owner, snapshot, archive, prepared)
    return {**archive, **result}


# one private launch request is sealed while both endpoint and controller custody agree
def prepare_launch(owner, archive, timeout):
    archive_sha = archive["archive_manifest_sha256"]
    base = owner.root / f"archived-replacement-preflight-{archive_sha}.json"
    preflight = read_pinned(base, archive["replacement_preflight_sha256"])
    request_path = owner.root / f"archived-replacement-launch-{archive_sha}.json"
    old = preflight["epoch"]["peer"]
    bundle = pinned_bundle(
        file_bytes(owner.args.lifecycle), preflight["epoch"]["installation_sha256"]
    )
    source = replacement_source(owner.config, require_admission=True)
    require(
        bundle_pins(bundle) == preflight["bundle"]
        and sha256(source) == preflight["provider_source_sha256"],
        "Fusion archived replacement deployment changed",
    )
    binding = {
        "version": 1,
        "scope": "owner_fusion_archived_replacement_launch",
        "archive_manifest_sha256": archive_sha,
        "recovery_basis_sha256": archive["recovery_basis_sha256"],
        "replacement_preflight_sha256": archive["replacement_preflight_sha256"],
        "commissioned_exit_sha256": preflight["commissioned_exit_sha256"],
        "commissioned_admission_sha256": preflight["epoch"]["admission_sha256"],
        "queue_job_id": timeout["queue_job_id"],
        "launch_challenge": preflight["launch_challenge"],
    }
    prior = optional_receipt(request_path)
    created = prior is None
    if created:
        require(
            not any(
                os.path.lexists(
                    owner.root / f"archived-replacement-{kind}-{archive_sha}.json"
                )
                for kind in ("peer", "startup")
            ),
            "Fusion archive retains effects with no launch request",
        )
        with owner_lock(owner.root / "host.lock"):
            require(
                identity(old["pid"]) is None, "prior Fusion process ID is still in use"
            )
            now = time.time()
            request = {
                **binding,
                "requested_at": now,
                "dispatch_before": now + owner.args.launch_seconds,
            }
            prior = encoded(request)
            write_new(request_path, prior)
    else:
        request = json.loads(prior)
        require(
            request
            == {
                **binding,
                "requested_at": request["requested_at"],
                "dispatch_before": request["dispatch_before"],
            }
            and 0 < request["dispatch_before"] - request["requested_at"] <= 300,
            "Fusion archive launch request belongs to another recovery",
        )
    return request_path, request, prior, preflight, bundle, source, created


# the provider observation and bootstrap are separate durable success conditions
def observe_launch(owner, snapshot, archive, prepared):
    request_path, request, request_raw, preflight, bundle, source, created = prepared
    archive_sha = archive["archive_manifest_sha256"]
    peer_path = owner.root / f"archived-replacement-peer-{archive_sha}.json"
    verify = partial(exact_archive, snapshot, archive, request_path, request_raw)
    if created:
        try:
            launched = launch_bundle(
                source,
                bundle,
                request["requested_at"],
                preflight["epoch"]["peer"],
                owner.args.launch_seconds,
                request_path,
                sha256(request_raw),
                dispatch_before=request["dispatch_before"],
                recovery_gate=partial(
                    launch_gate,
                    snapshot,
                    archive,
                    request_path,
                    request_raw,
                    preflight["epoch"]["peer"],
                ),
            )
        except MacLaunchError as error:
            return {
                "archive_replacement_status": "launch_unobserved",
                "archive_replacement_provider_exit": error.returncode,
            }
        except (OSError, subprocess.SubprocessError):
            return {"archive_replacement_status": "launch_unobserved"}
        with verify():
            write_new(
                peer_path,
                encoded(
                    {
                        "version": 1,
                        "scope": "fusion_archived_replacement_process",
                        "launch_request_sha256": sha256(request_raw),
                        "replacement_preflight_sha256": request[
                            "replacement_preflight_sha256"
                        ],
                        **launched,
                    }
                ),
            )
    if not os.path.lexists(peer_path):
        return {"archive_replacement_status": "launch_unobserved"}
    launch_raw, launched = read_peer_receipt(peer_path, request, request_raw, preflight)
    startup_path = owner.root / f"archived-replacement-startup-{archive_sha}.json"
    result = startup_proof(
        owner, preflight, bundle, launched, launch_raw, startup_path, verify=verify
    )
    if (
        owner.args.measure_archived_replacement
        and result["archive_replacement_status"] == "startup_verified_control_pending"
    ):
        from FusionArchiveControlOwner import observe_control

        result.update(
            observe_control(owner, archive, request, result, launched, verify)
        )
    return result
